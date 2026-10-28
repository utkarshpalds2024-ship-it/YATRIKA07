from extensions import db
from datetime import datetime
import json

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, default='')
    phone = db.Column(db.String(20), default='')
    avatar = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trips = db.relationship('Trip', backref='user', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    stories = db.relationship('TravelStory', backref='user', lazy=True, cascade='all, delete-orphan')
    wishlist = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', back_populates='user', lazy=True, cascade='all, delete-orphan')
    visa_applications = db.relationship('VisaApplication', backref='user', lazy=True, cascade='all, delete-orphan')
    places = db.relationship('Place', backref='user', lazy=True, cascade='all, delete-orphan')
    companion_profile = db.relationship('CompanionProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    sent_companion_requests = db.relationship('CompanionRequest', foreign_keys='CompanionRequest.sender_id', backref='sender', lazy=True, cascade='all, delete-orphan')
    received_companion_requests = db.relationship('CompanionRequest', foreign_keys='CompanionRequest.receiver_id', backref='receiver', lazy=True, cascade='all, delete-orphan')
    gamification_profile = db.relationship('GamificationProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    gamification_events = db.relationship('GamificationEvent', backref='user', lazy=True, cascade='all, delete-orphan')
    user_achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')
    user_missions = db.relationship('UserMission', backref='user', lazy=True, cascade='all, delete-orphan')
    redemptions = db.relationship('RewardRedemption', backref='user', lazy=True, cascade='all, delete-orphan')


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, default=0)
    itinerary = db.Column(db.Text, default='[]')  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    expenses = db.relationship('Expense', back_populates='trip', lazy=True, cascade='all, delete-orphan')


class Booking(db.Model):
    """Unified booking for flights, hotels, trains, buses"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Booking type: flight, hotel, train, bus
    booking_type = db.Column(db.String(20), nullable=False)  # flight, hotel, train, bus
    
    # Common fields
    provider = db.Column(db.String(100), nullable=False)  # e.g., "IndiGo", "Taj Hotel", "Indian Railways"
    from_location = db.Column(db.String(100))  # departure city (for flights, trains, buses)
    to_location = db.Column(db.String(100))    # arrival city (for flights, trains, buses)
    date = db.Column(db.Date, nullable=False)  # travel date or check-in date
    time = db.Column(db.String(20))            # departure time or check-in time
    price = db.Column(db.Float, nullable=False)
    travelers = db.Column(db.Integer, default=1)
    
    # Hotel-specific fields
    hotel_name = db.Column(db.String(200))
    room_type = db.Column(db.String(100))
    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)
    nights = db.Column(db.Integer)
    
    # Flight-specific fields
    flight_number = db.Column(db.String(20))
    airline = db.Column(db.String(100))
    duration = db.Column(db.String(50))
    
    # Train-specific fields
    train_number = db.Column(db.String(20))
    train_name = db.Column(db.String(100))
    coach = db.Column(db.String(20))
    seat_number = db.Column(db.String(20))
    
    # Bus-specific fields
    bus_number = db.Column(db.String(20))
    bus_operator = db.Column(db.String(100))
    seat_numbers = db.Column(db.String(100))
    
    # Payment and status
    payment_id = db.Column(db.String(100))
    order_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='confirmed')
    special_requests = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert booking to dictionary for JSON responses"""
        return {
            'id': self.id,
            'type': self.booking_type,
            'provider': self.provider,
            'from': self.from_location,
            'to': self.to_location,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time,
            'price': self.price,
            'travelers': self.travelers,
            'status': self.status,
            'hotel_name': self.hotel_name,
            'room_type': self.room_type,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'nights': self.nights,
            'flight_number': self.flight_number,
            'airline': self.airline,
            'duration': self.duration,
            'train_number': self.train_number,
            'train_name': self.train_name,
            'coach': self.coach,
            'seat_number': self.seat_number,
            'bus_number': self.bus_number,
            'bus_operator': self.bus_operator,
            'seat_numbers': self.seat_numbers,
            'special_requests': self.special_requests
        }


class Expense(db.Model):
    """Track expenses for trips"""
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # food, transport, accommodation, etc.
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - using back_populates to avoid conflicts
    user = db.relationship('User', back_populates='expenses')
    trip = db.relationship('Trip', back_populates='expenses')


class VisaApplication(db.Model):
    """Track visa applications"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Applied')  # Applied, In Review, Approved, Rejected
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Place(db.Model):
    """User-added places with smart tags"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    tags = db.Column(db.Text, default='')  # comma-separated tags: pet-friendly, senior-friendly, parking, medical
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TravelStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, default='')  # comma-separated paths
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    destination = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500))
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ========== COMPANION MODELS ==========

class CompanionProfile(db.Model):
    __tablename__ = 'companion_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # Personal Info
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    bio = db.Column(db.String(500))
    
    # Travel Details
    destination = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    interests = db.Column(db.String(500))
    looking_for = db.Column(db.String(200))
    
    # Location
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)


class CompanionRequest(db.Model):
    __tablename__ = 'companion_requests'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== GAMIFICATION MODELS ==========

class GamificationProfile(db.Model):
    __tablename__ = 'gamification_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    yc_balance = db.Column(db.Integer, default=0)
    yc_lifetime_earned = db.Column(db.Integer, default=0)
    yc_lifetime_spent = db.Column(db.Integer, default=0)
    xp_total = db.Column(db.Integer, default=0)
    current_level = db.Column(db.String(50), default='Explorer')
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_login_date = db.Column(db.Date)
    referral_code = db.Column(db.String(30), unique=True)
    referred_by = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GamificationEvent(db.Model):
    __tablename__ = 'gamification_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type = db.Column(db.String(80), nullable=False)
    event_ref = db.Column(db.String(120))
    coins_delta = db.Column(db.Integer, default=0)
    xp_delta = db.Column(db.Integer, default=0)
    meta_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_code = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(250), default='')
    icon = db.Column(db.String(50), default='fa-medal')
    progress = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, default=1)
    is_unlocked = db.Column(db.Boolean, default=False)
    unlocked_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserMission(db.Model):
    __tablename__ = 'user_missions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mission_key = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    mission_type = db.Column(db.String(20), nullable=False)  # daily, weekly
    event_type = db.Column(db.String(80), nullable=False)
    target_count = db.Column(db.Integer, default=1)
    current_count = db.Column(db.Integer, default=0)
    reward_coins = db.Column(db.Integer, default=0)
    reward_xp = db.Column(db.Integer, default=0)
    is_claimed = db.Column(db.Boolean, default=False)
    window_start = db.Column(db.Date, nullable=False)
    window_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RewardRedemption(db.Model):
    __tablename__ = 'reward_redemptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reward_key = db.Column(db.String(80), nullable=False)
    reward_title = db.Column(db.String(150), nullable=False)
    coins_spent = db.Column(db.Integer, nullable=False)
    voucher_code = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, used, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)