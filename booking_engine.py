# booking_engine.py
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ---------- Mock Data ----------
AIRLINES = [
    "IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air", "Go First",
    "Emirates", "Qatar Airways", "Etihad", "Turkish Airlines", "Lufthansa",
    "Singapore Airlines", "British Airways", "Air France", "KLM", "ANA"
]
TRAIN_OPERATORS = [
    "Indian Railways", "IRCTC", "Rajdhani", "Shatabdi", "Duronto", "Vande Bharat",
    "Tejas", "Garib Rath", "Humsafar"
]
HOTEL_CHAINS = [
    "Taj", "Oberoi", "ITC", "Marriott", "Hilton", "Hyatt", "Leela", "Accor",
    "Radisson", "JW Marriott", "The Lalit", "Novotel", "Holiday Inn", "Sheraton"
]
CAB_COMPANIES = ["Uber", "Ola", "Mega Cabs", "Meru", "FastTrack", "BluSmart", "Rapido", "Savaari"]
CRUISE_LINES = ["Carnival", "Royal Caribbean", "Norwegian", "MSC", "Costa", "Princess", "Celebrity"]

FLIGHT_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Goa", "Jaipur",
    "Lucknow", "Chandigarh", "Kochi", "Varanasi", "Srinagar", "Indore", "Bhubaneswar", "Nagpur", "Surat", "Amritsar",
    "Dubai", "Singapore", "Bangkok", "London", "Paris", "New York", "Tokyo", "Sydney", "Toronto", "Istanbul"
]
TRAIN_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Chandigarh", "Bhopal", "Patna", "Nagpur", "Indore", "Varanasi", "Kochi", "Amritsar"
]
HOTEL_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Goa", "Jaipur",
    "Lucknow", "Chandigarh", "Kochi", "Varanasi", "Srinagar", "Indore", "Bhubaneswar", "Nagpur", "Surat", "Amritsar",
    "Dubai", "Singapore", "Bangkok", "London", "Paris", "New York", "Tokyo", "Sydney", "Toronto", "Istanbul",
    "Rome", "Barcelona", "Amsterdam", "Zurich", "Berlin", "Vienna", "Prague", "Seoul", "Kuala Lumpur", "Cape Town"
]
CAB_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Goa", "Jaipur",
    "Lucknow", "Chandigarh", "Kochi", "Varanasi", "Srinagar", "Indore", "Bhubaneswar", "Nagpur", "Surat", "Amritsar"
]
CRUISE_ROUTES = [
    "Mumbai-Goa", "Mumbai-Kochi", "Kochi-Maldives", "Chennai-Singapore", "Mumbai-Dubai", "Goa-Lakshadweep",
    "Singapore-Phuket", "Dubai-Abu Dhabi", "Barcelona-Rome", "Athens-Santorini", "Miami-Bahamas", "Seattle-Alaska",
    "Sydney-Auckland", "Hong Kong-Ha Long Bay", "Istanbul-Greek Isles", "Cape Town-Walvis Bay"
]

# Backward compatibility alias used by other modules.
CITIES = FLIGHT_CITIES

# In-memory storage for bookings (simulate database)
bookings_db = {}
booking_counter = 1000

# Availability pools (simulate real-time inventory)
flight_inventory = {}
train_inventory = {}
hotel_inventory = {}
cab_inventory = {}
cruise_inventory = {}

def init_inventory():
    """Initialize mock availability for next 30 days"""
    today = datetime.now().date()
    for i in range(30):
        date = today + timedelta(days=i)
        date_str = date.isoformat()
        # Flights: each route has 5-10 flights with 50-200 seats
        for origin in FLIGHT_CITIES:
            for dest in FLIGHT_CITIES:
                if origin != dest:
                    key = f"{origin}|{dest}|{date_str}"
                    flight_inventory[key] = {
                        'flights': [],
                        'booked': 0
                    }
                    for _ in range(random.randint(5, 10)):
                        flight = {
                            'flight_number': f"{random.choice(['6E','AI','SG','UK','QP'])}{random.randint(100,999)}",
                            'airline': random.choice(AIRLINES),
                            'departure_time': f"{random.randint(5,22):02d}:{random.randint(0,59):02d}",
                            'arrival_time': f"{random.randint(6,23):02d}:{random.randint(0,59):02d}",
                            'duration': random.randint(60, 240),
                            'price': random.randint(2500, 12000),
                            'seats': random.randint(50, 200)
                        }
                        flight_inventory[key]['flights'].append(flight)
        # Trains
        for origin in TRAIN_CITIES:
            for dest in TRAIN_CITIES:
                if origin != dest:
                    key = f"{origin}|{dest}|{date_str}"
                    train_inventory[key] = {
                        'trains': [],
                        'booked': 0
                    }
                    for _ in range(random.randint(3, 8)):
                        train = {
                            'train_number': f"{random.randint(10000, 99999)}",
                            'train_name': random.choice(TRAIN_OPERATORS) + " Express",
                            'departure_time': f"{random.randint(5,22):02d}:{random.randint(0,59):02d}",
                            'arrival_time': f"{random.randint(6,23):02d}:{random.randint(0,59):02d}",
                            'duration': random.randint(180, 720),
                            'price': random.randint(300, 3000),
                            'seats': random.randint(100, 500)
                        }
                        train_inventory[key]['trains'].append(train)
        # Hotels
        for city in HOTEL_CITIES:
            key = f"{city}|{date_str}"
            hotel_inventory[key] = {
                'hotels': [],
                'booked': 0
            }
            for _ in range(random.randint(10, 20)):
                hotel = {
                    'name': random.choice(HOTEL_CHAINS) + " " + random.choice(["Palace", "Resort", "Grand", "Inn", "Suites"]),
                    'room_type': random.choice(["Standard", "Deluxe", "Suite", "Executive"]),
                    'price_per_night': random.randint(2000, 25000),
                    'available_rooms': random.randint(10, 100),
                    'rating': round(random.uniform(3.5, 5.0), 1)
                }
                hotel_inventory[key]['hotels'].append(hotel)
        # Cabs
        for city in CAB_CITIES:
            key = f"{city}|{date_str}"
            cab_inventory[key] = {
                'cabs': [],
                'booked': 0
            }
            for _ in range(random.randint(20, 50)):
                cab = {
                    'type': random.choice(["Micro", "Mini", "Sedan", "SUV", "Luxury"]),
                    'company': random.choice(CAB_COMPANIES),
                    'price_km': random.randint(8, 25),
                    'base_fare': random.randint(50, 150),
                    'available': random.randint(5, 30)
                }
                cab_inventory[key]['cabs'].append(cab)
        # Cruises
        for route in CRUISE_ROUTES:
            key = f"{route}|{date_str}"
            cruise_inventory[key] = {
                'cruises': [],
                'booked': 0
            }
            for _ in range(random.randint(1, 3)):
                cruise = {
                    'name': random.choice(CRUISE_LINES) + " " + random.choice(["Dream", "Explorer", "Adventure", "Princess"]),
                    'duration_days': random.choice([3, 5, 7, 10]),
                    'price': random.randint(15000, 150000),
                    'cabins': random.randint(50, 300),
                    'departure_time': "18:00",
                    'arrival_time': "08:00"
                }
                cruise_inventory[key]['cruises'].append(cruise)

# Initialize inventory on module load
init_inventory()

def generate_booking_id():
    global booking_counter
    booking_counter += 1
    return f"BK{booking_counter}"

def search_flights(origin: str, destination: str, date: str) -> List[Dict]:
    key = f"{origin}|{destination}|{date}"
    data = flight_inventory.get(key, {})
    flights = data.get('flights', [])
    # Apply dynamic pricing based on demand
    booked = data.get('booked', 0)
    total_seats = sum(f['seats'] for f in flights)
    if total_seats > 0:
        demand_factor = booked / total_seats
        for f in flights:
            base_price = f['price']
            f['price'] = int(base_price * (1 + demand_factor * 0.5))
            f['available_seats'] = max(0, f['seats'] - int(booked / max(1, len(flights))))
    return flights

def search_trains(origin: str, destination: str, date: str) -> List[Dict]:
    key = f"{origin}|{destination}|{date}"
    data = train_inventory.get(key, {})
    trains = data.get('trains', [])
    booked = data.get('booked', 0)
    for t in trains:
        t['available_seats'] = max(0, t['seats'] - int(booked / max(1, len(trains))))
    return trains

def search_hotels(city: str, check_in: str, check_out: str, guests: int) -> List[Dict]:
    # For hotels, we need to check multiple dates
    start = datetime.strptime(check_in, '%Y-%m-%d')
    end = datetime.strptime(check_out, '%Y-%m-%d')
    nights = (end - start).days
    if nights <= 0:
        return []
    # Sample availability from check-in date inventory (simplified)
    key = f"{city}|{check_in}"
    data = hotel_inventory.get(key, {})
    hotels = data.get('hotels', [])
    for h in hotels:
        h['total_price'] = h['price_per_night'] * nights
        h['nights'] = nights
        h['available_rooms'] = max(0, h['available_rooms'] - data.get('booked', 0))
    return hotels

def search_cabs(city: str, date: str) -> List[Dict]:
    key = f"{city}|{date}"
    data = cab_inventory.get(key, {})
    cabs = data.get('cabs', [])
    for c in cabs:
        c['available'] = max(0, c['available'] - data.get('booked', 0))
    return cabs

def search_cruises(route: str, date: str) -> List[Dict]:
    key = f"{route}|{date}"
    data = cruise_inventory.get(key, {})
    cruises = data.get('cruises', [])
    for c in cruises:
        c['available_cabins'] = max(0, c['cabins'] - data.get('booked', 0))
    return cruises

def create_booking(booking_type: str, details: Dict) -> Dict:
    booking_id = generate_booking_id()
    booking = {
        'booking_id': booking_id,
        'type': booking_type,
        'status': 'confirmed',
        'created_at': datetime.now().isoformat(),
        'details': details
    }
    bookings_db[booking_id] = booking
    
    # Update inventory (reduce availability)
    if booking_type == 'flight':
        key = f"{details['origin']}|{details['destination']}|{details['date']}"
        if key in flight_inventory:
            flight_inventory[key]['booked'] += details.get('passengers', 1)
    elif booking_type == 'train':
        key = f"{details['origin']}|{details['destination']}|{details['date']}"
        if key in train_inventory:
            train_inventory[key]['booked'] += details.get('passengers', 1)
    elif booking_type == 'hotel':
        key = f"{details['city']}|{details['check_in']}"
        if key in hotel_inventory:
            hotel_inventory[key]['booked'] += 1
    elif booking_type == 'cab':
        key = f"{details['city']}|{details['date']}"
        if key in cab_inventory:
            cab_inventory[key]['booked'] += 1
    elif booking_type == 'cruise':
        key = f"{details['route']}|{details['date']}"
        if key in cruise_inventory:
            cruise_inventory[key]['booked'] += 1
    
    return booking

def get_booking(booking_id: str) -> Optional[Dict]:
    return bookings_db.get(booking_id)

def cancel_booking(booking_id: str) -> bool:
    if booking_id in bookings_db:
        booking = bookings_db[booking_id]
        # Refund logic (mock)
        booking['status'] = 'cancelled'
        bookings_db[booking_id] = booking
        # Optionally release inventory (not implemented for simplicity)
        return True
    return False

def get_live_status(booking_id: str) -> Dict:
    booking = bookings_db.get(booking_id)
    if not booking:
        return {'error': 'Booking not found'}
    
    status = {
        'booking_id': booking_id,
        'type': booking['type'],
        'status': booking['status'],
        'last_updated': datetime.now().isoformat()
    }
    
    # Simulate real-time status updates
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
    
    return status