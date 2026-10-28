import os
import json
import datetime
import requests
import random
import math
import uuid
from datetime import datetime, timedelta
from flask import Flask, make_response, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import func
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config import Config
from extensions import db, socketio, jwt
from models import (
    User, Trip, Booking, Review, TravelStory,
    Wishlist, Notification, Expense, VisaApplication, Place,
    CompanionProfile, CompanionRequest,
    GamificationProfile, GamificationEvent, UserAchievement,
    UserMission, RewardRedemption
)
from utils import (
    get_weather, get_crowd_density, geocode_osm, reverse_geocode_osm,
    search_nearby_osm, get_route_osm, create_razorpay_order,
    allowed_file, save_uploaded_file
)

# Try to import Razorpay
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
    print("✅ Razorpay package imported successfully")
except ImportError:
    RAZORPAY_AVAILABLE = False
    print("❌ Razorpay import failed. Run: pip install razorpay")

# Try to import Groq for AI features
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Groq not installed. Run: pip install groq")

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize extensions
db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")
jwt.init_app(app)

# API Configuration (from environment variables)
AVIATION_STACK_KEY = os.getenv('AVIATION_STACK_KEY', '')
IRCTC_RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
# The former Llama model IDs were retired by Groq.  This model supports
# Structured Outputs, which keeps the itinerary response predictable.
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

# Initialize Razorpay client
razorpay_client = None
if RAZORPAY_AVAILABLE and RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        print("✅ Razorpay client initialized successfully")
    except Exception as e:
        print(f"❌ Razorpay client error: {e}")

# Initialize Groq client
groq_client = None
if GROQ_AVAILABLE and GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI client initialized successfully")
    except Exception as e:
        print(f"⚠️ Groq initialization error: {e}")
else:
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY not found in environment variables")
    elif not GROQ_AVAILABLE:
        print("⚠️ Groq package not installed. Run: pip install groq")

# Print API key status for debugging
print(f"AviationStack Key configured: {'Yes' if AVIATION_STACK_KEY else 'No'}")
print(f"IRCTC API Key configured: {'Yes' if IRCTC_RAPIDAPI_KEY else 'No'}")
print(f"Groq AI configured: {'Yes' if groq_client else 'No'}")
print(f"Razorpay configured: {'Yes' if RAZORPAY_KEY_ID else 'No'}")

# Load City Database for Trip Planner
CITIES_DB = None
try:
    with open('data/cities.json', 'r', encoding='utf-8') as f:
        CITIES_DB = json.load(f)
    print(f"✅ Loaded {len(CITIES_DB.get('cities', []))} cities for trip planner")
except FileNotFoundError:
    print("❌ cities.json not found! Trip planner will use AI only.")
    CITIES_DB = {"cities": []}
except Exception as e:
    print(f"❌ Error loading cities.json: {e}")
    CITIES_DB = {"cities": []}

def get_city_by_name(city_name):
    """Search for city in database (case-insensitive)"""
    if not CITIES_DB or not CITIES_DB.get('cities'):
        return None
    city_name = city_name.lower().strip()
    for city in CITIES_DB['cities']:
        if city['name'].lower() == city_name:
            return city
    return None

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_best_time_to_visit(place_type):
    """Suggest best time to visit based on place type"""
    best_times = {
        'restaurant': '12:00 PM - 2:00 PM or 7:00 PM - 9:00 PM',
        'cafe': '9:00 AM - 11:00 AM or 4:00 PM - 6:00 PM',
        'attraction': 'Morning hours (9:00 AM - 11:00 AM)',
        'museum': 'Weekday mornings',
        'mall': 'Weekday afternoons (2:00 PM - 5:00 PM)',
        'station': 'Avoid peak hours (8-10 AM, 5-7 PM)'
    }
    for key, time in best_times.items():
        if key in place_type.lower():
            return time
    return 'Check local hours for best experience'


# ---------- Gamification Core ----------
LEVELS = [
    ('Explorer', 0, 500),
    ('Adventurer', 501, 1500),
    ('Globetrotter', 1501, 3000),
    ('Legend Traveler', 3001, 10**9)
]

EVENT_REWARDS = {
    'signup': {'coins': 100, 'xp': 120},
    'profile_completion': {'coins': 150, 'xp': 140},
    'booking_flight': {'coins': 200, 'xp': 180},
    'booking_hotel': {'coins': 180, 'xp': 160},
    'booking_train': {'coins': 120, 'xp': 120},
    'booking_cab': {'coins': 80, 'xp': 90},
    'booking_bus': {'coins': 90, 'xp': 100},
    'booking_cruise': {'coins': 260, 'xp': 220},
    'daily_login': {'coins': 10, 'xp': 20},
    'login_streak_7': {'coins': 100, 'xp': 130},
    'ai_itinerary': {'coins': 40, 'xp': 70},
    'review_posted': {'coins': 70, 'xp': 80},
    'trip_photo_upload': {'coins': 40, 'xp': 50},
    'referral_friend': {'coins': 300, 'xp': 220},
    'companion_finder_use': {'coins': 50, 'xp': 60},
    'smart_map_use': {'coins': 25, 'xp': 30},
    'mission_claim': {'coins': 0, 'xp': 0},
    'achievement_unlock': {'coins': 0, 'xp': 0}
}

BADGE_DEFS = [
    {'code': 'first_flight_booked', 'title': 'First Flight Booked', 'description': 'Complete your first flight booking', 'icon': 'fa-plane', 'target': 1, 'metric': 'flight_bookings', 'reward': {'coins': 120, 'xp': 120}},
    {'code': 'rail_explorer', 'title': 'Rail Explorer', 'description': 'Complete 3 train bookings', 'icon': 'fa-train', 'target': 3, 'metric': 'train_bookings', 'reward': {'coins': 160, 'xp': 140}},
    {'code': 'hotel_master', 'title': 'Hotel Master', 'description': 'Complete 5 hotel bookings', 'icon': 'fa-hotel', 'target': 5, 'metric': 'hotel_bookings', 'reward': {'coins': 220, 'xp': 180}},
    {'code': 'ai_planner_pro', 'title': 'AI Planner Pro', 'description': 'Generate 10 AI itineraries', 'icon': 'fa-robot', 'target': 10, 'metric': 'ai_itinerary_count', 'reward': {'coins': 180, 'xp': 160}},
    {'code': 'safety_hero', 'title': 'Safety Hero', 'description': 'Use companion finder 3 times', 'icon': 'fa-shield-alt', 'target': 3, 'metric': 'companion_uses', 'reward': {'coins': 130, 'xp': 120}},
    {'code': 'social_traveler', 'title': 'Social Traveler', 'description': 'Refer 1 friend', 'icon': 'fa-user-friends', 'target': 1, 'metric': 'referral_count', 'reward': {'coins': 250, 'xp': 200}},
    {'code': 'five_cities_visited', 'title': '5 Cities Visited', 'description': 'Complete bookings to 5 unique cities', 'icon': 'fa-city', 'target': 5, 'metric': 'cities_visited', 'reward': {'coins': 300, 'xp': 260}}
]

DAILY_MISSIONS = [
    {'key': 'daily_ai', 'title': 'Generate AI itinerary', 'event': 'ai_itinerary', 'target': 1, 'coins': 40, 'xp': 35},
    {'key': 'daily_booking', 'title': 'Book one trip', 'event': 'booking_any', 'target': 1, 'coins': 100, 'xp': 80},
    {'key': 'daily_review', 'title': 'Add review', 'event': 'review_posted', 'target': 1, 'coins': 50, 'xp': 40}
]

WEEKLY_MISSIONS = [
    {'key': 'weekly_referral', 'title': 'Invite a friend', 'event': 'referral_friend', 'target': 1, 'coins': 200, 'xp': 130},
    {'key': 'weekly_explore', 'title': 'Explore 3 attractions', 'event': 'smart_map_use', 'target': 3, 'coins': 120, 'xp': 90},
    {'key': 'weekly_story', 'title': 'Upload trip photos', 'event': 'trip_photo_upload', 'target': 5, 'coins': 110, 'xp': 85}
]

STORE_REWARDS = [
    {'key': 'hotel_discount', 'title': 'Hotel Discount Voucher', 'cost': 1500, 'value': 'Rs 200 OFF', 'type': 'hotel'},
    {'key': 'cab_discount', 'title': 'Cab Discount Voucher', 'cost': 800, 'value': 'Rs 100 OFF', 'type': 'cab'},
    {'key': 'premium_itinerary', 'title': 'Premium Itinerary Unlock', 'cost': 2000, 'value': 'AI Premium Pack', 'type': 'premium'},
    {'key': 'cashback_voucher', 'title': 'Cashback Voucher', 'cost': 2500, 'value': 'Rs 300 Cashback', 'type': 'cashback'}
]

SPIN_REWARDS = [
    {'key': 'spin_small_yc', 'label': '+30 YC', 'coins': 30, 'xp': 20, 'weight': 28, 'kind': 'yc'},
    {'key': 'spin_medium_yc', 'label': '+60 YC', 'coins': 60, 'xp': 35, 'weight': 22, 'kind': 'yc'},
    {'key': 'spin_big_yc', 'label': '+120 YC', 'coins': 120, 'xp': 70, 'weight': 12, 'kind': 'yc'},
    {'key': 'spin_xp_boost', 'label': 'Mystery XP Boost', 'coins': 20, 'xp': 180, 'weight': 16, 'kind': 'xp'},
    {'key': 'spin_cashback', 'label': 'Cashback Coupon', 'coins': 40, 'xp': 40, 'weight': 14, 'kind': 'coupon'},
    {'key': 'spin_bonus_badge', 'label': 'Bonus Badge', 'coins': 80, 'xp': 90, 'weight': 8, 'kind': 'badge'}
]


def _to_int_user_id(user_id):
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return user_id


def level_from_xp(xp_total):
    xp_total = int(xp_total or 0)
    for name, low, high in LEVELS:
        if low <= xp_total <= high:
            return name, low, high
    return LEVELS[-1][0], LEVELS[-1][1], LEVELS[-1][2]


def get_or_create_gamification_profile(user_id):
    user_id = _to_int_user_id(user_id)
    profile = GamificationProfile.query.filter_by(user_id=user_id).first()
    if profile:
        return profile
    referral_code = f"YAT{user_id}{random.randint(100, 999)}"
    profile = GamificationProfile(user_id=user_id, referral_code=referral_code)
    db.session.add(profile)
    db.session.flush()
    return profile


def _profile_is_complete(user):
    if not user:
        return False
    checks = [bool(user.bio and user.bio.strip()), bool(user.phone and user.phone.strip()), bool(user.avatar and user.avatar.strip())]
    return sum(checks) >= 2


def ensure_user_missions(user_id):
    user_id = _to_int_user_id(user_id)
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    for m in DAILY_MISSIONS:
        exists = UserMission.query.filter_by(user_id=user_id, mission_key=m['key'], window_start=today, mission_type='daily').first()
        if not exists:
            db.session.add(UserMission(
                user_id=user_id,
                mission_key=m['key'],
                title=m['title'],
                mission_type='daily',
                event_type=m['event'],
                target_count=m['target'],
                reward_coins=m['coins'],
                reward_xp=m['xp'],
                window_start=today,
                window_end=today
            ))

    for m in WEEKLY_MISSIONS:
        exists = UserMission.query.filter_by(user_id=user_id, mission_key=m['key'], window_start=week_start, mission_type='weekly').first()
        if not exists:
            db.session.add(UserMission(
                user_id=user_id,
                mission_key=m['key'],
                title=m['title'],
                mission_type='weekly',
                event_type=m['event'],
                target_count=m['target'],
                reward_coins=m['coins'],
                reward_xp=m['xp'],
                window_start=week_start,
                window_end=week_end
            ))


def _increment_missions(user_id, event_type):
    user_id = _to_int_user_id(user_id)
    today = datetime.utcnow().date()
    active = UserMission.query.filter(
        UserMission.user_id == user_id,
        UserMission.window_start <= today,
        UserMission.window_end >= today,
        UserMission.is_claimed == False
    ).all()

    mapped_events = {event_type}
    if str(event_type).startswith('booking_'):
        mapped_events.add('booking_any')

    for m in active:
        if m.event_type in mapped_events and m.current_count < m.target_count:
            m.current_count += 1


def ensure_badges(user_id):
    user_id = _to_int_user_id(user_id)
    for b in BADGE_DEFS:
        found = UserAchievement.query.filter_by(user_id=user_id, badge_code=b['code']).first()
        if not found:
            db.session.add(UserAchievement(
                user_id=user_id,
                badge_code=b['code'],
                title=b['title'],
                description=b['description'],
                icon=b['icon'],
                target=b['target']
            ))


def _achievement_metrics(user_id):
    user_id = _to_int_user_id(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).all()
    metrics = {
        'flight_bookings': sum(1 for b in bookings if b.booking_type == 'flight'),
        'train_bookings': sum(1 for b in bookings if b.booking_type == 'train'),
        'hotel_bookings': sum(1 for b in bookings if b.booking_type == 'hotel'),
        'ai_itinerary_count': GamificationEvent.query.filter_by(user_id=user_id, event_type='ai_itinerary').count(),
        'companion_uses': GamificationEvent.query.filter_by(user_id=user_id, event_type='companion_finder_use').count(),
        'referral_count': GamificationEvent.query.filter_by(user_id=user_id, event_type='referral_friend').count(),
        'cities_visited': len({(b.to_location or b.from_location or '').strip().lower() for b in bookings if (b.to_location or b.from_location)})
    }
    return metrics


def refresh_achievements(user_id):
    user_id = _to_int_user_id(user_id)
    ensure_badges(user_id)
    profile = get_or_create_gamification_profile(user_id)
    metrics = _achievement_metrics(user_id)

    achs = UserAchievement.query.filter_by(user_id=user_id).all()
    def_map = {b['code']: b for b in BADGE_DEFS}
    for ach in achs:
        d = def_map.get(ach.badge_code)
        if not d:
            continue
        ach.progress = int(metrics.get(d['metric'], 0))
        if (not ach.is_unlocked) and ach.progress >= ach.target:
            ach.is_unlocked = True
            ach.unlocked_at = datetime.utcnow()
            reward = d.get('reward', {'coins': 0, 'xp': 0})
            profile.yc_balance += reward.get('coins', 0)
            profile.yc_lifetime_earned += reward.get('coins', 0)
            profile.xp_total += reward.get('xp', 0)
            db.session.add(GamificationEvent(
                user_id=user_id,
                event_type='achievement_unlock',
                event_ref=ach.badge_code,
                coins_delta=reward.get('coins', 0),
                xp_delta=reward.get('xp', 0),
                meta_json=json.dumps({'badge': ach.title})
            ))

    level_name, _, _ = level_from_xp(profile.xp_total)
    profile.current_level = level_name


def award_event(user_id, event_type, event_ref=None, meta=None, force=False):
    user_id = _to_int_user_id(user_id)
    reward = EVENT_REWARDS.get(event_type)
    if not reward:
        return {'ok': False, 'msg': 'Unknown event type'}

    one_time_events = {'signup', 'profile_completion'}
    if event_type in one_time_events and not force:
        exists = GamificationEvent.query.filter_by(user_id=user_id, event_type=event_type).first()
        if exists:
            return {'ok': True, 'msg': 'Event already awarded'}

    once_per_day_events = {'smart_map_use'}
    if event_type in once_per_day_events and not force:
        today = datetime.utcnow().date()
        exists_today = GamificationEvent.query.filter(
            GamificationEvent.user_id == user_id,
            GamificationEvent.event_type == event_type,
            func.date(GamificationEvent.created_at) == today
        ).first()
        if exists_today:
            return {'ok': True, 'msg': 'Event already awarded today'}

    profile = get_or_create_gamification_profile(user_id)
    coins = int(reward.get('coins', 0))
    xp = int(reward.get('xp', 0))

    profile.yc_balance += coins
    profile.yc_lifetime_earned += max(0, coins)
    profile.xp_total += xp
    level_name, _, _ = level_from_xp(profile.xp_total)
    profile.current_level = level_name

    ev = GamificationEvent(
        user_id=user_id,
        event_type=event_type,
        event_ref=str(event_ref) if event_ref is not None else None,
        coins_delta=coins,
        xp_delta=xp,
        meta_json=json.dumps(meta or {})
    )
    db.session.add(ev)

    _increment_missions(user_id, event_type)
    refresh_achievements(user_id)
    return {'ok': True, 'coins': coins, 'xp': xp, 'level': profile.current_level}


def process_daily_login(user_id):
    user_id = _to_int_user_id(user_id)
    profile = get_or_create_gamification_profile(user_id)
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    if profile.last_login_date == today:
        return {'streak': profile.current_streak, 'awarded': False}

    if profile.last_login_date == yesterday:
        profile.current_streak += 1
    else:
        profile.current_streak = 1

    profile.longest_streak = max(profile.longest_streak or 0, profile.current_streak)
    profile.last_login_date = today

    award_event(user_id, 'daily_login', meta={'streak': profile.current_streak}, force=True)

    # Day-wise streak top-up rewards: day1 +10 ... day7 +100 bonus.
    streak_day = profile.current_streak % 7 or 7
    day_rewards = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30, 6: 40, 7: 100}
    extra_coins = day_rewards.get(streak_day, 10)
    if extra_coins > 0:
        p = get_or_create_gamification_profile(user_id)
        p.yc_balance += extra_coins
        p.yc_lifetime_earned += extra_coins
        db.session.add(GamificationEvent(
            user_id=user_id,
            event_type='streak_day_bonus',
            event_ref=str(streak_day),
            coins_delta=extra_coins,
            xp_delta=0,
            meta_json=json.dumps({'streak_day': streak_day})
        ))

    if streak_day == 7:
        award_event(user_id, 'login_streak_7', meta={'streak': profile.current_streak}, force=True)

    return {'streak': profile.current_streak, 'awarded': True}


def wallet_inr_value(coins):
    coins = int(coins or 0)
    return round((coins / 100.0) * 10.0, 2)


def build_leaderboard_for_scope(user_id, scope='weekly', limit=10):
    user_id = _to_int_user_id(user_id)
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())

    base_rows = db.session.query(
        GamificationEvent.user_id,
        func.coalesce(func.sum(GamificationEvent.coins_delta), 0).label('coins_score'),
        func.coalesce(func.sum(GamificationEvent.xp_delta), 0).label('xp_score')
    ).filter(
        func.date(GamificationEvent.created_at) >= week_start
    ).group_by(GamificationEvent.user_id).all()

    # Resolve user pool by scope.
    if scope == 'friends':
        friend_ids = {user_id}
        links = CompanionRequest.query.filter(
            (CompanionRequest.sender_id == user_id) | (CompanionRequest.receiver_id == user_id)
        ).all()
        for l in links:
            friend_ids.add(l.sender_id)
            friend_ids.add(l.receiver_id)
    else:
        friend_ids = None

    me = User.query.get(user_id)
    my_city = (me.bio.split(',')[0].strip().lower() if (me and me.bio) else '')
    my_college = (me.email.split('@')[1].split('.')[0].strip().lower() if (me and me.email and '@' in me.email) else '')

    resolved = []
    for row in base_rows:
        uid = int(row.user_id)
        u = User.query.get(uid)
        if not u:
            continue
        city = (u.bio.split(',')[0].strip() if u.bio else 'Traveler City')
        college = (u.email.split('@')[1].split('.')[0].title() if (u.email and '@' in u.email) else 'Campus')
        if scope == 'city' and my_city and city.lower() != my_city:
            continue
        if scope == 'college' and my_college and college.lower() != my_college:
            continue
        if scope == 'friends' and friend_ids is not None and uid not in friend_ids:
            continue
        score = int(row.coins_score or 0)
        resolved.append({'user_id': uid, 'username': u.username, 'score': score, 'city': city, 'college': college})

    resolved.sort(key=lambda x: x['score'], reverse=True)
    for idx, item in enumerate(resolved, start=1):
        item['rank'] = idx

    my_rank = next((r['rank'] for r in resolved if r['user_id'] == user_id), None)
    my_score = next((r['score'] for r in resolved if r['user_id'] == user_id), 0)
    need_next = 0
    if my_rank and my_rank > 1:
        prev = resolved[my_rank - 2]
        need_next = max(0, prev['score'] - my_score + 1)

    return {
        'items': resolved[:limit],
        'meta': {
            'your_rank': my_rank,
            'your_score': my_score,
            'need_points_to_next_rank': need_next
        }
    }

# Create tables and upload folder
with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------- Page Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/profile')
def profile_page():
    return render_template('profile.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/planner')
def planner_page():
    return render_template('trip_planner.html')

@app.route('/stories')
def stories_page():
    return render_template('stories.html')

@app.route('/smart-map')
def smart_map_page():
    response = make_response(render_template('Smart_map.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/booking')
def booking_page():
    return render_template('booking.html', 
                          razorpay_key_id=app.config.get('RAZORPAY_KEY_ID', ''))

@app.route('/route-planner')
def route_planner_page():
    return render_template('route_planner.html')

@app.route('/visa')
def visa_page():
    return render_template('visa.html')

@app.route('/hotels')
def hotels_page():
    return render_template('hotels.html')

@app.route('/live-flights')
def live_flights_page():
    return render_template('live_flights.html')

# ---------- OpenSky Network API (Live Flights) ----------
@app.route('/api/live-flights', methods=['GET'])
def get_live_flights():
    """Fetch real-time flight data from OpenSky Network API"""
    try:
        url = "https://opensky-network.org/api/states/all"
        response = requests.get(url, headers={'User-Agent': 'YATRIKA-TravelApp/1.0'}, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        flights = []
        for state in data.get('states', []):
            flight = {
                'icao24': state[0],
                'callsign': state[1].strip() if state[1] else 'N/A',
                'origin_country': state[2],
                'longitude': state[5],
                'latitude': state[6],
                'altitude': state[7],
                'velocity': state[9],
                'true_track': state[10],
                'on_ground': state[8],
                'geo_altitude': state[13]
            }
            if flight['longitude'] is not None and flight['latitude'] is not None and not flight['on_ground']:
                flights.append(flight)
        
        return jsonify({
            'success': True,
            'count': len(flights),
            'flights': flights[:100]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'flights': []}), 200

# ---------- Crowd Density with Waiting Time ----------
@app.route('/api/crowd/density', methods=['GET'])
def crowd_density_with_waiting():
    """Get crowd density and estimated waiting time for locations"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 3000, type=int)
    place_type = request.args.get('type', 'all')
    
    if not lat or not lng:
        return jsonify({'error': 'Coordinates required'}), 400
    
    current_hour = datetime.now().hour
    
    if 9 <= current_hour <= 11:
        crowd_factor = 0.7
        waiting_factor = 0.6
    elif 12 <= current_hour <= 14:
        crowd_factor = 0.8
        waiting_factor = 0.8
    elif 17 <= current_hour <= 20:
        crowd_factor = 0.9
        waiting_factor = 0.9
    else:
        crowd_factor = 0.3
        waiting_factor = 0.2
    
    place_types = {
        'restaurant': ['amenity=restaurant', 'amenity=cafe', 'amenity=fast_food'],
        'attraction': ['tourism=attraction', 'tourism=museum', 'historic=monument'],
        'mall': ['shop=mall', 'shop=supermarket'],
        'station': ['railway=station', 'public_transport=station'],
        'all': ['amenity=restaurant', 'tourism=attraction', 'shop=mall', 'railway=station']
    }
    
    search_terms = place_types.get(place_type, place_types['all'])
    places = search_nearby_osm(lat, lng, radius, ','.join(search_terms))
    
    results = []
    for place in places[:30]:
        crowd_level = min(100, int((random.random() * 0.5 + crowd_factor) * 100))
        
        place_name = str(place.get('type', '')).lower()
        if 'restaurant' in place_name or 'cafe' in place_name:
            base_wait = random.randint(5, 30) if crowd_level > 60 else random.randint(0, 10)
        elif 'attraction' in place_name or 'museum' in place_name:
            base_wait = random.randint(10, 45) if crowd_level > 70 else random.randint(0, 15)
        else:
            base_wait = random.randint(0, 15)
        
        waiting_time = int(base_wait * waiting_factor)
        
        if crowd_level >= 70:
            crowd_status = "Very Busy"
            crowd_color = "#ef4444"
        elif crowd_level >= 40:
            crowd_status = "Moderate"
            crowd_color = "#f59e0b"
        else:
            crowd_status = "Quiet"
            crowd_color = "#10b981"
        
        results.append({
            'id': place.get('id'),
            'name': place.get('name', 'Unknown Place'),
            'type': place.get('type', 'place'),
            'lat': place.get('lat'),
            'lng': place.get('lon'),
            'crowd_level': crowd_level,
            'crowd_status': crowd_status,
            'crowd_color': crowd_color,
            'waiting_time': waiting_time,
            'waiting_text': f"{waiting_time} min" if waiting_time > 0 else "No wait",
            'best_time': get_best_time_to_visit(place.get('type', ''))
        })
    
    return jsonify({'success': True, 'places': results, 'count': len(results)})

# ---------- Companion Profile Endpoints ----------
@app.route('/api/companion/profile', methods=['GET', 'POST'])
@jwt_required()
def companion_profile_enhanced():
    user_id = get_jwt_identity()
    profile = CompanionProfile.query.filter_by(user_id=user_id).first()
    
    if request.method == 'GET':
        if not profile:
            return jsonify({'exists': False})
        return jsonify({
            'exists': True,
            'name': profile.name,
            'age': profile.age,
            'gender': profile.gender,
            'bio': profile.bio,
            'destination': profile.destination,
            'start_date': profile.start_date.isoformat() if profile.start_date else None,
            'end_date': profile.end_date.isoformat() if profile.end_date else None,
            'interests': profile.interests,
            'looking_for': profile.looking_for,
            'latitude': profile.latitude,
            'longitude': profile.longitude,
            'is_active': profile.is_active
        })
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if not profile:
        profile = CompanionProfile(user_id=user_id)
        db.session.add(profile)
    
    profile.name = data.get('name', profile.name)
    if data.get('age'):
        try:
            profile.age = int(data['age'])
        except:
            pass
    profile.gender = data.get('gender', profile.gender)
    profile.bio = data.get('bio', profile.bio)
    profile.destination = data.get('destination', profile.destination)
    
    if data.get('start_date'):
        try:
            profile.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except:
            pass
    if data.get('end_date'):
        try:
            profile.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except:
            pass

    if data.get('latitude') is not None:
        try:
            profile.latitude = float(data.get('latitude'))
        except (TypeError, ValueError):
            pass

    if data.get('longitude') is not None:
        try:
            profile.longitude = float(data.get('longitude'))
        except (TypeError, ValueError):
            pass
    
    profile.interests = data.get('interests', profile.interests)
    profile.looking_for = data.get('looking_for', profile.looking_for)
    profile.is_active = data.get('is_active', True)
    
    db.session.commit()
    return jsonify({'message': 'Profile saved successfully'})


@app.route('/api/companion/nearby-enhanced', methods=['GET'])
@jwt_required()
def get_nearby_companions_enhanced():
    user_id = get_jwt_identity()
    current_user = CompanionProfile.query.filter_by(user_id=user_id).first()

    def build_mock_companions(base_lat, base_lng, radius_km=10.0):
        radius_deg = max(0.005, min(radius_km / 111.0, 0.08))
        templates = [
            {'name': 'Aarav', 'destination': 'Goa', 'looking_for': 'Beach and cafe hopping', 'interests': 'food,photography,beaches'},
            {'name': 'Mira', 'destination': 'Jaipur', 'looking_for': 'Culture and heritage walks', 'interests': 'history,markets,local food'},
            {'name': 'Kabir', 'destination': 'Mumbai', 'looking_for': 'City exploration', 'interests': 'nightlife,street food,music'},
            {'name': 'Anaya', 'destination': 'Bangalore', 'looking_for': 'Weekend trip buddy', 'interests': 'nature,coffee,trekking'}
        ]
        mocks = []
        for idx, t in enumerate(templates, start=1):
            offset_lat = (random.random() - 0.5) * radius_deg
            offset_lng = (random.random() - 0.5) * radius_deg
            mocks.append({
                'user_id': f'mock_{idx}',
                'username': f"{t['name'].lower()}_demo",
                'name': t['name'],
                'age': random.randint(22, 36),
                'gender': random.choice(['Male', 'Female']),
                'bio': f"Demo companion nearby for {t['destination']}.",
                'destination': t['destination'],
                'interests': t['interests'],
                'looking_for': t['looking_for'],
                'latitude': base_lat + offset_lat,
                'longitude': base_lng + offset_lng,
                'distance_km': round(haversine(base_lat, base_lng, base_lat + offset_lat, base_lng + offset_lng), 2),
                'compatibility': random.randint(62, 91),
                'connection_status': 'none',
                'is_mock': True,
                'contact': f"{t['name'].lower()}@demo.yatrika"
            })
        return mocks

    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius_km = request.args.get('radius', 10, type=float)

    if lat is None and current_user and current_user.latitude is not None:
        lat = current_user.latitude
    if lng is None and current_user and current_user.longitude is not None:
        lng = current_user.longitude

    if lat is None or lng is None:
        return jsonify(build_mock_companions(20.5937, 78.9629, radius_km))
    
    companions = CompanionProfile.query.filter(
        CompanionProfile.user_id != user_id,
        CompanionProfile.is_active == True,
        CompanionProfile.latitude.isnot(None),
        CompanionProfile.longitude.isnot(None)
    ).all()
    
    result = []
    for cp in companions:
        dist = haversine(lat, lng, cp.latitude, cp.longitude)
        if dist <= radius_km:
            compatibility = 50
            if current_user and current_user.destination and cp.destination:
                if current_user.destination.lower() == cp.destination.lower():
                    compatibility = 80
            elif current_user and current_user.interests and cp.interests:
                common = len(set(current_user.interests.split(',')) & set(cp.interests.split(',')))
                compatibility = min(100, 50 + common * 10)
            
            existing = CompanionRequest.query.filter(
                ((CompanionRequest.sender_id == user_id) & (CompanionRequest.receiver_id == cp.user_id)) |
                ((CompanionRequest.sender_id == cp.user_id) & (CompanionRequest.receiver_id == user_id))
            ).first()
            
            result.append({
                'user_id': cp.user_id,
                'username': cp.user.username,
                'name': cp.name or cp.user.username,
                'age': cp.age,
                'gender': cp.gender,
                'bio': cp.bio,
                'destination': cp.destination,
                'interests': cp.interests,
                'looking_for': cp.looking_for,
                'latitude': cp.latitude,
                'longitude': cp.longitude,
                'distance_km': round(dist, 2),
                'compatibility': compatibility,
                'connection_status': existing.status if existing else 'none',
                'is_mock': False,
                'contact': cp.user.username
            })

    result.sort(key=lambda x: x['distance_km'])
    if not result:
        return jsonify(build_mock_companions(lat, lng, radius_km))
    return jsonify(result)


@app.route('/api/companion/request', methods=['POST'])
@jwt_required()
def send_companion_request():
    user_id = get_jwt_identity()
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    message = data.get('message', '')
    
    if not receiver_id:
        return jsonify({'error': 'Receiver ID required'}), 400

    if isinstance(receiver_id, str) and receiver_id.startswith('mock_'):
        return jsonify({'error': 'Demo companion cannot receive real requests'}), 400

    try:
        receiver_id = int(receiver_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid receiver ID'}), 400
    
    existing = CompanionRequest.query.filter(
        ((CompanionRequest.sender_id == user_id) & (CompanionRequest.receiver_id == receiver_id)) |
        ((CompanionRequest.sender_id == receiver_id) & (CompanionRequest.receiver_id == user_id))
    ).first()
    
    if existing:
        return jsonify({'error': 'Request already exists'}), 400
    
    request_obj = CompanionRequest(
        sender_id=user_id,
        receiver_id=receiver_id,
        message=message
    )
    db.session.add(request_obj)
    try:
        award_event(user_id, 'companion_finder_use', event_ref=receiver_id, meta={'message': message[:50]})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gamification companion event failed: {e}")
        db.session.add(request_obj)
        db.session.commit()
    
    sender = User.query.get(user_id)
    sender_profile = CompanionProfile.query.filter_by(user_id=user_id).first()
    socketio.emit('companion_request', {
        'request_id': request_obj.id,
        'sender_id': user_id,
        'receiver_id': receiver_id,
        'from_name': (sender_profile.name if sender_profile and sender_profile.name else sender.username if sender else 'A traveler'),
        'message': message
    }, room=str(receiver_id))
    
    return jsonify({'message': 'Connection request sent'})


@app.route('/api/companion/requests', methods=['GET'])
@jwt_required()
def get_companion_requests():
    user_id = get_jwt_identity()
    requests_received = CompanionRequest.query.filter_by(
        receiver_id=user_id,
        status='pending'
    ).order_by(CompanionRequest.created_at.desc()).all()
    result = []
    for companion_request in requests_received:
        sender = companion_request.sender
        profile = CompanionProfile.query.filter_by(user_id=companion_request.sender_id).first()
        result.append({
            'id': companion_request.id,
            'sender_name': profile.name if profile and profile.name else sender.username if sender else 'Traveler',
            'destination': profile.destination if profile else '',
            'message': companion_request.message or '',
            'created_at': companion_request.created_at.isoformat() if companion_request.created_at else None
        })
    return jsonify({'requests': result, 'count': len(result)})


@app.route('/api/companion/request/<int:request_id>/<action>', methods=['POST'])
@jwt_required()
def handle_companion_request(request_id, action):
    user_id = get_jwt_identity()
    request_obj = CompanionRequest.query.get(request_id)
    
    if not request_obj or request_obj.receiver_id != user_id:
        return jsonify({'error': 'Request not found'}), 404
    
    if action not in ['accept', 'decline']:
        return jsonify({'error': 'Invalid action'}), 400
    
    request_obj.status = 'accepted' if action == 'accept' else 'declined'
    request_obj.updated_at = datetime.utcnow()
    db.session.commit()
    
    socketio.emit('companion_request_response', {
        'request_id': request_id,
        'status': request_obj.status,
        'receiver_id': user_id
    }, room=str(request_obj.sender_id))
    
    return jsonify({'message': f'Request {action}ed'})

# ---------- Smart Map API Endpoints ----------
@app.route('/api/nearby/search', methods=['GET'])
def nearby_search():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 2000, type=int)
    category = request.args.get('category', 'all')
    
    if lat is None or lng is None:
        return jsonify({'error': 'Coordinates required'}), 400
    
    # Try with timeout
    try:
        places = search_nearby_osm(lat, lng, radius, category)
    except Exception as e:
        print(f"OSM search timeout/error: {e}")
        places = []
    
    for place in places:
        place_type = str(place.get('type', '')).lower()
        if 'hospital' in place_type or 'clinic' in place_type:
            place['emergency_phone'] = '108'
        elif 'police' in place_type:
            place['emergency_phone'] = '100'
        elif 'fire' in place_type:
            place['emergency_phone'] = '101'
    
    return jsonify({'success': True, 'places': places, 'count': len(places)})

@app.route('/api/crowd/heatmap', methods=['GET'])
def crowd_heatmap():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 5000, type=int)
    
    if lat is None or lng is None:
        return jsonify({'error': 'Coordinates required'}), 400
    
    popular_places = search_nearby_osm(lat, lng, radius, 'tourism=attraction,amenity=restaurant,shop=mall,railway=station')
    points = []
    
    for place in popular_places[:30]:
        intensity = 0.5
        place_type = str(place.get('type', '')).lower()
        if 'attraction' in place_type:
            intensity = 0.8
        elif 'restaurant' in place_type:
            intensity = 0.6
        elif 'mall' in place_type:
            intensity = 0.7
        points.append([place['lat'], place['lon'], intensity])
    
    return jsonify({'success': True, 'points': points, 'count': len(points), 'live': False})

@app.route('/api/parking/nearby', methods=['GET'])
def nearby_parking():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 1000, type=int)
    
    if lat is None or lng is None:
        return jsonify({'error': 'Coordinates required'}), 400
    
    try:
        parking_spots = search_nearby_osm(lat, lng, radius, 'parking')
    except Exception as e:
        print(f"Parking search timeout: {e}")
        parking_spots = []
    
    # OSM does not provide live occupancy or pricing; keep those values unknown.
    for spot in parking_spots:
        tags = spot.get('tags', {})
        spot['available_spots'] = None
        spot['total_spots'] = None
        spot['price_per_hour'] = None
        spot['is_free'] = None
        has_ev_charging = any(key.startswith('socket:') for key in tags) or tags.get('capacity:charging') is not None
        spot['has_ev_charging'] = True if has_ev_charging else None
        spot['parking_type'] = tags.get('parking', '')
        spot['availability_known'] = False
        spot.setdefault('is_mock', False)
        spot['address'] = tags.get('addr:street') or spot.get('name', 'Parking location')
        spot['description'] = 'Demo location' if spot['is_mock'] else 'Live availability and pricing are not provided.'

    return jsonify({'success': True, 'parking_spots': parking_spots, 'count': len(parking_spots)})

@app.route('/api/local-experiences', methods=['GET'])
def local_experiences():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 2000, type=int)
    
    if lat is None or lng is None:
        return jsonify({'error': 'Coordinates required'}), 400
    
    # Fast-fail approach: single OSM lookup; fallback to mock immediately on failure.
    real_places = []
    try:
        print(f"🔍 Attempting OSM local experience search at {lat},{lng}")
        real_places = search_nearby_osm(lat, lng, radius, 'all')
    except Exception as e:
        print(f"⏱️ Local experience OSM lookup timed out/failed at ({lat},{lng}): {e}")
        real_places = []
    
    experiences = []
    
    # If no real data, generate mock places around the location
    if not real_places:
        import random
        mock_templates = [
            {'name': 'Local Street Food Corner', 'category': 'street_food', 'icon': 'fa-utensils', 'color': '#f59e0b', 'description': 'Authentic local street food'},
            {'name': 'City Museum', 'category': 'cultural', 'icon': 'fa-landmark', 'color': '#8b5cf6', 'description': 'History and art exhibits'},
            {'name': 'Central Market', 'category': 'market', 'icon': 'fa-store', 'color': '#10b981', 'description': 'Traditional marketplace'},
            {'name': 'Art Gallery & Café', 'category': 'cultural', 'icon': 'fa-palette', 'color': '#8b5cf6', 'description': 'Contemporary art space'},
            {'name': 'Food Truck Park', 'category': 'street_food', 'icon': 'fa-utensils', 'color': '#f59e0b', 'description': 'Gourmet food trucks'},
            {'name': 'Historic Temple', 'category': 'cultural', 'icon': 'fa-church', 'color': '#8b5cf6', 'description': 'Ancient spiritual site'},
            {'name': 'Night Market & Bazaar', 'category': 'market', 'icon': 'fa-store', 'color': '#10b981', 'description': 'Evening shopping hub'},
            {'name': 'Café & Dessert Corner', 'category': 'street_food', 'icon': 'fa-mug-hot', 'color': '#f59e0b', 'description': 'Coffee and pastries'}
        ]
        for i, t in enumerate(mock_templates[:8]):
            # Spread mock points around the given coordinates
            offset_lat = (random.random() - 0.5) * 0.02
            offset_lng = (random.random() - 0.5) * 0.02
            experiences.append({
                'name': t['name'],
                'type': t['category'],
                'lat': lat + offset_lat,
                'lon': lng + offset_lng,
                'distance': round(random.uniform(0.2, 2.0), 1),
                'category': t['category'],
                'icon': t['icon'],
                'color': t['color'],
                'is_mock': True,
                'description': t['description']
            })
        print(f"📍 Using MOCK local experiences for {lat},{lng} (OSM lookup failed or no real places found)")
    else:
        for spot in real_places[:12]:
            spot_type = str(spot.get('type', '')).lower()
            if any(word in spot_type for word in ['restaurant', 'cafe', 'fast_food', 'bar', 'pub']):
                spot['category'] = 'street_food'
                spot['icon'] = 'fa-utensils'
                spot['color'] = '#f59e0b'
                spot['description'] = 'Local food and cafe spot'
            elif any(word in spot_type for word in ['shop', 'mall', 'market', 'supermarket']):
                spot['category'] = 'market'
                spot['icon'] = 'fa-store'
                spot['color'] = '#10b981'
                spot['description'] = 'Shopping and market area'
            else:
                spot['category'] = 'cultural'
                spot['icon'] = 'fa-landmark'
                spot['color'] = '#8b5cf6'
                spot['description'] = 'Attraction and cultural place'
            spot['is_mock'] = False
            experiences.append(spot)
    
    return jsonify({'success': True, 'experiences': experiences, 'count': len(experiences)})
@app.route('/api/weather/map', methods=['GET'])
def weather_api():
    """Fetch weather data by coordinates"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if lat is None or lng is None:
            return jsonify({'error': 'Coordinates required'}), 400
        
        api_key = os.getenv('Open_weather', '')
        if not api_key:
            response = requests.get(
                'https://api.open-meteo.com/v1/forecast',
                params={
                    'latitude': lat,
                    'longitude': lng,
                    'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m',
                    'timezone': 'auto'
                },
                timeout=5
            )
            if response.status_code != 200:
                return jsonify({'error': 'Unable to fetch weather data'}), 503
            current = response.json().get('current', {})
            weather_code = current.get('weather_code')
            weather_labels = {
                0: 'Clear', 1: 'Mostly clear', 2: 'Partly cloudy', 3: 'Overcast',
                45: 'Fog', 48: 'Rime fog', 51: 'Light drizzle', 53: 'Drizzle',
                55: 'Heavy drizzle', 61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
                71: 'Light snow', 73: 'Snow', 75: 'Heavy snow', 80: 'Rain showers',
                81: 'Rain showers', 82: 'Heavy rain showers', 95: 'Thunderstorm',
                96: 'Thunderstorm with hail', 99: 'Thunderstorm with hail'
            }
            return jsonify({
                'temp': current.get('temperature_2m'),
                'feels_like': current.get('apparent_temperature'),
                'humidity': current.get('relative_humidity_2m'),
                'wind_speed': current.get('wind_speed_10m'),
                'description': weather_labels.get(weather_code, 'Current conditions')
            })
        
        # Use real OpenWeatherMap API with coordinates
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={api_key}&units=metric"
        try:
            response = requests.get(url, timeout=5)
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Weather service timed out'}), 504
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'Unable to connect to weather service'}), 503
        
        if response.status_code != 200:
            return jsonify({'error': 'Unable to fetch weather data'}), 500
        
        data = response.json()
        
        return jsonify({
            'city': data.get('name', 'Unknown'),
            'temp': round(data.get('main', {}).get('temp', 0)),
            'feels_like': round(data.get('main', {}).get('feels_like', 0)),
            'humidity': data.get('main', {}).get('humidity', 0),
            'wind_speed': round(data.get('wind', {}).get('speed', 0) * 3.6, 1),  # Convert m/s to km/h
            'visibility': round(data.get('visibility', 10000) / 1000, 1),
            'description': data.get('weather', [{}])[0].get('main', 'Unknown'),
            'icon': data.get('weather', [{}])[0].get('icon', '01d')
        })
    
    except Exception as e:
        return jsonify({'error': f'Weather service error: {str(e)}'}), 500

@app.route('/api/sos', methods=['POST'])
@jwt_required()
def sos_alert():
    data = request.get_json()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if latitude is None or longitude is None:
        return jsonify({'error': 'Location required'}), 400
    
    try:
        emergency_places = search_nearby_osm(latitude, longitude, 2000, 'emergency')
    except Exception as e:
        print(f"SOS nearby-services lookup failed: {e}")
        emergency_places = []
    
    socketio.emit('emergency_alert', {
        'user_id': user_id,
        'username': user.username if user else 'User',
        'latitude': latitude,
        'longitude': longitude,
        'emergency_services': emergency_places[:5],
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)
    
    return jsonify({
        'success': True,
        'message': 'SOS alert shared with connected YATRIKA users. This does not contact emergency services.',
        'emergency_services': emergency_places[:5]
    })

# ---------- BOOKING ENGINE API (Mock Data) ----------
# In-memory storage for bookings
bookings_db = {}
booking_counter = 1000

# Availability pools
flight_inventory = {}
train_inventory = {}
hotel_inventory = {}
cab_inventory = {}
cruise_inventory = {}

def init_inventory():
    """Initialize mock availability for next 30 days"""
    today = datetime.now().date()
    cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Goa", "Jaipur"]
    hotel_cities = cities + ["Paris", "London", "Dubai", "Singapore", "Bangkok"]
    
    for i in range(30):
        date = today + timedelta(days=i)
        date_str = date.isoformat()
        
        # Flights
        for origin in cities[:5]:
            for dest in cities[:5]:
                if origin != dest:
                    key = f"{origin}|{dest}|{date_str}"
                    flight_inventory[key] = {'flights': [], 'booked': 0}
                    airlines = ["IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air"]
                    for _ in range(random.randint(5, 10)):
                        flight = {
                            'flight_number': f"{random.choice(['6E','AI','SG','UK','QP'])}{random.randint(100,999)}",
                            'airline': random.choice(airlines),
                            'departure_time': f"{random.randint(5,22):02d}:{random.randint(0,59):02d}",
                            'arrival_time': f"{random.randint(6,23):02d}:{random.randint(0,59):02d}",
                            'duration': random.randint(60, 240),
                            'price': random.randint(2500, 12000),
                            'seats': random.randint(50, 200),
                            'origin': origin,
                            'destination': dest,
                            'date': date_str
                        }
                        flight_inventory[key]['flights'].append(flight)
        
        # Trains
        for origin in cities[:4]:
            for dest in cities[:4]:
                if origin != dest:
                    key = f"{origin}|{dest}|{date_str}"
                    train_inventory[key] = {'trains': [], 'booked': 0}
                    for _ in range(random.randint(3, 8)):
                        train = {
                            'train_number': f"{random.randint(10000, 99999)}",
                            'train_name': random.choice(["Rajdhani", "Shatabdi", "Duronto", "Garib Rath"]),
                            'departure_time': f"{random.randint(5,22):02d}:{random.randint(0,59):02d}",
                            'arrival_time': f"{random.randint(6,23):02d}:{random.randint(0,59):02d}",
                            'duration': random.randint(180, 720),
                            'price': random.randint(300, 3000),
                            'seats': random.randint(100, 500),
                            'origin': origin,
                            'destination': dest,
                            'date': date_str
                        }
                        train_inventory[key]['trains'].append(train)
        
        # Hotels
        for city in hotel_cities:
            key = f"{city}|{date_str}"
            hotel_inventory[key] = {'hotels': [], 'booked': 0}
            hotel_chains = ["Taj", "Oberoi", "ITC", "Marriott", "Hilton", "Hyatt"]
            room_types = ["Standard", "Deluxe", "Suite", "Executive"]
            for _ in range(random.randint(10, 20)):
                hotel = {
                    'name': random.choice(hotel_chains) + " " + random.choice(["Palace", "Resort", "Grand", "Inn"]),
                    'room_type': random.choice(room_types),
                    'price_per_night': random.randint(2000, 25000),
                    'available_rooms': random.randint(10, 100),
                    'rating': round(random.uniform(3.5, 5.0), 1),
                    'city': city,
                    'check_in': date_str
                }
                hotel_inventory[key]['hotels'].append(hotel)
        
        # Cabs
        for city in cities[:3]:
            key = f"{city}|{date_str}"
            cab_inventory[key] = {'cabs': [], 'booked': 0}
            cab_companies = ["Uber", "Ola", "Mega Cabs", "Meru"]
            cab_types = ["Micro", "Mini", "Sedan", "SUV", "Luxury"]
            for _ in range(random.randint(20, 50)):
                cab = {
                    'type': random.choice(cab_types),
                    'company': random.choice(cab_companies),
                    'price_km': random.randint(8, 25),
                    'base_fare': random.randint(50, 150),
                    'available': random.randint(5, 30),
                    'city': city,
                    'date': date_str
                }
                cab_inventory[key]['cabs'].append(cab)
        
        # Cruises
        cruise_routes = ["Mumbai-Goa", "Chennai-Singapore", "Mumbai-Dubai", "Kochi-Maldives"]
        for route in cruise_routes:
            key = f"{route}|{date_str}"
            cruise_inventory[key] = {'cruises': [], 'booked': 0}
            cruise_lines = ["Carnival", "Royal Caribbean", "Norwegian", "MSC"]
            for _ in range(random.randint(1, 3)):
                cruise = {
                    'name': random.choice(cruise_lines) + " " + random.choice(["Dream", "Explorer", "Princess"]),
                    'duration_days': random.choice([3, 5, 7, 10]),
                    'price': random.randint(15000, 150000),
                    'cabins': random.randint(50, 300),
                    'departure_time': "18:00",
                    'arrival_time': "08:00",
                    'route': route,
                    'date': date_str
                }
                cruise_inventory[key]['cruises'].append(cruise)

def generate_booking_id():
    global booking_counter
    booking_counter += 1
    return f"BK{booking_counter}"

def parse_engine_date(date_value):
    """Parse date values coming from booking engine payloads."""
    if not date_value:
        return datetime.utcnow().date()
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value[:10], '%Y-%m-%d').date()
        except ValueError:
            return datetime.utcnow().date()
    return datetime.utcnow().date()

def create_db_booking_from_engine(user_id, booking_type, details):
    """Create a persistent Booking row from engine booking payload."""
    provider = (
        details.get('provider')
        or details.get('airline')
        or details.get('train_name')
        or details.get('company')
        or details.get('name')
        or booking_type.title()
    )

    booking_date = parse_engine_date(
        details.get('date')
        or details.get('check_in')
        or details.get('booking_date')
    )

    booking = Booking(
        user_id=user_id,
        booking_type=booking_type,
        provider=provider,
        from_location=details.get('origin') or details.get('from') or details.get('city'),
        to_location=details.get('destination') or details.get('to') or details.get('route') or details.get('city'),
        date=booking_date,
        time=details.get('departure_time') or details.get('time'),
        price=float(details.get('total_price') or details.get('price') or details.get('base_fare') or 0),
        travelers=int(details.get('travelers') or 1),
        special_requests=details.get('special_requests', ''),
        payment_id=details.get('payment_id'),
        order_id=details.get('order_id'),
        status='confirmed'
    )

    if booking_type == 'flight':
        booking.flight_number = details.get('flight_number')
        booking.airline = details.get('airline')
        booking.duration = str(details.get('duration', '')) if details.get('duration') else None
    elif booking_type == 'train':
        booking.train_number = details.get('train_number')
        booking.train_name = details.get('train_name')
        booking.coach = details.get('coach')
        booking.seat_number = details.get('seat_number')
    elif booking_type == 'hotel':
        booking.hotel_name = details.get('name') or details.get('hotel_name') or provider
        booking.room_type = details.get('room_type')
        booking.check_in = parse_engine_date(details.get('check_in'))
        booking.check_out = parse_engine_date(details.get('check_out')) if details.get('check_out') else None
        booking.nights = int(details.get('nights') or 1)
    elif booking_type == 'bus':
        booking.bus_operator = details.get('operator') or details.get('company') or provider
        booking.bus_number = details.get('bus_number')
        booking.seat_numbers = details.get('seat_numbers')

    db.session.add(booking)
    db.session.commit()
    return booking

# Initialize inventory
init_inventory()

# API Endpoints
@app.route('/api/engine/flights', methods=['GET'])
def engine_flights():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')
    if not all([origin, destination, date]):
        return jsonify({'error': 'Missing parameters'}), 400
    key = f"{origin}|{destination}|{date}"
    data = flight_inventory.get(key, {})
    flights = data.get('flights', [])
    booked = data.get('booked', 0)
    total_seats = sum(f['seats'] for f in flights)
    if total_seats > 0:
        demand_factor = booked / total_seats
        for f in flights:
            f['price'] = int(f['price'] * (1 + demand_factor * 0.5))
            f['available_seats'] = max(0, f['seats'] - int(booked / max(1, len(flights))))
    return jsonify({'success': True, 'results': flights})

@app.route('/api/engine/trains', methods=['GET'])
def engine_trains():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')
    if not all([origin, destination, date]):
        return jsonify({'error': 'Missing parameters'}), 400
    key = f"{origin}|{destination}|{date}"
    data = train_inventory.get(key, {})
    trains = data.get('trains', [])
    booked = data.get('booked', 0)
    for t in trains:
        t['available_seats'] = max(0, t['seats'] - int(booked / max(1, len(trains))))
    return jsonify({'success': True, 'results': trains})

@app.route('/api/engine/hotels', methods=['GET'])
def engine_hotels():
    city = request.args.get('city')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    guests = request.args.get('guests', 1, type=int)
    if not all([city, check_in, check_out]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    start = datetime.strptime(check_in, '%Y-%m-%d')
    end = datetime.strptime(check_out, '%Y-%m-%d')
    nights = (end - start).days
    if nights <= 0:
        return jsonify({'error': 'Invalid date range'}), 400
    
    key = f"{city}|{check_in}"
    data = hotel_inventory.get(key, {})
    hotels = data.get('hotels', [])
    for h in hotels:
        h['total_price'] = h['price_per_night'] * nights
        h['nights'] = nights
        h['available_rooms'] = max(0, h['available_rooms'] - data.get('booked', 0))
    return jsonify({'success': True, 'results': hotels})

@app.route('/api/engine/cabs', methods=['GET'])
def engine_cabs():
    city = request.args.get('city')
    date = request.args.get('date')
    if not all([city, date]):
        return jsonify({'error': 'Missing parameters'}), 400
    key = f"{city}|{date}"
    data = cab_inventory.get(key, {})
    cabs = data.get('cabs', [])
    for c in cabs:
        c['available'] = max(0, c['available'] - data.get('booked', 0))
    return jsonify({'success': True, 'results': cabs})

@app.route('/api/engine/cruises', methods=['GET'])
def engine_cruises():
    route = request.args.get('route')
    date = request.args.get('date')
    if not all([route, date]):
        return jsonify({'error': 'Missing parameters'}), 400
    key = f"{route}|{date}"
    data = cruise_inventory.get(key, {})
    cruises = data.get('cruises', [])
    for c in cruises:
        c['available_cabins'] = max(0, c['cabins'] - data.get('booked', 0))
    return jsonify({'success': True, 'results': cruises})

@app.route('/api/engine/book', methods=['POST'])
@jwt_required()
def engine_book():
    data = request.get_json()
    user_id = get_jwt_identity()
    booking_type = data.get('type')
    details = data.get('details')
    if not booking_type or not details:
        return jsonify({'error': 'Missing booking details'}), 400
    
    booking_id = generate_booking_id()
    booking = {
        'booking_id': booking_id,
        'type': booking_type,
        'status': 'confirmed',
        'created_at': datetime.now().isoformat(),
        'details': details
    }
    bookings_db[booking_id] = booking

    db_booking = None
    try:
        db_booking = create_db_booking_from_engine(user_id, booking_type, details)
        event_map = {
            'flight': 'booking_flight',
            'hotel': 'booking_hotel',
            'train': 'booking_train',
            'cab': 'booking_cab',
            'bus': 'booking_bus',
            'cruise': 'booking_cruise'
        }
        event_type = event_map.get((booking_type or '').lower())
        if event_type:
            award_event(user_id, event_type, event_ref=db_booking.id if db_booking else booking_id, meta={'source': 'engine_book'})
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Booking could not be saved: {str(e)}'}), 500
    
    # Update inventory
    if booking_type == 'flight':
        key = f"{details.get('origin')}|{details.get('destination')}|{details.get('date')}"
        if key in flight_inventory:
            flight_inventory[key]['booked'] += details.get('travelers', 1)
    elif booking_type == 'train':
        key = f"{details.get('origin')}|{details.get('destination')}|{details.get('date')}"
        if key in train_inventory:
            train_inventory[key]['booked'] += details.get('travelers', 1)
    elif booking_type == 'hotel':
        key = f"{details.get('city')}|{details.get('check_in')}"
        if key in hotel_inventory:
            hotel_inventory[key]['booked'] += 1
    elif booking_type == 'cab':
        key = f"{details.get('city')}|{details.get('date')}"
        if key in cab_inventory:
            cab_inventory[key]['booked'] += 1
    elif booking_type == 'cruise':
        key = f"{details.get('route')}|{details.get('date')}"
        if key in cruise_inventory:
            cruise_inventory[key]['booked'] += 1
    
    return jsonify({'success': True, 'booking': booking, 'db_booking_id': db_booking.id if db_booking else None})

@app.route('/api/engine/booking/<booking_id>', methods=['GET'])
@jwt_required()
def engine_get_booking(booking_id):
    booking = bookings_db.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    return jsonify({'success': True, 'booking': booking})

@app.route('/api/engine/booking/<booking_id>/cancel', methods=['POST'])
@jwt_required()
def engine_cancel_booking(booking_id):
    if booking_id in bookings_db:
        bookings_db[booking_id]['status'] = 'cancelled'
        return jsonify({'success': True, 'message': 'Booking cancelled'})
    return jsonify({'error': 'Booking not found'}), 404

@app.route('/api/engine/booking/<booking_id>/status', methods=['GET'])
@jwt_required()
def engine_booking_status(booking_id):
    booking = bookings_db.get(booking_id)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    status = {
        'booking_id': booking_id,
        'type': booking['type'],
        'status': booking['status'],
        'last_updated': datetime.now().isoformat()
    }
    
    if booking['type'] == 'flight':
        status['flight_status'] = random.choice(['On Time', 'Delayed', 'Boarding', 'Departed', 'Landed'])
        status['gate'] = random.choice(['A1', 'B3', 'C2', 'D5'])
        status['terminal'] = random.randint(1, 4)
    elif booking['type'] == 'train':
        status['train_status'] = random.choice(['On Time', 'Delayed', 'Running', 'Arrived'])
        status['platform'] = random.randint(1, 12)
    elif booking['type'] == 'hotel':
        status['check_in_status'] = 'Confirmed'
        status['room_number'] = random.randint(101, 500)
    elif booking['type'] == 'cab':
        status['driver_name'] = f"Driver {random.randint(100,999)}"
        status['cab_number'] = f"KA{random.randint(1,99)}AB{random.randint(1000,9999)}"
        status['eta_minutes'] = random.randint(3, 15)
    elif booking['type'] == 'cruise':
        status['cruise_status'] = random.choice(['Docked', 'Loading', 'Departed', 'At Sea'])
        status['boarding_gate'] = random.choice(['A', 'B', 'C', 'D'])
    
    return jsonify({'success': True, 'status': status})

@app.route('/api/engine/bookings', methods=['GET'])
@jwt_required()
def get_user_bookings():
    """Get all bookings for the logged-in user"""
    user_id = get_jwt_identity()
    db_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    return jsonify({'success': True, 'bookings': [b.to_dict() for b in db_bookings], 'count': len(db_bookings)})

# ---------- Real Flight Search API ----------
@app.route('/api/flights/search', methods=['GET'])
def search_flights_api():
    from_location = request.args.get('from', '').strip().upper()
    to_location = request.args.get('to', '').strip().upper()
    date = request.args.get('date', '')
    
    if not AVIATION_STACK_KEY:
        return jsonify({'success': True, 'flights': get_sample_flights(), 'count': 5}), 200
    
    if not from_location or not to_location:
        return jsonify({'success': False, 'error': 'Origin and destination required', 'flights': []}), 200
    
    params = {'access_key': AVIATION_STACK_KEY, 'dep_iata': from_location, 'arr_iata': to_location, 'limit': 20}
    if date:
        params['flight_date'] = date
    
    try:
        response = requests.get('http://api.aviationstack.com/v1/flights', params=params, timeout=10)
        data = response.json()
        flights = []
        for flight in data.get('data', []):
            flights.append({
                'airline': flight.get('airline', {}).get('name', 'Unknown'),
                'airline_iata': flight.get('airline', {}).get('iata', ''),
                'flight_number': flight.get('flight', {}).get('iata', ''),
                'departure_airport': flight.get('departure', {}).get('airport', 'Unknown'),
                'departure_iata': flight.get('departure', {}).get('iata', ''),
                'departure_time': flight.get('departure', {}).get('scheduled', ''),
                'arrival_airport': flight.get('arrival', {}).get('airport', 'Unknown'),
                'arrival_iata': flight.get('arrival', {}).get('iata', ''),
                'arrival_time': flight.get('arrival', {}).get('scheduled', ''),
                'status': flight.get('flight_status', 'scheduled'),
                'price': random.randint(150, 800)
            })
        return jsonify({'success': True, 'flights': flights, 'count': len(flights)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'flights': get_sample_flights()}), 200

# ---------- Smart Itinerary API ----------
@app.route('/api/smart_itinerary', methods=['POST'])
@jwt_required()
def smart_itinerary():
    data = request.get_json()
    destination = data.get('destination', '').strip()
    days = int(data.get('days', 3))
    budget = float(data.get('budget', 0))
    preferences = data.get('preferences', '')
    start_date = data.get('start_date', '')
    save_trip = data.get('save_trip', True)
    user_id = get_jwt_identity()
    
    if not destination:
        return jsonify({'error': 'Destination is required'}), 400
    
    if not groq_client:
        return jsonify({'error': 'AI service not configured', 'source': 'error'}), 500
    
    try:
        return generate_ai_itinerary(destination, days, budget, preferences, start_date, save_trip, user_id)
    except Exception as e:
        return jsonify({'error': str(e), 'source': 'error'}), 500

def generate_ai_itinerary(destination, days, budget, preferences, start_date, save_trip, user_id):
    days = max(1, min(days, 30))
    preferences = preferences.strip() or 'general sightseeing and local food'
    prompt = f"""You are a practical travel planner. Create a realistic itinerary for:
Destination: {destination}
Duration: exactly {days} days
Total budget: INR {budget:,.0f}
Preferences: {preferences}
Start date: {start_date or 'not specified'}

Return one entry for every day, numbered consecutively from 1 through {days}.
Give each day 3 to 5 geographically sensible activities in chronological order.
Include transport, entry fees, food, and paid experiences where appropriate. Set each activity's cost to its realistic INR estimate and make total_estimated_cost equal the sum of all activity costs. Do not include markdown or text outside the JSON response."""

    itinerary_schema = {
        'type': 'object',
        'properties': {
            'destination': {'type': 'string'},
            'days': {'type': 'integer'},
            'total_estimated_cost': {'type': 'number'},
            'currency': {'type': 'string'},
            'itinerary': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'day': {'type': 'integer'},
                        'activities': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'time': {'type': 'string'},
                                    'name': {'type': 'string'},
                                    'duration': {'type': 'string'},
                                    'cost': {'type': 'number'},
                                    'description': {'type': 'string'}
                                },
                                'required': ['time', 'name', 'duration', 'cost', 'description'],
                                'additionalProperties': False
                            }
                        }
                    },
                    'required': ['day', 'activities'],
                    'additionalProperties': False
                }
            },
            'travel_tips': {'type': 'array', 'items': {'type': 'string'}},
            'best_time_to_visit': {'type': 'string'},
            'local_cuisine': {'type': 'array', 'items': {'type': 'string'}}
        },
        'required': ['destination', 'days', 'total_estimated_cost', 'currency', 'itinerary', 'travel_tips', 'best_time_to_visit', 'local_cuisine'],
        'additionalProperties': False
    }
    
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "Return only a valid JSON object that matches the supplied schema."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=4000,
        response_format={
            'type': 'json_schema',
            'json_schema': {
                'name': 'day_wise_itinerary',
                'strict': True,
                'schema': itinerary_schema
            }
        }
    )
    
    result_text = response.choices[0].message.content.strip()
    result_text = result_text.replace('```json', '').replace('```', '').strip()
    
    try:
        itinerary_data = json.loads(result_text)
        itinerary = itinerary_data.get('itinerary', [])
        expected_day_numbers = list(range(1, days + 1))
        actual_day_numbers = [item.get('day') for item in itinerary]
        if actual_day_numbers != expected_day_numbers:
            raise ValueError('The generated itinerary did not contain every requested day.')

        # Derive the total from the displayed activities so it always matches.
        total_estimated_cost = 0.0
        for day in itinerary:
            for activity in day.get('activities', []):
                try:
                    total_estimated_cost += max(0, float(activity.get('cost', 0)))
                except (TypeError, ValueError):
                    activity['cost'] = 0
        itinerary_data['total_estimated_cost'] = round(total_estimated_cost, 2)
        itinerary_data['currency'] = 'INR'
        trip_id = None
        if save_trip:
            try:
                parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else datetime.utcnow().date()
                parsed_end = parsed_start + timedelta(days=max(days - 1, 0))
                itinerary_items = []
                for day_data in itinerary_data.get('itinerary', []):
                    day_num = day_data.get('day', '')
                    activities = day_data.get('activities', [])
                    if activities and isinstance(activities, list):
                        first_activity = activities[0].get('name', 'Explore the destination')
                        itinerary_items.append(f"Day {day_num}: {first_activity}")
                    else:
                        itinerary_items.append(f"Day {day_num}: Explore {destination}")

                trip = Trip(
                    user_id=user_id,
                    destination=destination,
                    start_date=parsed_start,
                    end_date=parsed_end,
                    budget=budget,
                    itinerary=json.dumps(itinerary_items)
                )
                db.session.add(trip)
                db.session.commit()
                trip_id = trip.id
            except Exception as trip_save_error:
                db.session.rollback()
                app.logger.exception('Failed to save generated trip: %s', trip_save_error)

        try:
            award_event(user_id, 'ai_itinerary', meta={'destination': destination, 'days': days})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Gamification AI itinerary award failed: {e}")

        return jsonify({
            'success': True,
            'source': 'groq_ai',
            'trip_saved': trip_id is not None,
            'trip_id': trip_id,
            **itinerary_data
        })
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        app.logger.error('Groq returned invalid itinerary JSON: %s', error)
        return jsonify({'success': False, 'error': 'The AI returned an invalid itinerary. Please try again.'}), 502

# ---------- Helper Functions ----------
def get_sample_flights():
    return [
        {'airline': 'Emirates', 'airline_iata': 'EK', 'flight_number': 'EK524',
         'departure_airport': 'Dubai Airport', 'departure_iata': 'DXB',
         'departure_time': '2025-04-15T09:30:00', 'arrival_airport': 'Mumbai Airport',
         'arrival_iata': 'BOM', 'arrival_time': '2025-04-15T14:45:00',
         'status': 'scheduled', 'price': 450},
        {'airline': 'Air India', 'airline_iata': 'AI', 'flight_number': 'AI101',
         'departure_airport': 'Delhi Airport', 'departure_iata': 'DEL',
         'departure_time': '2025-04-15T06:00:00', 'arrival_airport': 'Mumbai Airport',
         'arrival_iata': 'BOM', 'arrival_time': '2025-04-15T08:15:00',
         'status': 'scheduled', 'price': 180}
    ]

def get_sample_trains():
    return [
        {'train_number': '12951', 'train_name': 'Mumbai Rajdhani Express',
         'source': 'Mumbai Central', 'source_code': 'BCT', 'destination': 'New Delhi',
         'destination_code': 'NDLS', 'departure_time': '16:35', 'arrival_time': '08:30',
         'duration': '15h 55m', 'classes': ['1A', '2A', '3A'], 'price': 2500}
    ]

def get_sample_hotels():
    return [
        {'name': 'Taj Mahal Palace', 'city': 'Mumbai', 'price_per_night': 25000, 'rating': 4.8,
         'amenities': ['Pool', 'Spa', 'Restaurant', 'Free WiFi']}
    ]

@app.route('/api/trains/search', methods=['GET'])
def search_trains_api():
    return jsonify({'success': True, 'trains': get_sample_trains(), 'count': 1}), 200

@app.route('/api/hotels/search', methods=['GET'])
def search_hotels_api():
    city = request.args.get('city', '')
    hotels = get_sample_hotels()
    if city:
        hotels = [h for h in hotels if city.lower() in h['city'].lower()]
    return jsonify({'success': True, 'hotels': hotels, 'count': len(hotels)})

# ---------- Authentication Routes ----------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No data provided'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'msg': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'msg': 'Email already exists'}), 400
    
    hashed = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed)
    db.session.add(user)
    db.session.commit()
    try:
        award_event(user.id, 'signup', meta={'source': 'register'})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gamification signup award failed: {e}")
    return jsonify({'msg': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'msg': 'Invalid credentials'}), 401

    try:
        ensure_user_missions(user.id)
        process_daily_login(user.id)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gamification login processing failed: {e}")
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token})

@app.route('/api/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

@app.route('/api/geocode', methods=['GET'])
def geocode():
    place = request.args.get('place')
    if not place:
        return jsonify({'error': 'Place name required'}), 400
    
    try:
        import urllib.parse
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place)}&format=json&limit=1"
        headers = {'User-Agent': 'YATRIKA-TravelApp/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return jsonify({
                    'lat': float(data[0]['lat']),
                    'lng': float(data[0]['lon']),
                    'display_name': data[0].get('display_name', place)
                })
    except Exception as e:
        print(f"Geocode error: {e}")
    
    return jsonify({'error': 'Place not found'}), 404

@app.route('/api/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'bio' in data:
        user.bio = data['bio']
    if 'phone' in data:
        user.phone = data['phone']
    
    db.session.commit()

    try:
        if _profile_is_complete(user):
            award_event(user.id, 'profile_completion', meta={'source': 'profile_update'})
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gamification profile completion award failed: {e}")

    return jsonify({'msg': 'Profile updated successfully'})

@app.route('/api/profile/preferences', methods=['POST'])
@jwt_required()
def save_profile_preferences():
    """Save user preferences like language"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    # Preferences are stored on client-side, this endpoint just acknowledges them
    # for future extensibility
    data = request.get_json() or {}
    language = data.get('language', 'en')
    
    # Log the preference (could be extended later)
    print(f"User {user_id} set language preference to: {language}")
    
    return jsonify({'msg': 'Preferences saved successfully', 'language': language}), 200

@app.route('/api/change_password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    if not check_password_hash(user.password_hash, data.get('current_password')):
        return jsonify({'msg': 'Current password is incorrect'}), 401
    
    new_password = data.get('new_password')
    if not new_password or len(new_password) < 6:
        return jsonify({'msg': 'Password must be at least 6 characters'}), 400
    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'msg': 'Password changed successfully'})

@app.route('/api/delete_account', methods=['DELETE'])
@jwt_required()
def delete_account():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    
    Trip.query.filter_by(user_id=user_id).delete()
    Booking.query.filter_by(user_id=user_id).delete()
    TravelStory.query.filter_by(user_id=user_id).delete()
    Wishlist.query.filter_by(user_id=user_id).delete()
    Notification.query.filter_by(user_id=user_id).delete()
    Review.query.filter_by(user_id=user_id).delete()
    Expense.query.filter_by(user_id=user_id).delete()
    VisaApplication.query.filter_by(user_id=user_id).delete()
    Place.query.filter_by(user_id=user_id).delete()
    CompanionProfile.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'msg': 'Account deleted successfully'})

# ---------- Trip Routes ----------
@app.route('/api/trips', methods=['POST'])
@jwt_required()
def create_trip():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    trip = Trip(
        user_id=user_id,
        destination=data.get('destination'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d'),
        budget=data.get('budget', 0),
        itinerary=json.dumps([])
    )
    db.session.add(trip)
    db.session.commit()
    return jsonify({'id': trip.id, 'message': 'Trip created successfully'})

@app.route('/api/trips', methods=['GET'])
@jwt_required()
def get_trips():
    user_id = get_jwt_identity()
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.start_date.desc()).all()
    result = []
    for t in trips:
        itinerary = []
        if t.itinerary:
            try:
                parsed_itinerary = json.loads(t.itinerary)
                if isinstance(parsed_itinerary, list):
                    itinerary = parsed_itinerary
            except (json.JSONDecodeError, TypeError):
                itinerary = []

        result.append({
            'id': t.id,
            'destination': t.destination,
            'start_date': t.start_date.isoformat(),
            'end_date': t.end_date.isoformat(),
            'budget': t.budget,
            'itinerary': itinerary,
            'created_at': t.created_at.isoformat() if t.created_at else None
        })
    return jsonify(result)

# ---------- Booking Routes ----------
@app.route('/api/bookings', methods=['POST', 'GET'])
@jwt_required()
def bookings():
    user_id = get_jwt_identity()
    
    if request.method == 'POST':
        data = request.get_json()
        booking = Booking(
            user_id=user_id,
            booking_type=data.get('type'),
            provider=data.get('provider'),
            from_location=data.get('from_location'),
            to_location=data.get('to_location'),
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            price=float(data['price']),
            travelers=data.get('travelers', 1)
        )
        db.session.add(booking)
        event_map = {
            'flight': 'booking_flight',
            'hotel': 'booking_hotel',
            'train': 'booking_train',
            'cab': 'booking_cab',
            'bus': 'booking_bus',
            'cruise': 'booking_cruise'
        }
        event_type = event_map.get((data.get('type') or '').lower(), 'booking_bus')
        try:
            db.session.flush()
            award_event(user_id, event_type, event_ref=booking.id, meta={'provider': booking.provider})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Gamification booking event failed: {e}")
            db.session.add(booking)
            db.session.commit()
        return jsonify({'id': booking.id, 'message': 'Booking confirmed'}), 201
    
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.date.desc()).all()
    result = []
    for b in bookings:
        booking_data = b.to_dict()
        booking_data['destination'] = b.to_location or b.hotel_name or b.provider
        booking_data['travel_date'] = b.date.isoformat() if b.date else None
        booking_data['booking_date'] = b.created_at.isoformat() if b.created_at else None
        result.append(booking_data)
    return jsonify(result)

@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    user_id = get_jwt_identity()
    booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    booking.status = 'cancelled'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Booking cancelled successfully'})


# ---------- Story Routes ----------
@app.route('/api/stories', methods=['GET', 'POST'])
def stories_api():
    if request.method == 'GET':
        stories = TravelStory.query.order_by(TravelStory.created_at.desc()).all()
        result = []
        for s in stories:
            image_list = []
            if s.images:
                image_list = [img.strip() for img in s.images.split(',') if img.strip()]

            result.append({
                'id': s.id,
                'user': s.user.username if s.user else 'Unknown',
                'title': s.title,
                'content': s.content,
                'images': image_list,
                'likes': s.likes or 0,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        return jsonify(result)

    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
    except Exception:
        return jsonify({'msg': 'Missing or invalid token'}), 401

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if not title or not content:
        return jsonify({'msg': 'Title and content are required'}), 400

    uploaded_files = request.files.getlist('images')
    saved_images = []
    for uploaded in uploaded_files[:5]:
        filename = save_uploaded_file(uploaded)
        if filename:
            saved_images.append(f"uploads/{filename}")

    story = TravelStory(
        user_id=user_id,
        title=title,
        content=content,
        images=','.join(saved_images),
        likes=0
    )
    db.session.add(story)
    try:
        db.session.flush()
        if saved_images:
            for _ in saved_images:
                award_event(user_id, 'trip_photo_upload', event_ref=story.id, meta={'title': title})
        award_event(user_id, 'review_posted', event_ref=story.id, meta={'title': title})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gamification story/review awards failed: {e}")
        db.session.add(story)
        db.session.commit()

    return jsonify({'msg': 'Story published successfully', 'id': story.id}), 201


# ---------- Review Routes ----------
@app.route('/api/reviews', methods=['GET', 'POST'])
@jwt_required(optional=True)
def reviews_api():
    if request.method == 'GET':
        destination = request.args.get('destination')
        q = Review.query
        if destination:
            q = q.filter(Review.destination.ilike(f"%{destination}%"))
        reviews = q.order_by(Review.created_at.desc()).limit(100).all()
        return jsonify([
            {
                'id': r.id,
                'user': r.user.username if r.user else 'Unknown',
                'destination': r.destination,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.isoformat() if r.created_at else None
            }
            for r in reviews
        ])

    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    data = request.get_json() or {}
    destination = (data.get('destination') or '').strip()
    rating = int(data.get('rating') or 0)
    comment = (data.get('comment') or '').strip()

    if not destination or rating < 1 or rating > 5 or not comment:
        return jsonify({'error': 'destination, rating (1-5), and comment are required'}), 400

    review = Review(user_id=user_id, destination=destination, rating=rating, comment=comment)
    db.session.add(review)
    try:
        db.session.flush()
        award_event(user_id, 'review_posted', event_ref=review.id, meta={'destination': destination})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Gamification review award failed: {e}")
        db.session.add(review)
        db.session.commit()

    return jsonify({'success': True, 'id': review.id, 'message': 'Review added successfully'}), 201

# ---------- REAL RAZORPAY ORDER ENDPOINT ----------
@app.route('/api/create_order', methods=['POST'])
@jwt_required()
def create_order():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data received'}), 400

    amount = data.get('amount')

    if amount is None:
        return jsonify({'error': 'Amount required'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid amount format: {e}'}), 400

    amount_in_paise = int(round(amount * 100))

    # Try real Razorpay
    if RAZORPAY_AVAILABLE and RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'payment_capture': 1
            })
            print(f"✅ Razorpay order created: {order['id']}")
            return jsonify({
                'id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'status': order['status']
            })
        except Exception as e:
            print(f"❌ Razorpay error: {e}")
            return jsonify({
                'id': f"mock_{uuid.uuid4().hex[:12]}",
                'amount': amount_in_paise,
                'currency': 'INR',
                'status': 'created'
            })

    return jsonify({
        'id': f"mock_{uuid.uuid4().hex[:12]}",
        'amount': amount_in_paise,
        'currency': 'INR',
        'status': 'created'
    })

# ---------- VISA APPLICATION ROUTES ----------
@app.route('/api/visa/apply', methods=['POST'])
@jwt_required()
def apply_visa():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        country = data.get('country')
        notes = data.get('notes', '')
        
        if not country:
            return jsonify({'error': 'Country is required'}), 400
        
        # Create visa application record
        visa_app = VisaApplication(
            user_id=user_id,
            country=country,
            notes=notes,
            status='Submitted'
        )
        db.session.add(visa_app)
        db.session.commit()
        
        # Generate application ID
        app_id = f"VISA{visa_app.id:06d}"
        
        return jsonify({
            'success': True,
            'application_id': app_id,
            'status': 'Submitted',
            'message': 'Visa application submitted successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Visa application error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/visa/applications', methods=['GET'])
@jwt_required()
def get_visa_applications():
    try:
        user_id = get_jwt_identity()
        applications = VisaApplication.query.filter_by(user_id=user_id).order_by(VisaApplication.applied_date.desc()).all()
        
        result = []
        for app in applications:
            result.append({
                'id': f"VISA{app.id:06d}",
                'country': app.country,
                'status': app.status,
                'applied_date': app.applied_date.isoformat(),
                'updated_at': app.updated_at.isoformat() if app.updated_at else None,
                'notes': app.notes
            })
        
        return jsonify({'applications': result, 'count': len(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/visa/requirements', methods=['GET'])
def get_visa_requirements():
    """Get visa requirements for a country"""
    country = (request.args.get('country') or '').strip()
    
    visa_requirements = {
        'USA': {'required': True, 'type': 'Tourist Visa', 'processing_time': '2-4 weeks', 'fee': 160, 'currency': 'USD'},
        'UK': {'required': True, 'type': 'Standard Visitor Visa', 'processing_time': '3 weeks', 'fee': 115, 'currency': 'GBP'},
        'France': {'required': True, 'type': 'Schengen Visa', 'processing_time': '2 weeks', 'fee': 80, 'currency': 'EUR'},
        'Germany': {'required': True, 'type': 'Schengen Visa', 'processing_time': '2 weeks', 'fee': 80, 'currency': 'EUR'},
        'Italy': {'required': True, 'type': 'Schengen Visa', 'processing_time': '2 weeks', 'fee': 80, 'currency': 'EUR'},
        'Spain': {'required': True, 'type': 'Schengen Visa', 'processing_time': '2 weeks', 'fee': 80, 'currency': 'EUR'},
        'Australia': {'required': True, 'type': 'Visitor Visa', 'processing_time': '4-6 weeks', 'fee': 190, 'currency': 'AUD'},
        'Canada': {'required': True, 'type': 'Visitor Visa', 'processing_time': '5-8 weeks', 'fee': 100, 'currency': 'CAD'},
        'Japan': {'required': True, 'type': 'Tourist Visa', 'processing_time': '5-7 days', 'fee': 30, 'currency': 'USD'},
        'Singapore': {'required': False, 'type': 'Visa Free', 'processing_time': 'N/A', 'fee': 0, 'currency': 'USD'},
        'Thailand': {'required': False, 'type': 'Visa on Arrival', 'processing_time': 'On arrival', 'fee': 50, 'currency': 'USD'},
        'Malaysia': {'required': False, 'type': 'Visa Free', 'processing_time': 'N/A', 'fee': 0, 'currency': 'USD'},
        'UAE': {'required': False, 'type': 'Visa on Arrival', 'processing_time': 'On arrival', 'fee': 0, 'currency': 'USD'},
        'Turkey': {'required': True, 'type': 'eVisa', 'processing_time': '24 hours', 'fee': 60, 'currency': 'USD'},
        'Egypt': {'required': True, 'type': 'eVisa', 'processing_time': '3-5 days', 'fee': 25, 'currency': 'USD'}
    }

    if not country:
        return jsonify({'error': 'Country is required'}), 400

    # Provide a complete fallback profile for any country name while keeping detailed overrides.
    fallback = {
        'required': True,
        'type': 'Tourist Visa',
        'processing_time': '2-4 weeks',
        'fee': 75,
        'currency': 'USD'
    }

    return jsonify(visa_requirements.get(country, fallback))

# ---------- Weather API Integration ----------
@app.route('/api/weather', methods=['GET'])
def get_weather_data():
    """Fetch real-time weather data from OpenWeather API"""
    try:
        city = (request.args.get('city') or '').strip()
        if not city:
            return jsonify({'error': 'City is required'}), 400

        api_key = os.getenv('Open_weather', '')
        if not api_key:
            return jsonify({'error': 'Weather API key not configured'}), 500

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            response = requests.get(url, timeout=5)
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Weather service timed out'}), 504
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'Unable to connect to weather service'}), 503
        
        if response.status_code == 404:
            return jsonify({'error': 'City not found'}), 404
        
        if response.status_code != 200:
            return jsonify({'error': 'Unable to fetch weather data'}), 500

        data = response.json()
        
        # Extract relevant weather information
        weather_info = {
            'city': data.get('name'),
            'country': data.get('sys', {}).get('country'),
            'temperature': round(data.get('main', {}).get('temp', 0)),
            'feels_like': round(data.get('main', {}).get('feels_like', 0)),
            'humidity': data.get('main', {}).get('humidity', 0),
            'pressure': data.get('main', {}).get('pressure', 0),
            'description': data.get('weather', [{}])[0].get('main', ''),
            'wind_speed': round(data.get('wind', {}).get('speed', 0) * 3.6, 1),  # Convert m/s to km/h
            'clouds': data.get('clouds', {}).get('all', 0),
            'visibility': round(data.get('visibility', 10000) / 1000, 1),  # Convert to km
            'uvi': data.get('uvi', 0),  # UV Index
            'icon': data.get('weather', [{}])[0].get('icon', '01d')
        }
        
        # Generate travel alerts based on weather conditions
        alerts = []
        desc_lower = weather_info['description'].lower()
        
        if 'rain' in desc_lower or 'shower' in desc_lower:
            alerts.append({
                'type': 'rain',
                'message': 'Heavy rainfall expected. Bring an umbrella and be cautious on wet roads.',
                'icon': '🌧️',
                'severity': 'warning'
            })
        
        if 'storm' in desc_lower or 'thunderstorm' in desc_lower:
            alerts.append({
                'type': 'storm',
                'message': 'Thunderstorm warning! Avoid outdoor activities and stay indoors.',
                'icon': '⚡',
                'severity': 'danger'
            })
        
        if 'snow' in desc_lower or 'sleet' in desc_lower:
            alerts.append({
                'type': 'snow',
                'message': 'Snow expected. Travel conditions may be hazardous. Check weather updates regularly.',
                'icon': '❄️',
                'severity': 'warning'
            })
        
        if weather_info['temperature'] > 40:
            alerts.append({
                'type': 'heat',
                'message': f"Extreme heat alert! Temperature is {weather_info['temperature']}°C. Stay hydrated and limit outdoor activities.",
                'icon': '🔥',
                'severity': 'danger'
            })
        elif weather_info['temperature'] > 35:
            alerts.append({
                'type': 'hot',
                'message': f"High temperature ({weather_info['temperature']}°C). Use sunscreen and stay hydrated.",
                'icon': '☀️',
                'severity': 'warning'
            })
        
        if weather_info['temperature'] < 0:
            alerts.append({
                'type': 'cold',
                'message': f"Freezing temperature ({weather_info['temperature']}°C). Wear warm clothing and be cautious on icy surfaces.",
                'icon': '🥶',
                'severity': 'warning'
            })
        
        if weather_info['wind_speed'] > 40:
            alerts.append({
                'type': 'wind',
                'message': f"Strong winds ({weather_info['wind_speed']} km/h). Hold onto loose items and be cautious.",
                'icon': '💨',
                'severity': 'warning'
            })
        
        if weather_info['visibility'] < 1:
            alerts.append({
                'type': 'fog',
                'message': 'Dense fog. Reduce visibility. Drive carefully and use headlights.',
                'icon': '🌫️',
                'severity': 'warning'
            })
        
        weather_info['alerts'] = alerts
        weather_info['has_alerts'] = len(alerts) > 0
        
        return jsonify(weather_info)
    
    except Exception as e:
        return jsonify({'error': f'Weather service error: {str(e)}'}), 500

# ---------- Expense Tracking Routes ----------
@app.route('/api/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    """Add an expense to a trip"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    trip_id = data.get('trip_id')
    category = data.get('category')
    amount = data.get('amount')
    date_str = data.get('date')
    
    if not trip_id:
        return jsonify({'error': 'Trip ID is required'}), 400
    if not category:
        return jsonify({'error': 'Category is required'}), 400
    if not amount:
        return jsonify({'error': 'Amount is required'}), 400
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()
    if not trip:
        return jsonify({'error': 'Trip not found or access denied'}), 404
    
    try:
        expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            expense_date = datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    try:
        expense = Expense(
            user_id=user_id,
            trip_id=trip_id,
            category=category,
            amount=float(amount),
            date=expense_date,
            note=data.get('note', '')
        )
        db.session.add(expense)
        db.session.commit()
        return jsonify({
            'id': expense.id, 
            'message': 'Expense added successfully',
            'expense': {
                'id': expense.id,
                'category': expense.category,
                'amount': expense.amount,
                'date': expense.date.isoformat(),
                'note': expense.note
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Expense error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/trip/<int:trip_id>', methods=['GET'])
@jwt_required()
def get_trip_expenses(trip_id):
    """Get all expenses for a specific trip"""
    user_id = get_jwt_identity()
    
    trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
    
    expenses = Expense.query.filter_by(user_id=user_id, trip_id=trip_id).order_by(Expense.date.desc()).all()
    
    result = []
    for e in expenses:
        result.append({
            'id': e.id,
            'category': e.category,
            'amount': e.amount,
            'date': e.date.isoformat(),
            'note': e.note
        })
    
    total = sum(e.amount for e in expenses)
    
    return jsonify({
        'expenses': result,
        'total': total,
        'trip_name': trip.destination
    })


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):
    """Delete an expense"""
    user_id = get_jwt_identity()
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    
    if not expense:
        return jsonify({'error': 'Expense not found'}), 404
    
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Expense deleted successfully'})


@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):
    """Update an expense"""
    user_id = get_jwt_identity()
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    
    if not expense:
        return jsonify({'error': 'Expense not found'}), 404
    
    data = request.get_json()
    
    if 'category' in data:
        expense.category = data['category']
    if 'amount' in data:
        expense.amount = float(data['amount'])
    if 'date' in data:
        try:
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            try:
                expense.date = datetime.strptime(data['date'], '%m/%d/%Y').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
    if 'note' in data:
        expense.note = data['note']
    
    db.session.commit()
    return jsonify({
        'message': 'Expense updated successfully',
        'expense': {
            'id': expense.id,
            'category': expense.category,
            'amount': expense.amount,
            'date': expense.date.isoformat(),
            'note': expense.note
        }
    })


@app.route('/api/expenses/categories', methods=['GET'])
@jwt_required()
def get_expense_categories():
    """Get all expense categories for dropdown"""
    categories = [
        'Food', 'Transport', 'Accommodation', 'Activities', 'Shopping',
        'Sightseeing', 'Local Transport', 'Flights', 'Trains', 'Buses',
        'Taxis', 'Entrance Fees', 'Guide Fees', 'Tips', 'Other'
    ]
    return jsonify({'categories': categories})


# ---------- Gamification API Routes ----------
@app.route('/api/gamification/dashboard', methods=['GET'])
@jwt_required()
def gamification_dashboard():
    user_id = _to_int_user_id(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    profile = get_or_create_gamification_profile(user_id)
    ensure_user_missions(user_id)
    ensure_badges(user_id)
    refresh_achievements(user_id)
    db.session.commit()

    level_name, low, high = level_from_xp(profile.xp_total)
    progress = 100 if high <= low else int(((profile.xp_total - low) / (high - low)) * 100)
    progress = max(0, min(100, progress))

    today = datetime.utcnow().date()
    missions = UserMission.query.filter(
        UserMission.user_id == user_id,
        UserMission.window_start <= today,
        UserMission.window_end >= today
    ).order_by(UserMission.mission_type.asc(), UserMission.id.asc()).all()

    badge_rows = UserAchievement.query.filter_by(user_id=user_id).order_by(UserAchievement.id.asc()).all()
    recent_events = GamificationEvent.query.filter_by(user_id=user_id).order_by(GamificationEvent.created_at.desc()).limit(12).all()

    lb = build_leaderboard_for_scope(user_id, scope='weekly', limit=10)
    leaderboard = lb['items']

    today_earned = db.session.query(func.coalesce(func.sum(GamificationEvent.coins_delta), 0)).filter(
        GamificationEvent.user_id == user_id,
        func.date(GamificationEvent.created_at) == today,
        GamificationEvent.coins_delta > 0
    ).scalar() or 0

    result = {
        'user_id': user_id,
        'wallet': {
            'yc_balance': profile.yc_balance,
            'yc_lifetime_earned': profile.yc_lifetime_earned,
            'yc_lifetime_spent': profile.yc_lifetime_spent,
            'discount_inr': wallet_inr_value(profile.yc_balance),
            'today_earned': int(today_earned)
        },
        'level': {
            'current_level': level_name,
            'xp_total': profile.xp_total,
            'range_start': low,
            'range_end': high,
            'progress_percent': progress,
            'xp_to_next': max(0, high - profile.xp_total)
        },
        'streak': {
            'current': profile.current_streak,
            'longest': profile.longest_streak,
            'last_login_date': profile.last_login_date.isoformat() if profile.last_login_date else None,
            'day_rewards': [10, 15, 20, 25, 30, 40, 100]
        },
        'badges': [
            {
                'id': b.id,
                'code': b.badge_code,
                'title': b.title,
                'description': b.description,
                'icon': b.icon,
                'progress': b.progress,
                'target': b.target,
                'is_unlocked': b.is_unlocked,
                'unlocked_at': b.unlocked_at.isoformat() if b.unlocked_at else None
            }
            for b in badge_rows
        ],
        'missions': [
            {
                'id': m.id,
                'key': m.mission_key,
                'title': m.title,
                'mission_type': m.mission_type,
                'event_type': m.event_type,
                'current_count': m.current_count,
                'target_count': m.target_count,
                'reward_coins': m.reward_coins,
                'reward_xp': m.reward_xp,
                'is_claimed': m.is_claimed,
                'is_complete': m.current_count >= m.target_count
            }
            for m in missions
        ],
        'leaderboard': leaderboard,
        'leaderboard_meta': lb['meta'],
        'reward_store': STORE_REWARDS,
        'recent_events': [
            {
                'event_type': e.event_type,
                'coins': e.coins_delta,
                'xp': e.xp_delta,
                'created_at': e.created_at.isoformat() if e.created_at else None
            }
            for e in recent_events
        ]
    }
    return jsonify(result)


@app.route('/api/gamification/spin', methods=['POST'])
@jwt_required()
def spin_and_win():
    user_id = _to_int_user_id(get_jwt_identity())
    profile = get_or_create_gamification_profile(user_id)

    today = datetime.utcnow().date()
    existing_today = GamificationEvent.query.filter(
        GamificationEvent.user_id == user_id,
        GamificationEvent.event_type == 'spin_win',
        func.date(GamificationEvent.created_at) == today
    ).count()
    if existing_today >= 1:
        return jsonify({'error': 'Spin already used today. Try again tomorrow.'}), 400

    total_weight = sum(item['weight'] for item in SPIN_REWARDS)
    pick = random.randint(1, total_weight)
    upto = 0
    selected = SPIN_REWARDS[0]
    for item in SPIN_REWARDS:
        upto += item['weight']
        if pick <= upto:
            selected = item
            break

    profile.yc_balance += int(selected['coins'])
    profile.yc_lifetime_earned += int(selected['coins'])
    profile.xp_total += int(selected['xp'])
    level_name, _, _ = level_from_xp(profile.xp_total)
    profile.current_level = level_name

    bonus_badge_awarded = False
    bonus_badge = UserAchievement.query.filter_by(user_id=user_id, badge_code='spin_master').first()
    if not bonus_badge:
        bonus_badge = UserAchievement(
            user_id=user_id,
            badge_code='spin_master',
            title='Spin Master',
            description='Won your first Spin & Win reward',
            icon='fa-dharmachakra',
            progress=0,
            target=1,
            is_unlocked=False
        )
        db.session.add(bonus_badge)

    if selected['kind'] == 'badge' and not bonus_badge.is_unlocked:
        bonus_badge.progress = 1
        bonus_badge.is_unlocked = True
        bonus_badge.unlocked_at = datetime.utcnow()
        bonus_badge_awarded = True

    coupon = None
    if selected['kind'] == 'coupon':
        coupon = f"YW-CASH-{uuid.uuid4().hex[:8].upper()}"

    db.session.add(GamificationEvent(
        user_id=user_id,
        event_type='spin_win',
        event_ref=selected['key'],
        coins_delta=int(selected['coins']),
        xp_delta=int(selected['xp']),
        meta_json=json.dumps({'label': selected['label'], 'coupon': coupon})
    ))
    db.session.commit()

    return jsonify({
        'success': True,
        'reward': selected['label'],
        'coins': int(selected['coins']),
        'xp': int(selected['xp']),
        'coupon': coupon,
        'bonus_badge': bonus_badge_awarded,
        'new_balance': profile.yc_balance
    })


@app.route('/api/gamification/leaderboard', methods=['GET'])
@jwt_required()
def gamification_leaderboard():
    user_id = _to_int_user_id(get_jwt_identity())
    scope = (request.args.get('scope') or 'weekly').strip().lower()
    if scope not in {'weekly', 'city', 'college', 'friends'}:
        scope = 'weekly'
    lb = build_leaderboard_for_scope(user_id, scope=scope, limit=15)
    return jsonify({'scope': scope, 'items': lb['items'], 'meta': lb['meta']})


@app.route('/api/gamification/missions/progress', methods=['POST'])
@jwt_required()
def update_mission_progress():
    user_id = _to_int_user_id(get_jwt_identity())
    data = request.get_json() or {}
    mission_id = data.get('mission_id')
    delta = int(data.get('delta', 1) or 1)
    mission = UserMission.query.filter_by(id=mission_id, user_id=user_id).first()
    if not mission:
        return jsonify({'error': 'Mission not found'}), 404
    if mission.is_claimed:
        return jsonify({'error': 'Mission already claimed'}), 400

    mission.current_count = min(mission.target_count, max(0, mission.current_count + delta))
    db.session.commit()
    return jsonify({
        'success': True,
        'mission_id': mission.id,
        'current_count': mission.current_count,
        'target_count': mission.target_count,
        'is_complete': mission.current_count >= mission.target_count
    })


@app.route('/api/gamification/referral', methods=['GET'])
@jwt_required()
def get_referral_info():
    user_id = _to_int_user_id(get_jwt_identity())
    profile = get_or_create_gamification_profile(user_id)
    db.session.commit()
    return jsonify({'success': True, 'referral_code': profile.referral_code, 'referred_by': profile.referred_by})


@app.route('/api/gamification/referral/apply', methods=['POST'])
@jwt_required()
def apply_referral_code():
    user_id = _to_int_user_id(get_jwt_identity())
    data = request.get_json() or {}
    code = (data.get('code') or '').strip().upper()
    if not code:
        return jsonify({'error': 'Referral code required'}), 400

    my_profile = get_or_create_gamification_profile(user_id)
    if my_profile.referral_code == code:
        return jsonify({'error': 'You cannot use your own code'}), 400
    if my_profile.referred_by:
        return jsonify({'error': 'Referral already applied'}), 400

    referrer = GamificationProfile.query.filter(func.upper(GamificationProfile.referral_code) == code).first()
    if not referrer:
        return jsonify({'error': 'Invalid referral code'}), 404

    my_profile.referred_by = code
    # Reward both users via existing event engine.
    award_event(referrer.user_id, 'referral_friend', event_ref=user_id, meta={'type': 'referrer'})
    award_event(user_id, 'referral_friend', event_ref=referrer.user_id, meta={'type': 'referred_user'})
    db.session.commit()
    return jsonify({'success': True, 'message': 'Referral applied and rewards granted'})


@app.route('/api/gamification/missions/claim', methods=['POST'])
@jwt_required()
def claim_mission():
    user_id = _to_int_user_id(get_jwt_identity())
    data = request.get_json() or {}
    mission_id = data.get('mission_id')
    mission = UserMission.query.filter_by(id=mission_id, user_id=user_id).first()
    if not mission:
        return jsonify({'error': 'Mission not found'}), 404
    if mission.is_claimed:
        return jsonify({'error': 'Mission already claimed'}), 400
    if mission.current_count < mission.target_count:
        return jsonify({'error': 'Mission not complete yet'}), 400

    profile = get_or_create_gamification_profile(user_id)
    profile.yc_balance += int(mission.reward_coins)
    profile.yc_lifetime_earned += int(mission.reward_coins)
    profile.xp_total += int(mission.reward_xp)
    level_name, _, _ = level_from_xp(profile.xp_total)
    profile.current_level = level_name
    mission.is_claimed = True

    db.session.add(GamificationEvent(
        user_id=user_id,
        event_type='mission_claim',
        event_ref=mission.mission_key,
        coins_delta=int(mission.reward_coins),
        xp_delta=int(mission.reward_xp),
        meta_json=json.dumps({'mission': mission.title})
    ))
    db.session.commit()
    return jsonify({'success': True, 'coins': mission.reward_coins, 'xp': mission.reward_xp, 'message': 'Mission reward claimed'})


@app.route('/api/gamification/redeem', methods=['POST'])
@jwt_required()
def redeem_reward():
    user_id = _to_int_user_id(get_jwt_identity())
    data = request.get_json() or {}
    reward_key = data.get('reward_key')
    reward = next((r for r in STORE_REWARDS if r['key'] == reward_key), None)
    if not reward:
        return jsonify({'error': 'Reward not found'}), 404

    profile = get_or_create_gamification_profile(user_id)
    if profile.yc_balance < reward['cost']:
        return jsonify({'error': 'Insufficient Yatrika Coins'}), 400

    profile.yc_balance -= int(reward['cost'])
    profile.yc_lifetime_spent += int(reward['cost'])
    voucher_code = f"YC-{reward['key'].upper()}-{uuid.uuid4().hex[:8].upper()}"

    red = RewardRedemption(
        user_id=user_id,
        reward_key=reward['key'],
        reward_title=reward['title'],
        coins_spent=reward['cost'],
        voucher_code=voucher_code,
        status='active'
    )
    db.session.add(red)
    db.session.add(GamificationEvent(
        user_id=user_id,
        event_type='reward_redemption',
        event_ref=reward['key'],
        coins_delta=-int(reward['cost']),
        xp_delta=0,
        meta_json=json.dumps({'voucher_code': voucher_code, 'reward': reward['title']})
    ))
    db.session.commit()
    return jsonify({'success': True, 'voucher_code': voucher_code, 'reward': reward['title'], 'cost': reward['cost']})


@app.route('/api/gamification/event', methods=['POST'])
@jwt_required()
def gamification_event_api():
    user_id = _to_int_user_id(get_jwt_identity())
    data = request.get_json() or {}
    event_type = data.get('event_type')
    event_ref = data.get('event_ref')
    meta = data.get('meta', {})
    if event_type not in EVENT_REWARDS:
        return jsonify({'error': 'Unsupported event_type'}), 400

    result = award_event(user_id, event_type, event_ref=event_ref, meta=meta)
    db.session.commit()
    return jsonify({'success': True, **result})

# ---------- Socket.IO Events ----------
online_users = {}

@socketio.on('join')
def handle_join(data):
    from flask_socketio import emit, request
    sid = request.sid
    online_users[sid] = {
        'user_id': data.get('user_id'),
        'username': data.get('username'),
        'lat': data.get('lat'),
        'lng': data.get('lng')
    }
    emit('online_users', [{'username': u['username'], 'lat': u['lat'], 'lng': u['lng']} for u in online_users.values() if u.get('username')], broadcast=True)

@socketio.on('update_companion_location')
def handle_companion_location(data):
    from flask_socketio import emit, request
    token = data.get('token')
    if not token:
        return
    try:
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        user_id = decoded['sub']
        user = User.query.get(user_id)
        profile = CompanionProfile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.latitude = data.get('lat')
            profile.longitude = data.get('lng')
            profile.last_seen = datetime.utcnow()
            db.session.commit()
            emit('companion_moved', {
                'user_id': user_id,
                'username': user.username,
                'lat': data.get('lat'),
                'lng': data.get('lng')
            }, broadcast=True, include_self=False)
    except Exception as e:
        print(f"Socket error: {e}")

@socketio.on('sos_alert')
def handle_sos(data):
    from flask_socketio import emit
    emit('emergency_alert', {'location': data.get('location'), 'timestamp': datetime.now().isoformat()}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    from flask_socketio import emit, request
    sid = request.sid
    if sid in online_users:
        del online_users[sid]
        emit('user_left', {'sid': sid}, broadcast=True)

# ---------- Error Handlers ----------
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created/verified successfully")
        print("🚀 Server starting at http://127.0.0.1:5000")
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
