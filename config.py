import os
from datetime import timedelta

class Config:
    # 🔐 Security Keys
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', '2748840e1d28efe969203cb021b5bf9a39673776085d5eee34e199d3a9359ede')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # 🗄️ Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///travel.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🤖 Gemini AI (FREE)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyBHJVwivPRPHy9I6_nW3VTRwaoH0K20KrI')
    
    # 🌦️ Weather API (OpenWeatherMap)
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', 'e89593b547a76b8ff6863fb7668f2aec')

    # 💳 Razorpay (TEST MODE)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_SahrPJ1gOYLNnz')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'gAGrWxHYWLACrBxqLHwSE6ah')

    # 📂 File Upload Settings
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # 📁 Allowed file types
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 🗺️ Leaflet/OSM (Free - no API key required)
    TILE_LAYER = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    
    # 🚀 Optional: Dark mode tile layer
    TILE_LAYER_DARK = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    
    # 📧 Email Configuration (Optional - for future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # 🔄 Pagination Settings
    ITEMS_PER_PAGE = 10
    
    # 🌐 CORS Settings (if needed)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')