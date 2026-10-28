import requests
import random
import os
import math
import time
from flask import current_app
from datetime import datetime
from werkzeug.utils import secure_filename

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    print("✅ Gemini AI loaded successfully")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Google Generative AI not installed. Run: pip install google-generativeai")

# ==================== Payment Functions ====================

def create_razorpay_order(amount):
    """Create a mock order for testing (no real Razorpay)"""
    print(f"⚠️ Creating mock order for amount: ₹{amount}")
    return {
        'id': f'mock_order_{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'amount': int(amount * 100),
        'currency': 'INR',
        'status': 'created'
    }

# ==================== Weather Functions ====================

def get_weather(city):
    """Fetch weather from OpenWeather API or return mock data"""
    api_key = current_app.config.get('WEATHER_API_KEY')
    
    if api_key:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get('cod') == 200:
                return {
                    'temp': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon']
                }
        except Exception as e:
            print(f"❌ Weather API error: {e}")
    
    # Return mock weather data
    weather_conditions = ['Sunny', 'Partly Cloudy', 'Clear Sky', 'Light Breeze', 'Cloudy']
    return {
        'temp': random.randint(20, 35),
        'feels_like': random.randint(18, 33),
        'humidity': random.randint(40, 80),
        'description': random.choice(weather_conditions),
        'icon': '01d'
    }

# ==================== Crowd Density Functions ====================

def get_crowd_density(lat, lng):
    """Mock crowd density prediction based on time and location"""
    hour = datetime.now().hour

    if 10 <= hour <= 18:
        density = random.choice(['high', 'medium', 'low'])
    else:
        density = random.choice(['medium', 'low'])

    wait_time = random.randint(0, 45) if density == 'high' else random.randint(0, 15)

    place_info = reverse_geocode_osm(lat, lng)
    place_type = get_place_type_from_name(place_info)

    if place_type == 'shopping_mall' and 10 <= hour <= 20:
        density = 'high'
        wait_time = random.randint(20, 60)
    elif place_type == 'restaurant' and (12 <= hour <= 14 or 19 <= hour <= 22):
        density = 'high'
        wait_time = random.randint(15, 45)

    return {
        'density': density,
        'wait_time': wait_time,
        'best_time': get_best_time(place_type),
        'place_type': place_type
    }

def get_place_type_from_name(place_name):
    """Simple place type detection from name"""
    place_name_lower = place_name.lower()

    if any(word in place_name_lower for word in ['mall', 'shopping', 'market']):
        return 'shopping_mall'
    elif any(word in place_name_lower for word in ['restaurant', 'cafe', 'food', 'dining']):
        return 'restaurant'
    elif any(word in place_name_lower for word in ['museum', 'gallery', 'exhibition']):
        return 'museum'
    elif any(word in place_name_lower for word in ['park', 'garden', 'zoo']):
        return 'park'
    else:
        return 'tourist_attraction'

def get_best_time(place_type):
    """Return best time to visit based on place type"""
    times = {
        'shopping_mall': 'Weekday mornings (10 AM - 12 PM)',
        'restaurant': 'Early lunch (11:30 AM) or late dinner (8:30 PM)',
        'museum': 'Tuesday - Thursday mornings',
        'park': 'Early morning (7 AM - 9 AM)',
        'tourist_attraction': 'Early morning (8 AM - 10 AM)'
    }
    return times.get(place_type, 'Early morning (8 AM - 10 AM)')

# ==================== OpenStreetMap Functions ====================

def geocode_osm(place_name):
    """Free geocoding using OpenStreetMap Nominatim"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': place_name,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'YATRIKA-TravelApp/1.0'}

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()

        if data:
            return {
                'lat': float(data[0]['lat']),
                'lng': float(data[0]['lon']),
                'display_name': data[0]['display_name'],
                'type': data[0].get('type', 'attraction')
            }
        return None
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return None

def reverse_geocode_osm(lat, lng):
    """Reverse geocoding using OpenStreetMap Nominatim"""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'zoom': 18,
            'addressdetails': 1
        }
        headers = {'User-Agent': 'YATRIKA-TravelApp/1.0'}

        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        return data.get('display_name', 'Unknown location')
    except Exception as e:
        print(f"❌ Reverse geocoding error: {e}")
        return "Unknown location"

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(min(1, math.sqrt(a)))
    return R * c

# Lightweight in-memory cache to reduce repeated Overpass requests from frequent map moves.
_nearby_cache = {}


def search_nearby_osm(lat, lng, radius=1000, category='all'):
    """Search nearby places using OpenStreetMap Overpass API"""
    try:
        cache_key = f"{round(float(lat), 4)}|{round(float(lng), 4)}|{int(radius)}|{category}"
        now = time.time()
        cached = _nearby_cache.get(cache_key)
        if cached and (now - cached['ts'] < 120):
            return cached['data']

        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Category to OSM tag mapping
        categories = {
            'food': '["amenity"~"restaurant|cafe|fast_food|bar|pub"]',
            'tourism': '["tourism"~"attraction|museum|gallery|viewpoint|zoo"]',
            'shopping': '["shop"~"mall|supermarket|clothes|electronics"]',
            'emergency': '["amenity"~"hospital|clinic|police|fire_station"]',
            'parking': '["amenity"~"parking"]',
            'all': '["tourism"|"amenity"|"shop"]'
        }
        
        query_filter = categories.get(category, categories['all'])

        query = f"""
        [out:json][timeout:7];
        (
          node{query_filter}(around:{radius},{lat},{lng});
          way{query_filter}(around:{radius},{lat},{lng});
          rel{query_filter}(around:{radius},{lat},{lng});
        );
        out center 20;
        """

        resp = requests.get(overpass_url, params={'data': query}, timeout=7)
        data = resp.json()
        
        results = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', '')
            
            if not name or len(name) < 3:
                continue
                
            if 'lat' in element:
                place_lat = element['lat']
                place_lng = element['lon']
            elif 'center' in element:
                place_lat = element['center']['lat']
                place_lng = element['center']['lon']
            else:
                continue
            
            distance = calculate_distance(lat, lng, place_lat, place_lng)
            
            place_type = tags.get('tourism') or tags.get('amenity') or tags.get('shop') or 'place'
            
            results.append({
                'id': element.get('id'),
                'name': name,
                'type': place_type,
                'lat': place_lat,
                'lon': place_lng,
                'distance': round(distance, 1),
                'tags': tags
            })
        
        results.sort(key=lambda x: x['distance'])
        trimmed = results[:50]
        _nearby_cache[cache_key] = {'ts': now, 'data': trimmed}
        return trimmed
        
    except Exception as e:
        print(f"❌ OSM search error: {e}")
        return []

def get_route_osm(start_lat, start_lng, end_lat, end_lng, mode='driving'):
    """Get route using OSRM"""
    try:
        profile = 'driving' if mode == 'driving' else 'walking' if mode == 'walking' else 'cycling'
        url = f"http://router.project-osrm.org/route/v1/{profile}/{start_lng},{start_lat};{end_lng},{end_lat}"
        params = {'overview': 'full', 'geometries': 'geojson'}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('code') == 'Ok':
            route = data['routes'][0]
            distance = route['distance'] / 1000
            duration = route['duration'] / 60
            geometry = route['geometry']['coordinates']
            polyline = [[coord[1], coord[0]] for coord in geometry]
            
            return {
                'distance': f"{distance:.1f} km",
                'duration': f"{duration:.0f} mins",
                'steps': [],
                'geometry': polyline
            }
        return None
    except Exception as e:
        print(f"❌ Route API error: {e}")
        return get_mock_route(start_lat, start_lng, end_lat, end_lng, mode)

def get_mock_route(start_lat, start_lng, end_lat, end_lng, mode='driving'):
    """Mock route data when API fails"""
    distance = calculate_distance(start_lat, start_lng, end_lat, end_lng)
    speeds = {'driving': 50, 'walking': 5, 'cycling': 15}
    speed = speeds.get(mode, 30)
    duration = (distance / speed) * 60
    
    return {
        'distance': f"{distance:.1f} km",
        'duration': f"{duration:.0f} mins",
        'steps': []
    }

# ==================== AI Itinerary Functions (Gemini) ====================

def generate_ai_itinerary(destination, days, budget, preferences=''):
    """Generate AI-powered itinerary using Gemini"""
    print(f"🚀 Generating AI itinerary for {destination}")
    
    if not GEMINI_AVAILABLE:
        print("⚠️ Gemini not available, using fallback")
        return generate_fallback_itinerary(destination, days, budget)

    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            print("⚠️ No Gemini API key, using fallback")
            return generate_fallback_itinerary(destination, days, budget)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
You are a professional travel planner. Create a detailed {days}-day itinerary for **{destination}** with a budget of ${budget} USD.
Preferences: {preferences if preferences else 'balanced mix of activities'}.

**IMPORTANT – Use REAL names of attractions, restaurants, and districts.**

Create a JSON response with this exact structure:
{{
  "destination": "{destination}",
  "days": {days},
  "total_estimated_cost": {budget},
  "currency": "USD",
  "itinerary": [
    {{
      "day": 1,
      "activities": [
        {{"time": "09:00 AM", "name": "Activity name", "duration": "2 hours", "cost": 50, "description": "Description"}},
        {{"time": "12:30 PM", "name": "Lunch", "duration": "1 hour", "cost": 20, "description": "Restaurant name"}},
        {{"time": "02:00 PM", "name": "Afternoon activity", "duration": "3 hours", "cost": 30, "description": "Description"}},
        {{"time": "07:00 PM", "name": "Dinner", "duration": "1.5 hours", "cost": 40, "description": "Restaurant name"}}
      ]
    }}
  ],
  "travel_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "best_time_to_visit": "Best season",
  "local_cuisine": ["Dish 1", "Dish 2"]
}}

Return ONLY valid JSON, no markdown formatting.
"""

        response = model.generate_content(prompt)
        import json
        try:
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            return json.loads(result_text)
        except:
            return response.text

    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return generate_fallback_itinerary(destination, days, budget)

def generate_fallback_itinerary(destination, days, budget):
    """Generate detailed fallback itinerary with real place names from database"""
    popular_places = get_popular_places(destination)
    
    itinerary = f"✨ **AI-Powered Itinerary for {destination}** ✨\n\n"
    itinerary += f"💰 **Budget:** ${budget} USD\n"
    itinerary += f"📅 **Duration:** {days} days\n\n"
    
    landmarks = get_famous_landmarks(destination)
    restaurants = get_famous_restaurants(destination)
    
    for day in range(1, days + 1):
        itinerary += f"**Day {day}**\n"
        landmark_index = (day - 1) % len(landmarks)
        itinerary += f"🌅 **Morning (9:00 AM - 12:00 PM):** {landmarks[landmark_index]} - Visit this iconic landmark. Cost: $20-40\n"
        
        if day + 2 < len(popular_places):
            place = popular_places[day + 1]
            itinerary += f"🍽️ **Afternoon (12:30 PM - 5:00 PM):** {place} - Explore and enjoy local cuisine. Cost: $25-50\n"
        else:
            itinerary += f"🍽️ **Afternoon (12:30 PM - 5:00 PM):** Explore {destination}'s historic district and local markets. Cost: $20-45\n"
        
        restaurant_index = (day - 1) % len(restaurants)
        itinerary += f"🎨 **Evening (6:00 PM - 9:00 PM):** Dinner at {restaurants[restaurant_index]} - Experience authentic {destination} cuisine. Cost: $30-60\n"
        itinerary += f"🌙 **Night (after 9:00 PM):** Enjoy {destination}'s nightlife at a local bar or take a scenic night walk. Cost: $15-35\n\n"
    
    itinerary += f"**🌟 Travel Tips for {destination}:**\n"
    itinerary += get_travel_tips(destination)
    
    return itinerary

def get_famous_landmarks(destination):
    landmarks_db = {
        'paris': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame Cathedral'],
        'london': ['Big Ben', 'Tower of London', 'Buckingham Palace'],
        'new york': ['Statue of Liberty', 'Empire State Building', 'Times Square'],
        'tokyo': ['Tokyo Tower', 'Senso-ji Temple', 'Shibuya Crossing'],
        'dubai': ['Burj Khalifa', 'Palm Jumeirah', 'Burj Al Arab'],
        'rome': ['Colosseum', 'Vatican City', 'Trevi Fountain'],
        'mumbai': ['Gateway of India', 'Marine Drive', 'Elephanta Caves'],
        'delhi': ['India Gate', 'Red Fort', 'Qutub Minar'],
        'jaipur': ['Hawa Mahal', 'Amber Fort', 'City Palace'],
        'agra': ['Taj Mahal', 'Agra Fort', 'Fatehpur Sikri']
    }
    dest_lower = destination.lower()
    if dest_lower in landmarks_db:
        return landmarks_db[dest_lower]
    return [f"Main Square of {destination}", f"{destination} Cathedral", f"Historic District of {destination}"]

def get_famous_restaurants(destination):
    restaurants_db = {
        'paris': ['Le Jules Verne', 'Café de Flore', 'Le Comptoir du Relais'],
        'london': ['Dishoom', 'The Ledbury', 'Sketch'],
        'new york': ["Katz's Delicatessen", 'Peter Luger Steak House', 'Le Bernardin'],
        'tokyo': ['Sukiyabashi Jiro', 'Ichiran Ramen', 'Gonpachi Nishiazabu'],
        'dubai': ['At.mosphere', 'Al Mahara', 'Pierchic'],
        'rome': ['Roscioli', 'La Pergola', 'Armando al Pantheon'],
        'mumbai': ['Leopold Cafe', 'Britannia & Co.', 'Bademiya'],
        'delhi': ["Karim's", 'Bukhara', 'Indian Accent'],
        'jaipur': ['Chokhi Dhani', 'Surya Mahal', 'Peacock Rooftop'],
        'agra': ['Pinch of Spice', "Joney's Place", 'Dasaprakash']
    }
    dest_lower = destination.lower()
    if dest_lower in restaurants_db:
        return restaurants_db[dest_lower]
    return [f"Local Restaurant in {destination}", f"{destination} Bistro", f"Traditional {destination} Cuisine"]

def get_travel_tips(destination):
    return """• **Best Time to Visit:** Early morning (8-10 AM) for popular attractions to avoid crowds
• **Transportation:** Use public transport or ride-sharing apps for convenient travel
• **Local Currency:** Carry some cash for small purchases and markets
• **Language:** Learn a few basic phrases in the local language
• **Safety:** Keep valuables secure and be aware of your surroundings
• **Book in Advance:** Popular attractions and restaurants often need reservations"""

def get_popular_places(destination):
    places_database = {
        'paris': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame Cathedral', 'Montmartre', 'Arc de Triomphe'],
        'london': ['Big Ben', 'London Eye', 'Tower of London', 'Buckingham Palace', 'British Museum'],
        'new york': ['Statue of Liberty', 'Times Square', 'Central Park', 'Empire State Building', 'Brooklyn Bridge'],
        'tokyo': ['Tokyo Tower', 'Shibuya Crossing', 'Senso-ji Temple', 'Meiji Shrine', 'Shinjuku Gyoen'],
        'dubai': ['Burj Khalifa', 'Dubai Mall', 'Palm Jumeirah', 'Dubai Marina', 'Burj Al Arab'],
        'rome': ['Colosseum', 'Vatican City', 'Trevi Fountain', 'Roman Forum', 'Pantheon'],
        'mumbai': ['Gateway of India', 'Marine Drive', 'Elephanta Caves', 'Juhu Beach', 'Colaba Causeway'],
        'delhi': ['India Gate', 'Red Fort', 'Qutub Minar', "Humayun's Tomb", 'Lotus Temple'],
        'jaipur': ['Hawa Mahal', 'Amber Fort', 'City Palace', 'Jantar Mantar', 'Jal Mahal'],
        'agra': ['Taj Mahal', 'Agra Fort', 'Fatehpur Sikri', 'Mehtab Bagh', 'Itmad-ud-Daulah']
    }
    dest_lower = destination.lower()
    if dest_lower in places_database:
        return places_database[dest_lower]
    return [f"Main Square of {destination}", f"{destination} City Museum", f"Historic District of {destination}"]

# ==================== Simple Itinerary Generator ====================

def suggest_itinerary(destination, days, budget):
    """Simple itinerary generator for quick planning"""
    itinerary = []
    activities = [
        f"🏛️ Visit {destination}'s main landmarks and historical sites",
        "🍜 Try local cuisine at authentic restaurants and street food stalls",
        "🏺 Explore cultural sites, museums, and art galleries",
        "🌳 Relax and enjoy the scenic beauty and natural attractions",
        "🛍️ Shop at local markets for unique souvenirs and gifts",
        "📸 Take a guided city tour to discover hidden gems"
    ]
    for day in range(1, days + 1):
        activity = activities[(day - 1) % len(activities)]
        itinerary.append(f"**Day {day}:** {activity}")
    return itinerary

# ==================== File Upload Functions ====================

def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None

# ==================== Helper Functions ====================

def get_client_ip(request):
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    return ip

def format_price(price):
    """Format price with currency symbol"""
    return f"₹{price:,.2f}" if price else "Free"

def get_time_of_day():
    """Get current time of day"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

def get_season():
    """Get current season"""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"