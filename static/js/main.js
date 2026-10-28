// ==================== Global Variables ====================
let socket = null;
let currentUser = null;

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initSocket();
    initEventListeners();
    initMobileMenu();
    initBackToTop();
});

// ==================== Authentication ====================
function initAuth() {
    // ✅ FIX: Get token from localStorage, NOT hardcoded
    const token = localStorage.getItem('access_token');
    const authLinks = document.getElementById('auth-links');
    const mobileAuthLinks = document.getElementById('mobile-auth-links');

    if (token && token !== "null" && token !== "undefined" && token.length > 10) {
        // Fetch user data with token
        fetch('/api/me', {
            method: 'GET',
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
        .then(res => {
            if (res.ok) return res.json();
            throw new Error('Token invalid');
        })
        .then(user => {
            currentUser = user;
            const userMenuHtml = `
                <div class="relative group">
                    <button class="flex items-center space-x-2 focus:outline-none">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                            ${user.username.charAt(0).toUpperCase()}
                        </div>
                        <span class="text-sm text-gray-700 hidden md:inline">${user.username}</span>
                        <i class="fas fa-chevron-down text-xs text-gray-500 hidden md:inline"></i>
                    </button>
                    <div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50">
                        <div class="py-2">
                            <a href="/profile" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                <i class="fas fa-user mr-2"></i>Profile
                            </a>
                            <a href="/dashboard" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                <i class="fas fa-chart-line mr-2"></i>Dashboard
                            </a>
                            <div class="border-t border-gray-200 my-1"></div>
                            <button onclick="logout()" class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
                                <i class="fas fa-sign-out-alt mr-2"></i>Logout
                            </button>
                        </div>
                    </div>
                </div>
            `;
            if (authLinks) authLinks.innerHTML = userMenuHtml;
            if (mobileAuthLinks) {
                mobileAuthLinks.innerHTML = `
                    <a href="/profile" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50">
                        <i class="fas fa-user mr-2"></i>Profile
                    </a>
                    <a href="/dashboard" class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50">
                        <i class="fas fa-chart-line mr-2"></i>Dashboard
                    </a>
                    <button onclick="logout()" class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-600 hover:bg-red-50">
                        <i class="fas fa-sign-out-alt mr-2"></i>Logout
                    </button>
                `;
            }
        })
        .catch((error) => {
            console.error('Auth error:', error);
            localStorage.removeItem('access_token');
            showUnauth(authLinks, mobileAuthLinks);
        });
    } else {
        showUnauth(authLinks, mobileAuthLinks);
    }
}

function showUnauth(authLinks, mobileAuthLinks) {
    const html = `
        <a href="/login" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-all duration-200">
            <i class="fas fa-sign-in-alt mr-2"></i>Login
        </a>
        <a href="/register" class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-all duration-200">
            <i class="fas fa-user-plus mr-2"></i>Register
        </a>
    `;
    if (authLinks) authLinks.innerHTML = html;
    if (mobileAuthLinks) mobileAuthLinks.innerHTML = html;
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('access_token');
        window.location.href = '/';
    }
}

// ==================== Socket.IO ====================
function initSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    socket.on('alert', (data) => {
        showToast(data, 'info');
    });
    
    socket.on('emergency_alert', (data) => {
        showToast('⚠️ Emergency alert nearby! Check map for details.', 'error');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });
}

// ==================== Toast Notifications ====================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type} fade-in-up`;
    toast.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== Loading States ====================
function showLoading(element) {
    if (!element) return;
    const loader = document.createElement('div');
    loader.className = 'spinner mx-auto my-4';
    element.innerHTML = '';
    element.appendChild(loader);
}

function hideLoading(element) {
    if (element) {
        element.innerHTML = '';
    }
}

// ==================== Form Validation ====================
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{10}$/;
    return re.test(phone);
}

function validatePassword(password) {
    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    const strength = Object.values(checks).filter(Boolean).length;
    return { strength, checks };
}

// ==================== Event Listeners ====================
function initEventListeners() {
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
        const mobileMenu = document.querySelector('.mobile-menu');
        const mobileButton = document.querySelector('.mobile-menu-button');
        if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
            if (!mobileMenu.contains(e.target) && !mobileButton?.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

function initMobileMenu() {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

function initBackToTop() {
    const backToTopBtn = document.getElementById('back-to-top');
    if (!backToTopBtn) return;
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.remove('hidden');
            backToTopBtn.classList.add('flex');
        } else {
            backToTopBtn.classList.add('hidden');
            backToTopBtn.classList.remove('flex');
        }
    });
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// ==================== Date Formatting ====================
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatDateTime(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)} days ago`;
    return formatDate(dateString);
}

// ==================== Currency Formatting ====================
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(amount);
}

// ==================== Local Storage Helpers ====================
function saveToLocalStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function getFromLocalStorage(key, defaultValue = null) {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : defaultValue;
}

function removeFromLocalStorage(key) {
    localStorage.removeItem(key);
}

// ==================== Export Functions ====================
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.validateEmail = validateEmail;
window.validatePhone = validatePhone;
window.validatePassword = validatePassword;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.formatRelativeTime = formatRelativeTime;
window.formatCurrency = formatCurrency;
window.saveToLocalStorage = saveToLocalStorage;
window.getFromLocalStorage = getFromLocalStorage;
window.removeFromLocalStorage = removeFromLocalStorage;
window.logout = logout;