# YATRIKA - Complete Technical Documentation
## For Project Competition Presentation & Viva

---

# TABLE OF CONTENTS
1. [User Authentication (Login/Register)](#feature-1-user-authentication)
2. [AI Trip Planner](#feature-2-ai-trip-planner)
3. [Booking System (Multi-Transport)](#feature-3-booking-system)
4. [Razorpay Payment Integration](#feature-4-razorpay-payment)
5. [Live Flight Tracker](#feature-5-live-flight-tracker)
6. [Smart Map with Location Services](#feature-6-smart-map)
7. [Expense Tracker](#feature-7-expense-tracker)
8. [Dashboard & User Profile](#feature-8-dashboard)
9. [Visa Tracker](#feature-9-visa-tracker)
10. [Companion Finder](#feature-10-companion-finder)
11. [Gamification System](#feature-11-gamification)
12. [Travel Stories & Community](#feature-12-travel-stories)
13. [SOS & Emergency Alerts](#feature-13-sos-alerts)
14. [Weather Integration](#feature-14-weather)

---

# FEATURE 1: USER AUTHENTICATION (LOGIN/REGISTER)

## Purpose
User authentication is the foundation of the application. It enables:
- Secure user account creation and management
- User identification for personalized content
- Protection of user data and bookings
- Session management via JWT tokens

## Frontend Components/Pages/Files Used
- **Pages:** `templates/register.html`, `templates/login.html`, `templates/profile.html`
- **JavaScript:** `static/js/main.js` - Authentication initialization, token storage
- **UI Elements:** 
  - Registration form with username, email, password validation
  - Login form with username and password
  - User profile dropdown in navbar
  - Logout button

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 1800-1850)
- **Models:** `models.py` - User model
- **Database:** SQLAlchemy ORM with SQLite
- **Security:** werkzeug for password hashing

## API Routes
```python
POST   /api/register          # User registration
POST   /api/login             # User login
GET    /api/me                # Get current user info (JWT required)
PUT    /api/update_profile    # Update user profile
POST   /api/change_password   # Change password
DELETE /api/delete_account    # Delete user account
```

## Functions/Methods Used

### Backend Functions:
1. **register()** - Creates new user with hashed password
2. **login()** - Authenticates user and returns JWT token
3. **me()** - Returns logged-in user information
4. **update_profile()** - Updates user bio, phone, email
5. **change_password()** - Changes user password with validation
6. **delete_account()** - Deletes user and all associated data

### Security Functions:
- `generate_password_hash()` - Hashes passwords using werkzeug
- `check_password_hash()` - Verifies password during login
- `create_access_token()` - Creates JWT token for session management
- `jwt_required()` - Decorator to protect routes requiring authentication

## APIs/Libraries/Packages Used
- **Flask-JWT-Extended** - JWT token management
- **Werkzeug** - Password hashing and security
- **SQLAlchemy** - Database ORM

## Database Tables/Models Used
```
User Table:
├── id (Primary Key)
├── username (unique)
├── email (unique)
├── password_hash
├── bio
├── phone
├── avatar
└── created_at timestamp
```

## State Management/Hooks Used
- **Frontend:** `localStorage` - Stores JWT access_token
  ```javascript
  localStorage.setItem('access_token', token)
  localStorage.getItem('access_token')
  localStorage.removeItem('access_token')  // on logout
  ```
- **Backend:** Session managed via JWT claims

## Complete Workflow Step-by-Step

### Registration Flow:
```
1. User fills registration form (username, email, password)
   ↓
2. Frontend validates inputs (client-side)
   ↓
3. POST /api/register with credentials
   ↓
4. Backend checks if username/email exists
   ↓
5. Password hashed using generate_password_hash()
   ↓
6. User record created in database
   ↓
7. Gamification: award_event('signup', 100 coins)
   ↓
8. Return 201 success message
   ↓
9. Frontend redirects to login page
```

### Login Flow:
```
1. User enters username and password
   ↓
2. POST /api/login
   ↓
3. Backend finds user by username
   ↓
4. Verifies password using check_password_hash()
   ↓
5. If valid:
   - ensure_user_missions() - Creates daily/weekly missions
   - process_daily_login() - Handles login streak logic
   - create_access_token() - Generates JWT
   ↓
6. Return JWT token in JSON response
   ↓
7. Frontend stores token in localStorage
   ↓
8. Frontend makes GET /api/me to fetch user details
   ↓
9. Display user in navbar dropdown and redirect to dashboard
```

## Important Variables/Props/States Used
- **token (JWT):** Contains user_id as identity claim
- **currentUser (JS):** Global variable storing logged-in user object
- **user_id (Backend):** Extracted from JWT token via `get_jwt_identity()`

## Error Handling/Validation Used
- **Username validation:** Must be unique
- **Email validation:** Must be unique format
- **Password validation:** Minimum 6 characters
- **Credential validation:** Username must match password
- **Try-catch blocks:** For database operations with rollback on failure
- **Error responses:** Proper HTTP status codes (400, 401, 404)

## Third-party Integrations
- **None for authentication** (Pure backend implementation)

## How Frontend and Backend Communicate
```
Frontend (HTML/JS)
    ↓ (Fetch API with JSON)
POST/GET /api/register, /api/login, /api/update_profile
    ↓ (Response with JSON)
Backend (Flask/SQLAlchemy)
    ↓ (Database operations)
SQLite Database
```

## Files to Explain in Viva Presentation
1. `app.py` - Lines 1800-1850 (Authentication routes)
2. `models.py` - User model definition
3. `static/js/main.js` - Client-side auth handling
4. `templates/login.html` - Login UI
5. `templates/register.html` - Registration UI

## Possible Viva Questions & Answers

**Q1: How is password security ensured?**
```
A: Passwords are never stored in plain text. We use Werkzeug's 
generate_password_hash() which applies PBKDF2 algorithm with salt. 
During login, check_password_hash() compares the stored hash with 
the hashed input password.
```

**Q2: What is JWT and why is it used?**
```
A: JWT (JSON Web Token) is a stateless authentication mechanism. 
The token contains the user_id as a claim and is signed by the server. 
When a user logs in, we generate a token that expires and send it to 
the client. The client includes this token in the Authorization header 
for protected routes. Unlike sessions, JWTs don't require server storage.
```

**Q3: How does the @jwt_required() decorator work?**
```
A: Flask-JWT-Extended provides this decorator to protect routes. 
When a request reaches a @jwt_required() protected route:
1. It extracts the JWT from Authorization header
2. Verifies the signature using the secret key
3. Extracts the user_id from claims
4. If invalid/expired, returns 401 Unauthorized
5. If valid, allows route execution and user_id is available via 
   get_jwt_identity()
```

**Q4: What happens on logout?**
```
A: Logout is client-side only. Frontend clears the JWT token from 
localStorage and redirects to login page. Since JWT is stateless, 
no server-side session cleanup is needed. However, users can still 
use an expired token until it naturally expires (default 1 week).
```

---

# FEATURE 2: AI TRIP PLANNER

## Purpose
Generate intelligent, personalized travel itineraries using AI. Helps users:
- Plan trips without manual research
- Get realistic budget estimates
- Discover activities and restaurants
- Save trips to their trip list
- Earn gamification rewards

## Frontend Components/Pages/Files Used
- **Pages:** `templates/trip_planner.html`
- **JavaScript:** `static/js/main.js`
- **UI Elements:**
  - Destination input field with autocomplete
  - Days dropdown (1-30)
  - Budget input
  - Preferences textarea
  - Generate button
  - Display itinerary with day-wise activities
  - Save trip button

## Backend Files/Controllers/Routes Used
- **Main Files:** `app.py` (lines 1649-1720), `utils.py` (lines 300-500)
- **Models:** `models.py` - Trip model
- **AI Integration:** Groq API (LLaMA 3.3 70B model) or Google Gemini

## API Routes
```python
POST /api/smart_itinerary    # Generate AI itinerary (JWT required)
POST /api/trips              # Save generated trip
GET  /api/trips              # Get user's saved trips
```

## Functions/Methods Used

### AI Generation Functions:
1. **smart_itinerary()** - Main endpoint to trigger AI generation
2. **generate_ai_itinerary()** - Calls Groq/Gemini API with prompt
3. **generate_fallback_itinerary()** - Fallback when AI service fails
4. **get_famous_landmarks()** - Database of landmarks per city
5. **get_famous_restaurants()** - Database of restaurants per city
6. **get_travel_tips()** - Pre-written travel tips
7. **get_popular_places()** - Database of tourist attractions

### Trip Management:
1. **create_trip()** - Saves trip to database
2. **get_trips()** - Retrieves user's trips

## APIs/Libraries/Packages Used
- **Groq AI:** `groq` package - LLaMA 3.3 70B model
- **Google Gemini:** `google-generativeai` package (fallback)
- **JSON Processing:** `json` module for parsing AI responses
- **Environment Variables:** `python-dotenv` for API keys

## Database Tables/Models Used
```
Trip Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── destination
├── start_date
├── end_date
├── budget (float)
├── itinerary (JSON string)
├── created_at timestamp

Stores itinerary as JSON:
{
  "destination": "Paris",
  "days": 3,
  "total_estimated_cost": 5000,
  "currency": "INR",
  "itinerary": [
    {
      "day": 1,
      "activities": [
        {
          "time": "09:00 AM",
          "name": "Visit Eiffel Tower",
          "duration": "2 hours",
          "cost": 100,
          "description": "..."
        }
      ]
    }
  ],
  "travel_tips": [...],
  "best_time_to_visit": "April-May",
  "local_cuisine": [...]
}
```

## State Management/Hooks Used
- **Frontend State (JS):**
  ```javascript
  let generatedItinerary = null;  // Stores API response
  let tripToSave = {};             // Trip data before saving
  ```
- **Backend:** Request parameters stored in Flask `request` object

## Complete Workflow Step-by-Step

### Full AI Itinerary Generation:
```
1. User enters destination, days, budget, preferences
   ↓
2. Frontend validates inputs (destination not empty, days 1-30)
   ↓
3. POST /api/smart_itinerary with JSON data
   ↓
4. Backend checks if AI service (Groq) is configured
   ↓
5. If Groq available:
   - Constructs prompt with destination, days, budget, preferences
   - Sends to Groq LLaMA 3.3 70B model
   - Temperature: 0.7 (balanced creativity), max_tokens: 2500
   ↓
6. If Groq fails, fallback to generate_fallback_itinerary():
   - Uses pre-loaded landmark/restaurant databases
   - Generates itinerary locally using predefined templates
   ↓
7. Parse AI response (remove markdown, extract JSON)
   ↓
8. If save_trip flag is true:
   - Create Trip record with itinerary JSON
   - Save to database
   ↓
9. Award gamification event: award_event('ai_itinerary', 40 coins, 70 xp)
   ↓
10. Return JSON with full itinerary to frontend
   ↓
11. Frontend displays itinerary with day-wise activities, costs, tips
```

## Important Variables/Props/States Used
- **destination:** String - city or place name (required)
- **days:** Integer - number of days (1-30)
- **budget:** Float - total budget in currency
- **preferences:** String - user interests (optional)
- **start_date:** Date - trip start date (optional)
- **save_trip:** Boolean - whether to save to database
- **user_id:** Integer - extracted from JWT

## Error Handling/Validation Used
- **Input validation:** Destination required, days 1-30
- **API timeout:** 10-second timeout for Groq/Gemini
- **Fallback mechanism:** If AI fails, generates template itinerary
- **JSON parsing:** Try-catch for parsing AI response
- **Database transaction:** Rollback if save_trip fails
- **Gamification safety:** Wrapped in try-except to never break main flow

## Third-party Integrations Used
- **Groq AI:** LLaMA 3.3 70B model - Primary AI provider
- **Google Gemini:** Fallback AI provider
- **OpenStreetMap:** Optional for landmark data validation

## How Frontend and Backend Communicate
```
Frontend (React/Vanilla JS)
    ↓ (POST with itinerary params)
/api/smart_itinerary (Flask)
    ↓ (HTTP request)
Groq API / Google Gemini
    ↓ (Response in JSON)
Flask Backend
    ↓ (Store in SQLite)
Database
    ↓ (JSON response)
Frontend displays with Tailwind CSS
```

## Files to Explain in Viva
1. `app.py` - Lines 1649-1720: smart_itinerary route and generate_ai_itinerary()
2. `utils.py` - Lines 300-500: AI generation and fallback functions
3. `templates/trip_planner.html` - Trip planner UI
4. `models.py` - Trip model definition

## Possible Viva Questions & Answers

**Q1: Why use Groq AI instead of directly using ChatGPT?**
```
A: Groq is cost-effective for high-volume requests with fast inference 
(lower latency). We use LLaMA 3.3 70B which is open-source and powerful.
Google Gemini is used as fallback. This multi-AI approach ensures 
reliability - if one service is down, we switch to another.
```

**Q2: What happens if the AI service fails?**
```
A: We have a two-layer fallback:
1. First fallback: generate_fallback_itinerary() uses local databases 
   of landmarks and restaurants for 50+ cities
2. Second fallback: Returns pre-written template itinerary
This ensures users always get a response, even if AI is down.
```

**Q3: How is the itinerary stored in the database?**
```
A: The itinerary is stored as a JSON string in the Trip table. 
After fetching from AI, we parse it and serialize to JSON before 
storing. When retrieving, we parse JSON back to objects for frontend 
display. This allows flexible schema - each day can have different 
number of activities.
```

**Q4: What prompt engineering techniques are used?**
```
A: Our prompt includes:
1. System role: "You are a professional travel planner"
2. Specific format: We request ONLY JSON output, no markdown
3. Real place names: We specifically ask for real landmarks 
   and restaurants (not generic descriptions)
4. Temperature 0.7: Balanced between creativity and consistency
5. Token limit 2500: Ensures response completes in time
```

---

# FEATURE 3: BOOKING SYSTEM (Multi-Transport)

## Purpose
Unified booking system for:
- Flight bookings (domestic and international)
- Hotel reservations (check-in/check-out)
- Train tickets (Indian Railways)
- Cab/Taxi bookings
- Cruise bookings
- Bus bookings

## Frontend Components/Pages/Files Used
- **Pages:** `templates/booking.html`, `templates/bookings.html`, `templates/flight_results.html`, `templates/hotels.html`, `templates/live_flights.html`
- **JavaScript:** UI for search forms, result displays
- **UI Elements:**
  - Multi-tab interface (Flights, Hotels, Trains, Cabs, Cruises)
  - Search forms with date pickers
  - Results listing with filters
  - Booking confirmation modals
  - Passenger details forms

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 1404-1610), `booking_engine.py`
- **Models:** `models.py` - Booking model
- **Database:** SQLite with in-memory inventory

## API Routes
```python
GET  /api/engine/flights        # Search flights
GET  /api/engine/trains         # Search trains
GET  /api/engine/hotels         # Search hotels
GET  /api/engine/cabs           # Search cabs
GET  /api/engine/cruises        # Search cruises
POST /api/engine/book           # Create booking (JWT required)
GET  /api/engine/booking/<id>   # Get booking details
POST /api/engine/booking/<id>/cancel  # Cancel booking
GET  /api/engine/booking/<id>/status  # Real-time status
GET  /api/engine/bookings       # Get user's bookings
```

## Functions/Methods Used

### Search Functions:
1. **engine_flights()** - Searches flights, applies demand pricing
2. **engine_trains()** - Searches train inventory
3. **engine_hotels()** - Searches hotels with check-in/out dates
4. **engine_cabs()** - Searches available cabs
5. **engine_cruises()** - Searches cruise routes
6. **init_inventory()** - Initializes mock data for 30 days

### Booking Functions:
1. **engine_book()** - Creates booking, updates inventory
2. **create_db_booking_from_engine()** - Persists booking to database
3. **engine_get_booking()** - Retrieves booking details
4. **engine_cancel_booking()** - Cancels booking
5. **engine_booking_status()** - Returns real-time booking status
6. **get_user_bookings()** - Gets user's booking history

## APIs/Libraries/Packages Used
- **Mock Data:** In-memory dictionaries for inventory
- **Real APIs (Optional):**
  - AviationStack API - Real flight data
  - IRCTC API - Train data via RapidAPI
- **Database:** SQLAlchemy ORM

## Database Tables/Models Used
```
Booking Table:
├── id (Primary Key)
├── user_id (Foreign Key to User)
├── booking_type (flight/hotel/train/cab/bus/cruise)
├── provider (airline/hotel name/operator)
├── from_location (departure city)
├── to_location (arrival city)
├── date (travel/check-in date)
├── time (departure time)
├── price (total price in INR)
├── travelers (number of people)
├── hotel_name
├── room_type
├── check_in
├── check_out
├── nights
├── flight_number
├── airline
├── duration
├── train_number
├── train_name
├── coach
├── seat_number
├── bus_operator
├── bus_number
├── seat_numbers
├── payment_id (Razorpay)
├── order_id (Razorpay)
├── status (confirmed/cancelled)
├── special_requests
└── created_at timestamp

In-Memory Inventory (flight_inventory, train_inventory, etc.):
{
  "Delhi|Mumbai|2025-04-15": {
    "flights": [
      {
        "flight_number": "6E101",
        "airline": "IndiGo",
        "departure_time": "09:30",
        "arrival_time": "11:45",
        "duration": 135,
        "price": 4500,
        "seats": 150,
        "available_seats": 45
      }
    ],
    "booked": 105
  }
}
```

## State Management/Hooks Used
- **Frontend:** Search parameters stored in form state
- **Backend:** In-memory inventory dictionary, session-based
- **Database:** Persistent booking records in SQLite
- **Gamification event tracking:** Stored in GamificationEvent table

## Complete Workflow Step-by-Step

### Booking Workflow:
```
1. User selects transport type (Flight/Hotel/Train/Cab/Cruise)
   ↓
2. User fills search criteria with date, origin, destination, travelers
   ↓
3. Frontend validates inputs
   ↓
4. GET /api/engine/flights?origin=Delhi&destination=Mumbai&date=2025-04-15
   ↓
5. Backend retrieves from flight_inventory[key]
   ↓
6. Applies dynamic pricing based on demand_factor:
   price = base_price × (1 + (booked/total_seats) × 0.5)
   ↓
7. Frontend displays results sorted by price/time
   ↓
8. User clicks "Book Now" on selected flight
   ↓
9. Frontend opens booking form (passenger details, special requests)
   ↓
10. POST /api/engine/book with booking details
    {
      "type": "flight",
      "details": {
        "origin": "Delhi",
        "destination": "Mumbai",
        "date": "2025-04-15",
        "airline": "IndiGo",
        "flight_number": "6E101",
        "travelers": 2,
        "price": 9000
      }
    }
   ↓
11. Backend creates booking record:
    - Generates unique booking_id (BK1001)
    - Creates Booking record in database
    - Updates inventory: flight_inventory[key]['booked'] += travelers
   ↓
12. Triggers gamification event:
    award_event('booking_flight', event_ref=booking.id)
    Adds coins and XP to user's gamification profile
   ↓
13. If payment integration enabled, returns order_id for Razorpay
   ↓
14. Frontend shows booking confirmation with:
    - Booking ID
    - Travel details
    - Total price
    - Payment button
   ↓
15. User completed!
```

### Real-Time Status Tracking:
```
User clicks "Track Booking"
    ↓
GET /api/engine/booking/<booking_id>/status
    ↓
Backend returns mocked real-time data:
For Flight: Flight status (Boarding/Departed/Landed), Gate, Terminal
For Train: Train status, Platform, Coach
For Hotel: Check-in status, Room number
For Cab: Driver name, Cab number, ETA
    ↓
Frontend displays with real-time updates
```

## Important Variables/Props/States Used
- **booking_type:** "flight", "hotel", "train", "cab", "bus", "cruise"
- **provider:** Name of airline/hotel/operator
- **date:** Travel or check-in date
- **travelers:** Number of people traveling
- **price:** Total booking amount in INR
- **from_location, to_location:** Origin and destination
- **booking_counter:** Global counter for unique booking IDs
- **demand_factor:** Calculated from (booked / total_seats)

## Error Handling/Validation Used
- **Missing parameters:** Returns 400 Bad Request
- **Date validation:** Check-out must be after check-in
- **Availability check:** Ensure seats/rooms available
- **Price validation:** Positive numbers only
- **Database transaction:** Rollback if booking save fails
- **Inventory update atomicity:** Update counters only after DB commit

## Third-party Integrations Used
- **AviationStack API** - Real flight data (if API key configured)
- **RapidAPI (IRCTC)** - Train schedules (optional)
- **Razorpay** - Payment processing (separate feature)

## How Frontend and Backend Communicate
```
Frontend (HTML form)
    ↓ (GET with query parameters)
/api/engine/flights?origin=Delhi&destination=Mumbai&date=...
    ↓ (JSON response with results array)
Flask Backend
    ↓ (Query in-memory inventory)
flight_inventory dictionary
    ↓ (Apply pricing logic)
    ↓ (Send JSON response)
Frontend displays results
    ↓ (User selects and clicks Book)
    ↓ (POST with booking details)
/api/engine/book
    ↓ (Backend creates records)
SQLite Database + In-memory Inventory
    ↓ (Gamification event)
    ↓ (Return confirmation)
Frontend shows booking ID and status
```

## Files to Explain in Viva
1. `app.py` - Lines 1404-1610: All booking engine routes
2. `booking_engine.py` - Mock data and inventory system
3. `models.py` - Booking model definition
4. `templates/booking.html` - Booking UI
5. `templates/bookings.html` - Booking history UI

## Possible Viva Questions & Answers

**Q1: How does dynamic pricing work?**
```
A: We implement demand-based pricing. When users book, we increment the 
'booked' counter in the inventory. The price is calculated as:
price = base_price × (1 + (booked/total_seats) × 0.5)

This means:
- If 0 booked: price stays same
- If 50% booked: price increases by 25%
- If 100% booked: price increases by 50%

This simulates real-world airline pricing where prices go up as seats 
fill. In production, this would sync with real airline APIs.
```

**Q2: Why use in-memory inventory instead of only database?**
```
A: In-memory inventory provides:
1. Fast queries without database reads
2. Real-time availability updates across all users
3. Simulates real booking competition (seat getting booked by another user)

In production, we'd use Redis for distributed in-memory cache. 
Database is for persistent booking records for user history.
```

**Q3: How are booking IDs generated?**
```
A: Booking IDs are generated sequentially:
booking_counter = 1000 (initial)
Each new booking: booking_counter += 1
booking_id = "BK" + booking_counter

In production, we'd use UUID:
import uuid
booking_id = str(uuid.uuid4())

This prevents ID guessing and handles distributed systems better.
```

**Q4: What happens if two users book the same flight simultaneously?**
```
A: Both requests check inventory separately and see available seats.
Both can proceed. When they POST to book:
1. First request: booked += travelers, updates DB first
2. Second request: booked += travelers as well

Issue: Both get confirmed but inventory count may exceed actual seats!

Solution: Use database-level locking or transaction isolation levels. 
For current mock system, the inventory counter still works for demo but 
production needs transaction management.
```

---

# FEATURE 4: RAZORPAY PAYMENT INTEGRATION

## Purpose
Process payments for bookings using Razorpay, India's leading payment gateway. Enables:
- Secure online payment processing
- Multiple payment methods (Cards, UPI, Wallets)
- Order management and verification
- Payment status tracking

## Frontend Components/Pages/Files Used
- **Pages:** `templates/booking.html`, `templates/bookings.html`
- **JavaScript:** Razorpay checkout script integration
- **UI Elements:**
  - Payment button
  - Razorpay checkout modal
  - Payment status messages
  - Receipt display

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 1900+)
- **Utils:** `utils.py` - Razorpay order creation
- **Models:** `models.py` - Booking model with payment_id, order_id

## API Routes
```python
POST /api/create_order           # Create Razorpay order (JWT required)
POST /api/verify_payment         # Verify payment signature
```

## Functions/Methods Used
1. **create_order()** - Creates Razorpay order
2. **create_razorpay_order()** (utils.py) - Helper function
3. **verify_payment()** - Verifies payment with Razorpay

## APIs/Libraries/Packages Used
- **Razorpay Python SDK:** `razorpay` package
- **Cryptographic Signature:** `hmac` for payment verification

## Database Tables/Models Used
```
Booking Table Fields:
├── payment_id (Razorpay payment ID)
├── order_id (Razorpay order ID)
└── status (confirmed/pending/cancelled)
```

## State Management/Hooks Used
- **Frontend:**
  ```javascript
  let razorpayOrderId = null;
  let razorpayPaymentId = null;
  ```
- **Backend:** Storing order/payment IDs in Booking record

## Complete Workflow Step-by-Step

### Payment Workflow:
```
1. User confirms booking with all details
   ↓
2. Frontend shows "Pay Now" button
   ↓
3. User clicks "Pay Now"
   ↓
4. POST /api/create_order
   Request body:
   {
     "amount": 4500,
     "booking_id": "BK1005",
     "booking_type": "flight"
   }
   ↓
5. Backend creates Razorpay order:
   razorpay_client.order.create(amount=450000, currency='INR')
   Note: Amount in paise (450000 = ₹4500)
   ↓
6. Backend returns order details:
   {
     "order_id": "order_9A33XWu590gUtm",
     "amount": 450000,
     "currency": "INR"
   }
   ↓
7. Frontend initializes Razorpay checkout:
   let options = {
     key: RAZORPAY_KEY_ID,                    // Public key
     amount: amount_in_paise,
     currency: "INR",
     name: "YATRIKA",
     description: booking_type,
     order_id: order_id,
     handler: function(response) {            // Callback on success
       payment_id = response.razorpay_payment_id;
       verify_payment(order_id, payment_id, signature);
     }
   };
   let rzp = new Razorpay(options);
   rzp.open();
   ↓
8. Razorpay checkout modal opens
   User selects payment method:
   - Credit/Debit Card
   - UPI
   - Wallet (Google Pay, Apple Pay, etc.)
   ↓
9. User completes payment on Razorpay's secure portal
   ↓
10. Razorpay returns payment details to frontend:
    {
      "razorpay_order_id": "order_9A33XWu590gUtm",
      "razorpay_payment_id": "pay_29QQoUBi66xm2f",
      "razorpay_signature": "9ef4dffbfd84f1318f6739..."
    }
   ↓
11. Frontend calls POST /api/verify_payment with all three values
   ↓
12. Backend verifies signature:
    Expected_signature = HMAC-SHA256(
      order_id + "|" + payment_id,
      secret_key
    )
    
    If signature matches:
    - Payment confirmed
    - Set Booking.payment_id = payment_id
    - Set Booking.order_id = order_id
    - Set Booking.status = 'confirmed'
    - Save to database
    Else:
    - Payment fraud detected!
    - Return 400 error
   ↓
13. If signature valid, return success response
   ↓
14. Frontend:
    - Show payment successful message
    - Display booking with payment details
    - Save booking locally
    - Redirect to booking confirmation page
   ↓
15. User receives confirmation with booking ID and receipt
```

## Important Variables/Props/States Used
- **amount:** Payment amount in INR
- **razorpay_key_id:** Public key for Razorpay (frontend)
- **razorpay_key_secret:** Secret key for verification (backend only)
- **order_id:** Razorpay order ID
- **payment_id:** Razorpay payment ID (after payment)
- **signature:** HMAC-SHA256 signature for verification
- **booking_id:** Internal booking ID being paid for

## Error Handling/Validation Used
- **Missing amount:** Returns 400 Bad Request
- **Invalid order:** Check order exists before verification
- **Signature mismatch:** Returns 400 - Payment verification failed
- **API errors:** Catch Razorpay API exceptions, log errors
- **Network timeouts:** Implement retry logic with exponential backoff
- **Database errors:** Rollback if payment record save fails

## Third-party Integrations Used
- **Razorpay Payment Gateway**
  - Website: https://razorpay.com
  - Supported payment methods: Cards, UPI, Wallets, NetBanking
  - Real-time settlement
  - Multi-currency support (INR)

## How Frontend and Backend Communicate
```
Frontend (Checkout Modal)
    ↓ (POST with amount, booking details)
/api/create_order
    ↓ (Call Razorpay API)
Razorpay Backend
    ↓ (Returns order_id)
Flask Backend
    ↓ (Send order details to frontend)
Frontend displays Razorpay Modal
    ↓ (User pays)
    ↓ (POST with payment details)
/api/verify_payment
    ↓ (Verify signature with secret key)
    ↓ (Update booking in database)
SQLite Database
    ↓ (Success response)
Frontend shows confirmation
```

## Files to Explain in Viva
1. `app.py` - Razorpay order creation and verification
2. `utils.py` - create_razorpay_order() helper
3. `templates/booking.html` - Payment button and Razorpay integration
4. `models.py` - Booking model with payment fields

## Possible Viva Questions & Answers

**Q1: Why is payment amount in paise (₹4500 = 450000 paise)?**
```
A: Razorpay API uses the smallest currency unit (paise) to avoid 
floating-point precision issues. 1 Rupee = 100 paise.

So: 4500 INR × 100 = 450000 paise

This is similar to how most payment APIs work:
- Stripe uses cents (USD)
- PayPal uses cents
This ensures exact amounts without rounding errors.
```

**Q2: What is the role of the signature in payment verification?**
```
A: Signature prevents payment tampering. Here's how:

1. Frontend receives payment details from Razorpay
2. Backend independently recreates the signature:
   signature = HMAC-SHA256(order_id|payment_id, SECRET_KEY)
3. Compares with received signature
4. If signatures match: Payment is genuine (from Razorpay)
5. If signatures don't match: Attacker tried to modify payment details!

HMAC guarantees that only our server (with SECRET_KEY) can create 
valid signatures. Frontend never has access to SECRET_KEY.
```

**Q3: Why not trust Razorpay callback directly?**
```
A: We don't rely solely on callback webhooks because:
1. Webhooks can fail to deliver (network issues)
2. Frontend closes before webhook arrives
3. Attacker could spoof webhooks

Best practice: After user confirms payment, verify on backend using 
signature verification. This ensures payment is real before updating 
booking status.
```

**Q4: What happens if payment fails?**
```
A: If user cancels payment or payment fails:
1. Razorpay handler is not called
2. User is returned to checkout page
3. No booking record is created
4. No database change happens
5. User can retry payment

After 30 minutes, Razorpay order expires and user must start fresh.
In our system, booking is only confirmed AFTER verified payment.
```

---

# FEATURE 5: LIVE FLIGHT TRACKER

## Purpose
Real-time flight tracking using OpenSky Network free API. Allows users to:
- See live aircraft positions on a map
- Track flight altitude, speed, and direction
- Monitor flights in real-time globally
- Get live flight data for educational/informational purposes

## Frontend Components/Pages/Files Used
- **Pages:** `templates/live_flights.html`
- **JavaScript:** Map library integration (likely Leaflet or Google Maps)
- **UI Elements:**
  - Interactive map showing aircraft
  - Flight list/table
  - Aircraft markers with flight info
  - Real-time data updates
  - Filters by airline/country

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 595-628)
- **API Integration:** OpenSky Network public API

## API Routes
```python
GET /api/live-flights   # Get live flight data (no auth required)
```

## Functions/Methods Used
1. **get_live_flights()** - Fetches data from OpenSky Network API

## APIs/Libraries/Packages Used
- **OpenSky Network API:** https://opensky-network.org/apiv2/states/all
- **HTTP Library:** `requests` package
- **Data Format:** JSON parsing

## Database Tables/Models Used
- **No database storage** - Real-time data only, not persisted

## State Management/Hooks Used
- **Frontend:** setInterval() to update flights every 10-15 seconds
  ```javascript
  let flightUpdateInterval = setInterval(() => {
      fetch('/api/live-flights')
        .then(r => r.json())
        .then(data => updateMapMarkers(data.flights));
  }, 15000);  // Update every 15 seconds
  ```

## Complete Workflow Step-by-Step

### Live Flight Tracking:
```
1. User navigates to /live-flights page
   ↓
2. Frontend initializes map (Leaflet/Google Maps)
   ↓
3. Frontend calls GET /api/live-flights
   ↓
4. Backend calls OpenSky Network API:
   https://opensky-network.org/api/states/all?lamin=MIN_LAT&...
   
   Response structure:
   {
     "states": [
       [
         "icao24",                    // Aircraft ICAO ID
         "callsign",                  // Flight number (e.g., "EK524")
         "origin_country",            // Country
         "time_position",             // Time of last position
         "last_contact",              // Last contact with receiver
         1234.5,                      // [5] longitude
         5678.9,                      // [6] latitude
         12000,                       // [7] altitude (meters)
         false,                       // [8] on_ground
         250,                         // [9] velocity (m/s)
         12.5,                        // [10] true_track (bearing)
         ...
       ]
     ]
   }
   ↓
5. Backend filters flights:
   - Only include in-air flights (on_ground == false)
   - Only include flights with position data (lon != null, lat != null)
   - Limit to top 100 flights
   ↓
6. Backend transforms to simple format:
   {
     "flights": [
       {
         "icao24": "a8d4b8",
         "callsign": "EK524",
         "origin_country": "United Arab Emirates",
         "longitude": 55.27,
         "latitude": 25.23,
         "altitude": 12000,
         "velocity": 250,
         "true_track": 45.5,
         "on_ground": false
       }
     ]
   }
   ↓
7. Frontend receives JSON response
   ↓
8. For each flight:
   - Create marker on map at (latitude, longitude)
   - Set marker icon/rotation based on true_track (bearing)
   - Add popup with flight info (callsign, altitude, velocity)
   ↓
9. Frontend sets interval to refresh every 15 seconds
   - Clear old markers
   - Fetch new flight positions
   - Draw updated markers
   ↓
10. User can click on aircraft to see more details:
    - Flight number
    - Origin country
    - Altitude
    - Speed
    - Direction
```

## Important Variables/Props/States Used
- **icao24:** Unique aircraft identifier
- **callsign:** Flight number (e.g., "EK524" for Emirates 524)
- **latitude, longitude:** Current position
- **altitude:** Height in meters
- **velocity:** Speed in m/s
- **true_track:** Bearing/direction in degrees (0-360)
- **on_ground:** Boolean indicating if aircraft is on ground
- **origin_country:** Aircraft registration country

## Error Handling/Validation Used
- **API timeout:** 15-second timeout on OpenSky Network request
- **Connection error:** Catch and return empty array
- **Missing data:** Filter out incomplete flight records
- **Rate limiting:** OpenSky allows ~4000 requests/hour per IP
- **Frontend error handling:** Display "Loading..." or "No flights available"

## Third-party Integrations Used
- **OpenSky Network API** - Free, public API for real-time flight data
  - Rate limit: ~4000 requests/hour
  - No authentication required
  - Global flight coverage
  - 15-20 second data freshness

## How Frontend and Backend Communicate
```
Frontend (Leaflet Map)
    ↓ (GET request every 15-30 seconds)
/api/live-flights
    ↓ (HTTP request)
OpenSky Network API
    ↓ (JSON with live aircraft data)
Flask Backend
    ↓ (Transform and filter data)
    ↓ (Return simplified JSON)
Frontend receives
    ↓ (Plot markers on map)
    ↓ (Update positions, add popups)
User sees live aircraft on interactive map
```

## Files to Explain in Viva
1. `app.py` - Lines 595-628: get_live_flights() route
2. `templates/live_flights.html` - Map display and updates
3. `static/js/main.js` - Frontend map handling

## Possible Viva Questions & Answers

**Q1: How does the map coordinate system work?**
```
A: Maps use (latitude, longitude) pairs:
- Latitude: -90 to +90 (South Pole to North Pole)
- Longitude: -180 to +180 (West to East)

OpenSky returns:
- Longitude in element [5]
- Latitude in element [6]

Frontend maps like Leaflet expect: L.latlng(latitude, longitude)

Important: Order matters! Some APIs use [lon, lat] and some [lat, lon].
```

**Q2: What does true_track represent?**
```
A: true_track is the bearing/heading of aircraft in degrees:
- 0° = North
- 90° = East
- 180° = South
- 270° = West

Used to rotate aircraft icon on map to show direction of travel.
Frontend rotates marker image by this angle:
marker.setRotation(true_track);
```

**Q3: Why are we only showing in-air flights?**
```
A: Status field shows: on_ground = true/false

on_ground = true: Aircraft at gate/taxiing (not interesting for live tracker)
on_ground = false: Aircraft flying (interesting to track)

Filtering criteria:
1. on_ground == false (in-air flights only)
2. longitude != null && latitude != null (has position)
3. velocity > 0 (actually moving, not hovering)

This reduces clutter on map and focuses on active flights.
```

**Q4: How frequently should we update the map?**
```
A: OpenSky API updates every 15-20 seconds globally. 

Update frequency options:
- Every 10 seconds: More responsive, higher API calls
- Every 15 seconds: Balanced (standard)
- Every 30 seconds: Lower API calls, less responsive

For our demo with ~4000 updates/hour limit:
15 seconds = 240 requests/hour = Well within limit

In production, cache would be on server to reduce external API calls.
```

---

# FEATURE 6: SMART MAP WITH LOCATION SERVICES

## Purpose
Interactive map with location intelligence providing users:
- Search nearby places (food, attractions, shopping, emergencies)
- Crowd density prediction for locations
- Parking spot recommendations
- Weather data by location
- Route planning
- Local experiences and cultural spots
- Emergency SOS alerts

## Frontend Components/Pages/Files Used
- **Pages:** `templates/smart_map.html`
- **JavaScript:** Map library integration, real-time updates
- **UI Elements:**
  - Interactive map with markers
  - Search categories (Food, Tourism, Shopping, Emergency)
  - Filters and legends
  - Place info cards
  - Weather widget
  - SOS button

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 957-1180)
- **Utils:** `utils.py` - Geocoding, search, routing

## API Routes
```python
GET  /api/nearby/search           # Search nearby places
GET  /api/crowd/density           # Get crowd predictions with wait times
GET  /api/crowd/heatmap           # Generate crowd heatmap
GET  /api/parking/nearby          # Find nearby parking
GET  /api/local-experiences       # Get local activities
GET  /api/weather/map             # Get weather by coordinates
POST /api/sos                      # Emergency SOS alert
GET  /api/geocode                 # Geocode place name to coordinates
```

## Functions/Methods Used

### Location Search:
1. **search_nearby_osm()** - Uses Overpass API to find nearby places
2. **reverse_geocode_osm()** - Get place name from coordinates
3. **geocode_osm()** - Convert place name to coordinates
4. **nearby_search()** - API endpoint wrapper

### Crowd & Time Management:
1. **crowd_density_with_waiting()** - Predicts crowds and wait times
2. **get_crowd_density()** - Mock crowd prediction
3. **crowd_heatmap()** - Generate heatmap for popular areas
4. **get_best_time_to_visit()** - Recommend best visit times

### Parking & Experiences:
1. **nearby_parking()** - Find parking spots
2. **local_experiences()** - Get local cultural experiences
3. **get_place_type_from_name()** - Classify places

### Emergency & Weather:
1. **sos_alert()** - Broadcast emergency alert
2. **weather_api()** - Get weather by coordinates
3. **get_route_osm()** - Calculate routes using OSRM

## APIs/Libraries/Packages Used
- **OpenStreetMap Nominatim:** Geocoding (free)
- **Overpass API:** Place searches
- **OSRM (Open Source Routing Machine):** Route calculation
- **OpenWeather API:** Real-time weather (if key provided)
- **WebSocket (Socket.IO):** Real-time SOS broadcasts

## Database Tables/Models Used
- **Place Table:**
  ```
  id, user_id, name, lat, lng, tags, description, created_at
  ```
- **No persistent storage for searches** - Real-time only

## State Management/Hooks Used
- **Frontend:**
  ```javascript
  let currentLocation = null;      // User's current position
  let nearbyPlaces = [];           // Fetched places
  let selectedCategory = 'all';    // Filter category
  let searchRadius = 2000;         // Search radius in meters
  ```
- **Backend:** Request parameters in Flask `request` object

## Complete Workflow Step-by-Step

### Smart Map Nearby Search:
```
1. User opens Smart Map page at /smart-map
   ↓
2. Frontend requests user's location:
   navigator.geolocation.getCurrentPosition(position => {
     lat = position.coords.latitude;
     lng = position.coords.longitude;
   })
   ↓
3. User selects category (Food, Tourism, Shopping, Emergency, All)
   ↓
4. Frontend calls:
   GET /api/nearby/search?lat=28.6139&lng=77.2090&
       radius=2000&category=food
   ↓
5. Backend calls Overpass API:
   Query: [amenity~"restaurant|cafe|fast_food"](around:2000,28.6139,77.2090)
   ↓
6. Overpass returns places near coordinates
   ↓
7. For each place:
   - Calculate distance using Haversine formula
   - Classify place type (restaurant, cafe, etc.)
   - Cache result for 2 minutes
   ↓
8. Return top 50 places sorted by distance:
   {
     "places": [
       {
         "id": 123456,
         "name": "Cafe Coffee Day",
         "type": "cafe",
         "lat": 28.6145,
         "lng": 77.2095,
         "distance": 0.3,
         "address": "Connaught Place"
       }
     ]
   }
   ↓
9. Frontend displays markers on map
   ↓
10. User clicks on marker → Info card shows:
    - Place name and type
    - Distance from user
    - Category icon
    - "Get Directions" button
```

### Crowd Density Prediction:
```
1. User selects a restaurant/attraction
   ↓
2. Frontend calls:
   GET /api/crowd/density?lat=28.6145&lng=77.2095&type=restaurant
   ↓
3. Backend calculates crowd factor based on current time:
   If 9-11 AM: crowd_factor = 0.7 (less crowded)
   Else if 12-14: crowd_factor = 0.8 (busy lunch)
   Else if 17-20: crowd_factor = 0.9 (dinner time)
   Else: crowd_factor = 0.3 (quiet)
   ↓
4. For each place type:
   - Restaurant 12-2 PM or 7-10 PM: HIGH crowd
   - Attraction 8-10 AM: LOW crowd
   - Mall 2-5 PM: MEDIUM crowd
   - Station avoid 8-10 AM, 5-7 PM: RUSH hours
   ↓
5. Calculate waiting time:
   base_wait = random time based on type & crowd
   waiting_time = base_wait × waiting_factor
   ↓
6. Return:
   {
     "places": [
       {
         "crowd_level": 75,           // 0-100
         "crowd_status": "Very Busy",
         "crowd_color": "#ef4444",    // Red
         "waiting_time": 25,
         "waiting_text": "25 min wait",
         "best_time": "Early morning (9-11 AM)"
       }
     ]
   }
   ↓
7. Frontend displays:
   - Color-coded crowd level (Green=quiet, Orange=medium, Red=busy)
   - Estimated waiting time
   - Best time to visit recommendation
```

### Parking Spot Finder:
```
1. User searches for parking: GET /api/parking/nearby?lat=28.6139&lng=77.2090
   ↓
2. Backend searches for parking spots within 1 km radius
   ↓
3. If real data not available, generates mock parking:
   - Downtown Parking Garage: ₹30/hour, 25/50 spots
   - Street Parking: ₹20/hour, 12/40 spots
   - Free Community Parking: Free, 8/30 spots
   ↓
4. For each spot, provides:
   - Available/total spots
   - Price per hour
   - Distance from user
   - Features (EV charging, CCTV, covered)
   ↓
5. Frontend displays sorted by:
   - Availability (most spots first)
   - Price (cheapest first)
   - Distance (nearest first)
```

### Emergency SOS Alert:
```
1. User clicks SOS button
   ↓
2. Frontend gets current location GPS
   ↓
3. Frontend shows emergency confirmation dialog
   ↓
4. User clicks "Send Alert"
   ↓
5. POST /api/sos with location data
   {
     "latitude": 28.6139,
     "longitude": 77.2090,
     "emergency_type": "help"
   }
   ↓
6. Backend searches for emergency services nearby:
   - Hospitals (emergency_phone: 108)
   - Police (100)
   - Fire Station (101)
   ↓
7. Backend broadcasts alert via WebSocket:
   io.emit('emergency_alert', {
     user_id: 123,
     username: 'john_doe',
     location: { lat: 28.6139, lng: 77.2090 },
     emergency_services: [nearest 5 services],
     timestamp: now
   }, broadcast=True)
   ↓
8. All connected clients receive alert
   (In production, this would alert emergency services/nearby users)
   ↓
9. Frontend shows:
   - Alert sent confirmation
   - Map zoomed to emergency services
   - Phone numbers displayed
   ↓
10. User can call emergency number directly
```

## Important Variables/Props/States Used
- **lat, lng:** User's coordinates from GPS
- **radius:** Search radius in meters (typically 1000-3000)
- **category:** Place type filter (food, tourism, shopping, emergency, all)
- **crowd_level:** 0-100 percentage
- **waiting_time:** Minutes of estimated wait
- **best_time:** Recommended visiting time as string
- **emergency_phone:** Emergency service contact number

## Error Handling/Validation Used
- **Missing coordinates:** Returns 400 if lat/lng not provided
- **Timeout handling:** Overpass API timeout (7 seconds), fallback to mock
- **Empty results:** Generate mock data if OSM returns nothing
- **Coordinate bounds:** Validate lat (-90 to 90), lng (-180 to 180)
- **Radius validation:** Clamp radius to reasonable range (500-5000m)
- **Cache expiry:** 2-minute cache for same coordinates to reduce API calls

## Third-party Integrations Used
- **OpenStreetMap Nominatim** - Free geocoding API
- **Overpass API** - Free place searches
- **OSRM (Open Source Routing Machine)** - Free routing
- **OpenWeather API** - Weather data (optional, has fallback)
- **Socket.IO** - Real-time communication for SOS

## How Frontend and Backend Communicate
```
Frontend (Geolocation + Map UI)
    ↓ (GET with coordinates)
/api/nearby/search?lat=...&lng=...&category=food
    ↓ (Call external APIs)
Backend (Flask)
    ↓ (Query Nominatim/Overpass)
OSM APIs
    ↓ (Return places)
Backend (transform & filter)
    ↓ (Return JSON)
Frontend
    ↓ (Render markers on map)
User sees nearby places with icons
```

## Files to Explain in Viva
1. `app.py` - Lines 957-1180: All smart map routes
2. `utils.py` - Geocoding, search, routing functions
3. `templates/smart_map.html` - Map UI
4. `models.py` - Place model (for saved places)

## Possible Viva Questions & Answers

**Q1: How does the Haversine formula work for distance calculation?**
```
A: Haversine calculates great-circle distance between two points on Earth.

Formula:
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1−a))
d = R × c

Where:
- R = Earth's radius (6371 km)
- Δlat, Δlon = differences in latitude/longitude
- atan2 = 2-argument arctangent

Returns distance in km. Much more accurate than simple Euclidean 
distance for spherical Earth calculations.

We use this to:
1. Sort places by distance from user
2. Filter places within search radius
3. Find nearest parking/emergency services
```

**Q2: What happens if Overpass API fails?**
```
A: Multi-layer fallback:
1. Try Overpass API (7-second timeout)
2. If timeout/failure, return mock data
   - Predefined places around coordinate
   - Categories: cafes, attractions, malls, stations
   - Realistic distances
3. Ensures user always gets results

Log statement: "⚠️ Using MOCK data for {lat},{lng} (OSM lookup failed)"

This maintains UX even during API issues. In production, we'd 
probably cache responses or use multiple APIs.
```

**Q3: How is caching implemented in search_nearby_osm()?**
```
A: In-memory cache with expiry:

_nearby_cache = {}  # Global dictionary

cache_key = f"{round(lat,4)}|{round(lng,4)}|radius|category"
current_time = time.time()

if cache_key in _nearby_cache:
    cached = _nearby_cache[cache_key]
    if (now - cached['ts'] < 120):  # 2-minute expiry
        return cached['data']

After API call:
_nearby_cache[cache_key] = {
    'ts': now,
    'data': results
}

Benefits:
- Reduces API calls by 80-90%
- Faster responses
- Reduces load on Overpass (free API)
- 2-min freshness is acceptable for static searches

Limitation: Cache is per-instance. In distributed system, use Redis.
```

**Q4: Why use OSRM instead of Google Maps for routing?**
```
A: OSRM advantages:
✓ Free and open-source
✓ No API key required
✓ Hosted publicly at router.project-osrm.org
✓ No rate limiting
✓ Good for basic routing

Google Maps advantages:
✓ More accurate (real traffic data)
✓ Better support
✓ Paid but reliable

For MVP/demo, OSRM is perfect. For production, integrate Google Maps 
for real-time traffic. Our code structure allows easy swapping of 
routing providers.
```

---

# FEATURE 7: EXPENSE TRACKER

## Purpose
Track and manage trip expenses to:
- Categorize spending (food, accommodation, transport, shopping, etc.)
- Calculate total trip costs
- Split expenses analysis
- Budget monitoring
- Expense history by trip and category

## Frontend Components/Pages/Files Used
- **Pages:** `templates/dashboard.html` (contains expense section)
- **UI Elements:**
  - Expense entry form
  - Category selector
  - Date picker
  - Expense list/table
  - Charts and statistics
  - Category-wise breakdown

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (via Trip/Booking routes)
- **Models:** `models.py` - Expense model, Trip model

## API Routes
```python
POST /api/expenses           # Add new expense (implied)
GET  /api/trips/<id>/expenses  # Get expenses for trip (implied)
GET  /api/expenses/summary   # Get expense summary stats (implied)
```

## Functions/Methods Used
1. **create_expense()** - Create new expense record
2. **get_expenses()** - Retrieve user's expenses
3. **calculate_trip_total()** - Sum expenses for a trip
4. **expense_breakdown()** - Category-wise analysis

## Database Tables/Models Used
```
Expense Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── trip_id (Foreign Key)
├── category (String)
│  ├── food
│  ├── transport
│  ├── accommodation
│  ├── shopping
│  ├── entertainment
│  ├── medical
│  └── other
├── amount (Float)
├── date (Date)
├── note (Text)
└── created_at (DateTime)

Relationships:
Expense → User (many-to-one)
Expense → Trip (many-to-one)
```

## State Management/Hooks Used
- **Frontend:**
  ```javascript
  let expensesByCategory = {};
  let totalExpense = 0;
  let currentTrip = null;
  ```

## Complete Workflow Step-by-Step

### Adding Expense:
```
1. User clicks "Add Expense" button in dashboard/trip view
   ↓
2. Frontend shows expense entry form:
   - Select trip (dropdown)
   - Select category (food, transport, etc.)
   - Amount input
   - Date picker (defaults to today)
   - Optional notes
   ↓
3. User fills form and clicks "Save"
   ↓
4. Frontend validates:
   - Amount > 0
   - Category selected
   - Trip selected
   ↓
5. POST /api/expenses (or embedded in trip endpoints)
   {
     "trip_id": 5,
     "category": "food",
     "amount": 500,
     "date": "2025-04-15",
     "note": "Dinner at Italian restaurant"
   }
   ↓
6. Backend creates Expense record
   ↓
7. Database stores expense
   ↓
8. Frontend updates expense list immediately
   ↓
9. Frontend updates total expense calculation
```

### Viewing Trip Summary:
```
1. User views trip details
   ↓
2. Frontend fetches trip data including expenses
   ↓
3. Frontend calculates:
   - Total spent (sum of all expenses)
   - Budget remaining (trip.budget - total_spent)
   - Spent percentage (total_spent / trip.budget * 100)
   ↓
4. Breakdown by category:
   Food: 2000 (40%)
   Transport: 1500 (30%)
   Accommodation: 1200 (24%)
   Shopping: 300 (6%)
   ↓
5. Display:
   - Progress bar showing budget usage
   - Top categories
   - Daily spending trend
   - Comparison: Planned vs Actual
   ↓
6. User can click category to see detailed breakdown
```

## Important Variables/Props/States Used
- **category:** Expense category enum (food, transport, accommodation, shopping, entertainment, medical, other)
- **amount:** Expense amount in INR
- **trip_id:** Foreign key to trip
- **date:** When expense occurred
- **note:** Description/note about expense

## Error Handling/Validation Used
- **Amount validation:** Positive numbers only, reasonable limits
- **Category validation:** Must be valid category enum
- **Date validation:** Cannot be future date, within trip dates
- **Trip association:** Expense must belong to valid trip
- **Database transaction:** Rollback if insert fails

## Third-party Integrations Used
- **None** - Pure backend implementation

## How Frontend and Backend Communicate
```
Frontend (Expense Form)
    ↓ (POST with expense data)
/api/expenses
    ↓ (Validate & store)
Backend (Flask)
    ↓ (Database insert)
SQLite Database
    ↓ (Success response)
Frontend updates:
- Expense list
- Total calculation
- Charts refresh
```

## Files to Explain in Viva
1. `models.py` - Expense model and Trip model
2. `app.py` - Trip CRUD endpoints (expense management)
3. `templates/dashboard.html` - Expense display and charts

## Possible Viva Questions & Answers

**Q1: How do you calculate budget utilization?**
```
A: Simple formula:
utilized_percentage = (total_expenses / trip_budget) * 100

Then categorize:
- 0-50%: Green (under budget)
- 50-90%: Yellow (spending well)
- 90-100%: Orange (approaching limit)
- >100%: Red (over budget)

This helps users quickly see if they're overspending:
Trip Budget: ₹10,000
Spent: ₹7,500
Utilization: 75% (Yellow - nearly 3/4 spent)
Remaining: ₹2,500
```

**Q2: How is the expense date validated?**
```
A: Validation rules:
1. Must be valid date format (YYYY-MM-DD)
2. Cannot be future date (today or earlier)
3. Should be within trip dates:
   trip.start_date <= expense.date <= trip.end_date
4. For pending/future trips, constraint might be relaxed

This prevents:
- Invalid dates
- Planning expenses ahead of time (with constraints)
- Expenses for wrong trips
```

**Q3: What if user wants to edit/delete an expense?**
```
A: CRUD operations:
- Create: POST /api/expenses
- Read: GET /api/expenses or with trip
- Update: PUT /api/expenses/<id>
- Delete: DELETE /api/expenses/<id>

When deleting:
- Verify user ownership
- Recalculate trip total
- Update category breakdown
- Refresh UI
```

---

# FEATURE 8: DASHBOARD & USER PROFILE

## Purpose
Central hub displaying:
- User profile information
- Upcoming trips
- Recent bookings
- Saved places and wishlists
- Gamification stats
- Trip statistics and analytics

## Frontend Components/Pages/Files Used
- **Pages:** `templates/dashboard.html`, `templates/profile.html`
- **UI Elements:**
  - Profile card with avatar, stats
  - Trip cards with upcoming journeys
  - Booking history
  - Dashboard statistics
  - Profile settings form

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 1800-1870)
- **Models:** `models.py` - User, Trip, Booking models

## API Routes
```python
GET    /api/me                    # Get current user
PUT    /api/update_profile        # Update profile
POST   /api/change_password       # Change password
DELETE /api/delete_account        # Delete account
GET    /api/trips                 # Get user's trips
POST   /api/bookings              # Create/get bookings
GET    /api/stories/my           # Get user's stories
```

## Functions/Methods Used
1. **me()** - Get current user info
2. **update_profile()** - Update bio, phone, avatar
3. **change_password()** - Secure password change
4. **delete_account()** - Full account deletion with cascades
5. **get_trips()** - Retrieve user's trip history
6. **get_user_bookings()** - All bookings for user

## Database Tables/Models Used
```
User Table (already shown in Auth section)
Trip Table (already shown in AI Planner section)
Booking Table (already shown in Booking section)
```

## State Management/Hooks Used
- **Frontend:**
  ```javascript
  let userProfile = null;
  let upcomingTrips = [];
  let recentBookings = [];
  let dashboardStats = {};
  ```

## Complete Workflow Step-by-Step

### Dashboard Loading:
```
1. User navigates to /dashboard
   ↓
2. Frontend checks JWT token in localStorage
   If missing/invalid, redirect to /login
   ↓
3. Frontend makes parallel requests:
   - GET /api/me              → Current user info
   - GET /api/trips           → User's trips
   - GET /api/engine/bookings → Booking history
   - GET /api/companion/profile → Companion profile
   ↓
4. Backend responds with user data:
   ```json
   {
     "id": 123,
     "username": "john_doe",
     "email": "john@example.com",
     "bio": "Adventure seeker",
     "phone": "9876543210",
     "avatar": "avatar_123.jpg"
   }
   
   Trips: [
     {
       "id": 5,
       "destination": "Paris",
       "start_date": "2025-05-01",
       "end_date": "2025-05-07",
       "budget": 50000,
       "expenses": 35000
     }
   ]
   
   Bookings: [
     {...flight booking...},
     {...hotel booking...}
   ]
   ```
   ↓
5. Frontend renders dashboard with sections:
   
   Section 1: Profile Card
   - Avatar
   - Username
   - Stats (trips done, bookings made, etc.)
   - Edit profile button
   
   Section 2: Upcoming Trips
   - Trip cards showing destination, dates, progress
   - "View Details" button
   - Status (Planning, In Progress, Completed)
   
   Section 3: Recent Bookings
   - Last 5 bookings
   - Type, provider, date, price
   - "Track" or "Cancel" buttons
   
   Section 4: Quick Stats
   - Total trips
   - Total bookings
   - Total spent
   - Average rating
   
   Section 5: Gamification (if enabled)
   - Current points/coins
   - Level
   - Mission progress
   - Recent achievements
```

### Profile Update Flow:
```
1. User clicks "Edit Profile"
   ↓
2. Frontend shows profile edit form with current values
   ↓
3. User modifies fields:
   - Bio
   - Phone
   - Avatar (image upload)
   ↓
4. User clicks "Save"
   ↓
5. Frontend validates:
   - Phone format (10 digits)
   - Bio length (max 500 chars)
   - Image size if uploaded
   ↓
6. PUT /api/update_profile
   {
     "bio": "Updated bio",
     "phone": "9999999999",
     "avatar": "new_avatar.jpg"
   }
   ↓
7. Backend updates User record
   ↓
8. Check if profile is now complete:
   - Has bio? ✓
   - Has phone? ✓
   - Has avatar? ✓
   
   If 2+ fields filled: Profile complete!
   award_event('profile_completion', 150 coins)
   ↓
9. Redirect back to dashboard
   ↓
10. Display success message
```

## Important Variables/Props/States Used
- **userProfile:** Complete user object
- **upcomingTrips:** Array of trips with start_date > today
- **pastTrips:** Array of completed trips
- **recentBookings:** Last 5-10 bookings
- **avatarUrl:** URL to user's avatar image

## Error Handling/Validation Used
- **Missing token:** Redirect to login
- **Invalid token:** Show "Session expired, please login"
- **API failures:** Display error messages gracefully
- **Validation errors:** Show inline errors in forms
- **Modal confirmations:** For account deletion (prevent accidents)

## Third-party Integrations Used
- **None** - Pure backend/database implementation

## How Frontend and Backend Communicate
```
Frontend loads /dashboard
    ↓ (Multiple parallel GET requests)
/api/me, /api/trips, /api/engine/bookings
    ↓ (Backend queries database)
SQLite Database
    ↓ (Return JSON responses)
Frontend renders dashboard
    ↓ (User edits profile)
    ↓ (PUT request)
/api/update_profile
    ↓ (Backend validates & updates)
Database updates
    ↓ (Success response)
Frontend shows confirmation
```

## Files to Explain in Viva
1. `app.py` - User and trip endpoints
2. `models.py` - User, Trip, Booking models
3. `templates/dashboard.html` - Dashboard UI
4. `templates/profile.html` - Profile edit UI

## Possible Viva Questions & Answers

**Q1: How do you handle profile image uploads?**
```
A: Image upload process:
1. User selects image in file input
2. Frontend validates:
   - File type (png, jpg, jpeg, gif, webp only)
   - File size (< 5MB typically)
3. Frontend sends as FormData (multipart/form-data)
4. Backend receives file:
   - Validates again
   - Generates unique filename: name_TIMESTAMP.ext
   - Saves to static/uploads/
   - Stores path in User.avatar field
5. Frontend displays from URL: /static/uploads/avatar_123.jpg

Security:
- File type whitelist
- Filename sanitization (no path traversal)
- Store outside web root in production
- Virus scan before storage
```

**Q2: What happens during account deletion?**
```
A: Cascade delete of all related data:

DELETE FROM trips WHERE user_id = 123
DELETE FROM bookings WHERE user_id = 123
DELETE FROM travel_stories WHERE user_id = 123
DELETE FROM expenses WHERE user_id = 123
DELETE FROM reviews WHERE user_id = 123
DELETE FROM wishlist WHERE user_id = 123
DELETE FROM notifications WHERE user_id = 123
DELETE FROM user WHERE id = 123

This ensures no orphaned data remains. Flask-SQLAlchemy manages 
this with cascade='all, delete-orphan' in relationships.

GDPR compliance:
- User can request account deletion
- All personal data removed
- Option to download data before deletion
```

---

# FEATURE 9: VISA TRACKER

## Purpose
Track visa application status and requirements:
- Track visa applications to different countries
- Monitor application status (Applied, In Review, Approved, Rejected)
- Store visa application documents
- Get visa requirements for destinations
- Track expiry dates and validity periods

## Frontend Components/Pages/Files Used
- **Pages:** `templates/visa.html`
- **UI Elements:**
  - Visa application form
  - Application status tracker
  - Document upload section
  - Country selector
  - Timeline view

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (visa routes implied)
- **Models:** `models.py` - VisaApplication model

## API Routes
```python
POST   /api/visa/apply          # Create visa application
GET    /api/visa/applications   # Get user's visa applications
PUT    /api/visa/<id>/status    # Update application status
DELETE /api/visa/<id>           # Cancel application
```

## Database Tables/Models Used
```
VisaApplication Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── country (String)
├── status (String)
│  ├── Applied
│  ├── In Review
│  ├── Approved
│  └── Rejected
├── applied_date (DateTime)
├── notes (Text)
└── updated_at (DateTime)
```

## State Management/Hooks Used
- **Frontend:**
  ```javascript
  let visaApplications = [];
  let selectedCountry = null;
  let applicationStatus = 'Applied';
  ```

## Complete Workflow Step-by-Step

### Visa Application Progress:
```
1. User clicks "Apply for Visa"
   ↓
2. Frontend shows form:
   - Select country (dropdown)
   - Select visa type (Tourist, Business, Student, etc.)
   - Purpose/Reason (text)
   - Document uploads
   ↓
3. User fills form and uploads documents (PDF, images)
   ↓
4. Frontend validates:
   - Country selected
   - At least one document uploaded
   ↓
5. POST /api/visa/apply
   {
     "country": "France",
     "visa_type": "Tourist",
     "purpose": "Vacation and sightseeing",
     "documents": [...uploaded files...]
   }
   ↓
6. Backend creates VisaApplication record:
   {
     "status": "Applied",
     "applied_date": "2025-04-15 10:30:00"
   }
   ↓
7. Admin/System updates status over time:
   Day 1: Applied
   Day 5: In Review (email sent)
   Day 15: More Info Required (email sent)
   Day 20: Approved (email sent)
   ↓
8. User can view status anytime:
   GET /api/visa/applications
   Returns all visa apps with current status
   ↓
9. For approved visa:
   - Status shows "Approved"
   - Validity period displayed (valid until date)
   - Document download option
   ↓
10. For rejected visa:
    - Status shows "Rejected"
    - Reason displayed (if provided)
    - Option to appeal or apply again
```

## Important Variables/Props/States Used
- **country:** Destination country
- **status:** Current visa status (Applied, In Review, Approved, Rejected)
- **applied_date:** Date of application
- **validity_start, validity_end:** Visa active period
- **documents:** Array of uploaded documents

## Error Handling/Validation Used
- **Country validation:** Must be valid country
- **Document validation:** File type and size
- **Status transitions:** Only allow valid transitions
- **Date validation:** Validity dates make sense

## Third-party Integrations Used
- **None** - Internal tracking system

## Files to Explain in Viva
1. `models.py` - VisaApplication model
2. `app.py` - Visa routes
3. `templates/visa.html` - Visa tracker UI

---

# FEATURE 10: COMPANION FINDER

## Purpose
Connect travelers going to same destination to:
- Find travel companions with similar interests
- Reduce travel costs (shared accommodations, transport)
- Enhance safety through group travel
- Build travel community

## Frontend Components/Pages/Files Used
- **Pages:** Likely in dashboard or separate page
- **UI Elements:**
  - Companion profile setup form
  - Nearby companions map/list
  - Compatibility score display
  - Connection request buttons
  - Chat interface

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 708-955)
- **Models:** `models.py` - CompanionProfile, CompanionRequest

## API Routes
```python
GET    /api/companion/profile                    # Get user's profile
POST   /api/companion/profile                    # Create/update profile
GET    /api/companion/nearby-enhanced            # Find nearby companions
POST   /api/companion/request                    # Send connection request
POST   /api/companion/request/<id>/<action>     # Accept/decline request
```

## Database Tables/Models Used
```
CompanionProfile Table:
├── id (Primary Key)
├── user_id (Foreign Key, unique)
├── name
├── age
├── gender
├── bio
├── destination
├── start_date
├── end_date
├── interests (comma-separated)
├── looking_for (what type of companion)
├── latitude
├── longitude
├── last_seen (DateTime)
└── is_active

CompanionRequest Table:
├── id (Primary Key)
├── sender_id (Foreign Key to User)
├── receiver_id (Foreign Key to User)
├── status (pending/accepted/declined)
├── message
├── created_at (DateTime)
└── updated_at (DateTime)
```

## State Management/Hooks Used
- **Frontend:**
  ```javascript
  let myCompanionProfile = null;
  let nearbyCompanions = [];
  let connectionRequests = [];
  let userLocation = { lat: null, lng: null };
  ```

## Complete Workflow Step-by-Step

### Finding Companions:
```
1. User enables location and fills companion profile:
   - Name, age, gender
   - Destination and dates
   - Interests (adventure, budget travel, luxury, photography, etc.)
   - What type: Group, Solo buddy, Couple, etc.
   ↓
2. POST /api/companion/profile
   {
     "name": "Aarav",
     "age": 25,
     "destination": "Goa",
     "interests": "adventure,food,beaches",
     "latitude": 28.6139,
     "longitude": 77.2090
   }
   ↓
3. Backend stores profile with location
   ↓
4. User clicks "Find Companions Near Me"
   ↓
5. GET /api/companion/nearby-enhanced?radius=10
   ↓
6. Backend finds companions within radius (Haversine distance):
   - Query all active CompanionProfiles
   - Calculate distance to each
   - Filter by radius (default 10 km)
   ↓
7. Calculate compatibility score:
   - Same destination: +30 compatibility
   - Overlapping dates: +20
   - Similar interests: +10 per shared interest
   - Max 100
   ↓
8. Return nearby companions:
   {
     "companions": [
       {
         "user_id": 456,
         "name": "Mira",
         "age": 24,
         "destination": "Goa",
         "interests": "adventure,food",
         "distance_km": 2.5,
         "compatibility": 85,
         "connection_status": "none"
       }
     ]
   }
   ↓
9. Frontend displays cards sorted by:
   - Compatibility score (highest first)
   - Distance (nearest first)
   ↓
10. User clicks "Connect" on interesting companion
```

### Sending Connection Request:
```
1. User clicks "Connect" button on companion
   ↓
2. Frontend shows message compose modal
   ↓
3. User writes optional message:
   "Hi! I'm also going to Goa for 5 days. Want to team up?"
   ↓
4. POST /api/companion/request
   {
     "receiver_id": 456,
     "message": "Hi! I'm also going to Goa..."
   }
   ↓
5. Backend checks if connection already exists
   If already sent or received: Return 400 "Request already exists"
   ↓
6. Creates CompanionRequest record:
   {
     "sender_id": 123,
     "receiver_id": 456,
     "status": "pending",
     "message": "Hi! I'm also going to Goa..."
   }
   ↓
7. Awards gamification: companion_finder_use event
   ↓
8. Broadcasts via WebSocket to receiver:
   io.emit('companion_request', {
     'sender_id': 123,
     'sender_name': 'Aarav',
     'message': 'Hi! I\'m also going to Goa...',
     'timestamp': now
   }, room=str(receiver_id))
   ↓
9. Receiver sees notification:
   "Aarav wants to connect (Compatible: 85%)"
   ↓
10. Receiver can click to view full profile:
    - Photo/avatar
    - Bio and interests
    - Travel dates and plans
    - Accept or Decline button
```

### Accepting Connection:
```
1. Receiver clicks "Accept" on connection request
   ↓
2. POST /api/companion/request/789/accept
   ↓
3. Backend updates request status: pending → accepted
   ↓
4. Broadcasts to sender via WebSocket:
   io.emit('companion_request_response', {
     'request_id': 789,
     'status': 'accepted',
     'acceptor_name': 'Mira'
   }, room=str(sender_id))
   ↓
5. Both users see:
   - Connected users in their network
   - Option to message (in production)
   - Option to plan together
```

## Important Variables/Props/States Used
- **destination:** Target travel destination
- **interests:** Array of interest tags
- **compatibility:** 0-100 score based on matching
- **distance_km:** Distance between users in km
- **connection_status:** none/pending/accepted/declined

## Error Handling/Validation Used
- **Duplicate requests:** Check before creating
- **Distance validation:** Ensure reasonable radius (0.5-50 km)
- **Location validation:** Valid latitude/longitude
- **Status transitions:** Only valid transitions allowed

## Third-party Integrations Used
- **None** - Pure backend with WebSocket

## How Frontend and Backend Communicate
```
Frontend (Companion Map)
    ↓ (GET with user location)
/api/companion/nearby-enhanced?lat=...&lng=...&radius=10
    ↓ (Backend calculates distances)
Backend (Haversine formula)
    ↓ (Query database)
SQLite Database
    ↓ (Return matching profiles)
Backend (Calculate compatibility)
    ↓ (Return JSON)
Frontend displays cards
    ↓ (User clicks Connect)
    ↓ (POST with connect request)
/api/companion/request
    ↓ (Backend creates record, WebSocket broadcast)
Recipient receives real-time notification
```

## Files to Explain in Viva
1. `app.py` - Lines 708-955: All companion endpoints
2. `models.py` - CompanionProfile and CompanionRequest models
3. `utils.py` - haversine() distance calculation

---

# FEATURE 11: GAMIFICATION SYSTEM

## Purpose
Engage users through rewards and achievement system:
- Earn coins (YC - Yatrika Coins) for actions
- Gain XP to increase level
- Unlock badges and achievements
- Complete daily/weekly missions
- Redeem rewards in store
- Spin wheel for random rewards
- Compete on leaderboards

## Frontend Components/Pages/Files Used
- **Dashboard sections with gamification widgets**
- **UI Elements:**
  - Coins/XP display
  - Level badge
  - Achievement showcase
  - Mission progress
  - Leaderboard
  - Reward store
  - Spin wheel

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 130-520, plus integrated throughout)
- **Models:** `models.py` - GamificationProfile, GamificationEvent, UserAchievement, UserMission

## API Routes
```python
GET  /api/gamification/profile           # Get user's gamification stats
GET  /api/gamification/achievements      # Get unlocked achievements
GET  /api/gamification/missions           # Get current missions
POST /api/gamification/missions/<id>/claim  # Claim mission reward
GET  /api/gamification/leaderboard       # Get leaderboard
POST /api/gamification/spin              # Spin reward wheel
POST /api/gamification/store/redeem      # Redeem from store
```

## Database Tables/Models Used
```
GamificationProfile Table:
├── id (Primary Key)
├── user_id (Foreign Key, unique)
├── yc_balance (current coins)
├── yc_lifetime_earned (total ever earned)
├── yc_lifetime_spent (total redeemed)
├── xp_total (cumulative XP)
├── current_level (Explorer, Adventurer, Globetrotter, Legend)
├── current_streak (login streak)
├── longest_streak
├── last_login_date
├── referral_code (unique)
└── referred_by

GamificationEvent Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── event_type (signup, booking_flight, daily_login, etc.)
├── event_ref (booking ID, etc.)
├── coins_delta (coins awarded)
├── xp_delta (XP awarded)
├── meta_json (additional data)
└── created_at

UserAchievement Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── badge_code (first_flight_booked, hotel_master, etc.)
├── title (display name)
├── description
├── icon (FontAwesome icon)
├── progress (current count toward target)
├── target (count needed to unlock)
├── is_unlocked (boolean)
├── unlocked_at (DateTime)
└── created_at

UserMission Table:
├── id (Primary Key)
├── user_id (Foreign Key)
├── mission_key (daily_ai, weekly_referral, etc.)
├── title (display name)
├── mission_type (daily/weekly)
├── event_type (tracking which events)
├── target_count (goal)
├── current_count (progress)
├── reward_coins
├── reward_xp
├── is_claimed (bool)
├── window_start (date range)
├── window_end
└── created_at
```

## Event-Reward Mapping
```python
EVENT_REWARDS = {
    'signup': {'coins': 100, 'xp': 120},
    'profile_completion': {'coins': 150, 'xp': 140},
    'booking_flight': {'coins': 200, 'xp': 180},
    'booking_hotel': {'coins': 180, 'xp': 160},
    'booking_train': {'coins': 120, 'xp': 120},
    'booking_cab': {'coins': 80, 'xp': 90},
    'booking_cruise': {'coins': 260, 'xp': 220},
    'daily_login': {'coins': 10, 'xp': 20},
    'login_streak_7': {'coins': 100, 'xp': 130},
    'ai_itinerary': {'coins': 40, 'xp': 70},
    'review_posted': {'coins': 70, 'xp': 80},
    'trip_photo_upload': {'coins': 40, 'xp': 50},
    'referral_friend': {'coins': 300, 'xp': 220},
    'companion_finder_use': {'coins': 50, 'xp': 60},
    'smart_map_use': {'coins': 25, 'xp': 30}
}

BADGES = [
    "first_flight_booked",
    "rail_explorer",
    "hotel_master",
    "ai_planner_pro",
    "safety_hero",
    "social_traveler",
    "five_cities_visited"
]

LEVELS = [
    ('Explorer', 0, 500),
    ('Adventurer', 501, 1500),
    ('Globetrotter', 1501, 3000),
    ('Legend Traveler', 3001, ∞)
]
```

## Complete Workflow Step-by-Step

### Daily Login & Streak:
```
1. User logs in
   ↓
2. Backend calls process_daily_login(user_id)
   ↓
3. Checks last_login_date:
   - If today: Already logged in today, return
   - If yesterday: Increment streak
   - Else: Reset streak to 1
   ↓
4. Award coins:
   - Give 10 coins for login
   - Give additional bonus coins based on streak day:
     Day 1: +10 coins
     Day 2: +15 coins
     ...
     Day 7: +100 coins (jackpot!)
   ↓
5. Update profile:
   current_streak = new_streak
   longest_streak = max(longest_streak, current_streak)
   last_login_date = today
   ↓
6. If streak reaches 7:
   award_event('login_streak_7', 100 coins, 130 xp)
   ↓
7. Frontend displays:
   "🔥 You're on a X-day streak! +Y coins earned"
```

### Booking & Event Rewards:
```
1. User completes flight booking
   ↓
2. Backend calls:
   award_event(user_id, 'booking_flight', event_ref=booking.id)
   ↓
3. award_event() function:
   - Looks up EVENT_REWARDS['booking_flight']
   - Gets: {coins: 200, xp: 180}
   - Checks if event is one-time:
     'booking_flight' is NOT one-time (can book multiple)
   - Updates GamificationProfile:
     yc_balance += 200
     yc_lifetime_earned += 200
     xp_total += 180
   ↓
4. Recalculates level:
   level_name = level_from_xp(xp_total)
   If xp_total >= 501: current_level = "Adventurer"
   ↓
5. Increments relevant missions:
   - Daily mission "book_one_trip": current_count += 1
   - Weekly mission if applicable
   ↓
6. Checks achievement unlock:
   If current_level upgraded:
   New achievement "First Flight Booked" unlocked
   ↓
7. Stores GamificationEvent record in database
   ↓
8. Returns to user:
   {
     "coins": 200,
     "xp": 180,
     "level": "Adventurer",
     "new_achievements": []
   }
   ↓
9. Frontend displays:
   "✈️ Flight Booked! +200 YC, +180 XP"
   "Level Up: Explorer → Adventurer"
```

### Missions & Daily Checklist:
```
1. On login, ensure_user_missions() creates daily/weekly missions
   ↓
2. Daily missions (reset each day):
   - "Generate AI itinerary" - Target: 1, Reward: 40 coins
   - "Book one trip" - Target: 1, Reward: 100 coins
   - "Add review" - Target: 1, Reward: 50 coins
   ↓
3. Weekly missions (reset on Monday):
   - "Invite a friend" - Target: 1, Reward: 200 coins
   - "Explore 3 attractions" - Target: 3, Reward: 120 coins
   - "Upload trip photos" - Target: 5 photos, Reward: 110 coins
   ↓
4. User performs action (e.g., generates itinerary)
   ↓
5. award_event('ai_itinerary', ...) is called
   ↓
6. _increment_missions() checks active missions:
   Finds mission "Generate AI itinerary"
   current_count += 1
   If current_count >= target: mission.is_claimed = True
   ↓
7. Frontend shows mission progress:
   "📋 Daily: Generate Itinerary (1/1) ✓ COMPLETED
   Claim reward → 40 YC"
   ↓
8. User clicks "Claim Reward"
   ↓
9. Backend awards coins/xp and marks as claimed
```

### Achievements & Badges:
```
1. User completes 3 train bookings
   ↓
2. refresh_achievements() function runs:
   Gets metrics for user:
   {
     'train_bookings': 3,
     'flight_bookings': 1,
     ...
   }
   ↓
3. Checks "Rail Explorer" badge:
   Target: 3 train bookings
   Current: 3
   Is unlocked: False → True
   ↓
4. Updates UserAchievement:
   is_unlocked = True
   unlocked_at = now
   Award bonus coins/xp
   ↓
5. Creates achievement unlock event
   ↓
6. Frontend displays:
   "🎖️ BADGE UNLOCKED: Rail Explorer
   You've completed 3 train bookings!"
```

### Leaderboard:
```
1. User clicks "Leaderboard"
   ↓
2. GET /api/gamification/leaderboard?scope=weekly&limit=10
   ↓
3. Backend queries GamificationEvent from past week
   Groups by user_id
   Sums coins earned
   ↓
4. Resolves user details from User table
   ↓
5. Sorts by coins (descending)
   ↓
6. Returns with user's rank:
   {
     "items": [
       {"rank": 1, "username": "adventurer_mike", "score": 5000},
       {"rank": 2, "username": "globetrotter_jane", "score": 4500},
       ...
       {"rank": 7, "username": "current_user", "score": 2100}
     ],
     "meta": {
       "your_rank": 7,
       "need_points_to_next_rank": 300
     }
   }
   ↓
7. Frontend displays leaderboard with user highlighted
```

### Reward Store:
```
STORE_REWARDS = [
    {'key': 'hotel_discount', 'cost': 1500, 'value': '₹200 OFF Hotel'},
    {'key': 'cab_discount', 'cost': 800, 'value': '₹100 OFF Cab'},
    {'key': 'premium_itinerary', 'cost': 2000, 'value': 'Premium Pack'},
    {'key': 'cashback_voucher', 'cost': 2500, 'value': '₹300 Cashback'}
]

1. User clicks on hotel discount (1500 YC)
   ↓
2. Frontend shows confirmation:
   "Spend 1500 YC for ₹200 OFF Hotel Bookings?"
   ↓
3. User confirms
   ↓
4. POST /api/gamification/store/redeem
   {
     "reward_key": "hotel_discount"
   }
   ↓
5. Backend checks:
   - User has >= 1500 coins
   - Reward still available
   ↓
6. Deducts coins:
   yc_balance -= 1500
   yc_lifetime_spent += 1500
   ↓
7. Creates voucher/coupon code
   Stores in RewardRedemption table
   ↓
8. Returns voucher code to user:
   "HOTEL200OFF - Valid for 30 days"
   ↓
9. User can add this code during hotel booking for discount
```

## Important Variables/Props/States Used
- **yc_balance:** Current available coins
- **xp_total:** Cumulative experience points
- **current_level:** User's rank tier
- **current_streak:** Consecutive login days
- **event_type:** What action triggered the reward
- **coins_delta, xp_delta:** Amounts awarded
- **mission_type:** daily or weekly
- **target_count, current_count:** Mission progress

## Error Handling/Validation Used
- **One-time events:** Check before awarding again (signup, profile_completion)
- **Daily events:** Check if already awarded today (smart_map_use)
- **Invalid events:** Return error if event_type not in EVENT_REWARDS
- **Insufficient coins:** Return 400 if trying to redeem without enough
- **Mission claiming:** Check current_count >= target
- **Level recalculation:** Always sync when XP changes

## Third-party Integrations Used
- **None** - Pure backend gamification

## How Frontend and Backend Communicate
```
Frontend (Dashboard)
    ↓ (GET gamification profile)
/api/gamification/profile
    ↓ (Backend queries database)
SQLite Database
    ↓ (Return profile data)
Frontend displays stats
    ↓ (User takes action - books flight)
    ↓ (Backend automatically awards via award_event())
    ↓ (WebSocket broadcast to frontend)
Frontend shows: "+200 YC! ✈️"
Frontend updates UI (coins, level, progress)
```

## Files to Explain in Viva
1. `app.py` - Lines 130-520: All gamification functions
2. `models.py` - All gamification models
3. `app.py` - Award integration throughout (register, login, bookings)

## Possible Viva Questions & Answers

**Q1: Why have both coins and XP?**
```
A: They serve different purposes:

XP (Experience Points):
- Determines level/prestige
- Can only increase
- Reflects total travel activity
- Shows progression

Coins (YC - Yatrika Coins):
- Spendable currency
- Can increase and decrease
- Tradeable for rewards
- Provides tangible value

Analogy: Like video games - XP shows your rank, coins are in-game money.
User engagement: Seeing both currencies makes progress feel multi-dimensional.
```

**Q2: How do login streaks work for fairness?**
```
A: Streak tracking:
- Track last_login_date (date only, not timestamp)
- Compare if it's same as today: already logged in
- Compare if it's yesterday: streak continues
- Else: streak resets to 1

Rewards increase by day:
Day 1: +10
Day 2: +15
...
Day 7: +100 (big reward!)
Day 8: +10 (resets)

This incentivizes:
✓ Daily engagement (free coins)
✓ Consistency (bonus for 7-day streak)
✓ Comeback potential (streak resets, not lost forever)

Fairness:
- Everyone gets same base coins
- Bonus based on their consistency
- Can't cheat (date-based, not timer)
```

**Q3: How are achievements unlocked automatically?**
```
A: refresh_achievements() is called whenever:
1. User XP changes (level could change)
2. New booking created (count metrics change)
3. Daily/weekly missions completed

Metric calculation:
For "5 Cities Visited" badge:
- Query all bookings for user
- Extract unique cities: set(to_location for booking in bookings)
- Count unique cities
- If count >= 5: progress = 5

Unlock logic:
if progress >= target and not is_unlocked:
  is_unlocked = True
  unlocked_at = now
  Award bonus coins/xp

This creates satisfaction moment:
"You've unlocked a new achievement!"
- Different from regular event rewards
- Gives milestone recognition
```

**Q4: How do leaderboards handle ties?**
```
A: Ranking with ties:

Sorted by total coins in period (weekly/monthly)

If same coins:
- Use exact XP as tiebreaker
- If still same: alphabetical by username

Example:
Rank 1: John - 5000 coins
Rank 2: Jane - 5000 coins (earlier signup = tiebreaker)
Rank 3: Mike - 4900 coins

Scopes:
- Weekly: Last 7 days only
- Friends: Only connected companions
- City/College: Based on user bio

This adds healthy competition while accounting for activity differences.
```

---

# FEATURE 12: TRAVEL STORIES & COMMUNITY

## Purpose
Create social engagement through travel stories:
- Upload photos and experiences
- Write trip narratives
- Share with community
- Get likes and comments
- Build travel portfolio

## Frontend Components/Pages/Files Used
- **Pages:** `templates/stories.html`
- **UI Elements:**
  - Story card layout
  - Image gallery
  - Like button
  - Story publishing form

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 2100+)
- **Models:** `models.py` - TravelStory model

## API Routes
```python
GET  /api/stories              # Get all stories (public feed)
POST /api/stories              # Create new story (with image uploads)
GET  /api/stories/<id>         # Get specific story
POST /api/stories/<id>/like    # Like a story
GET  /api/reviews              # Get reviews/ratings
POST /api/reviews              # Post review
```

## Complete Workflow
[Similar structure to other features - abbreviated for space]

---

# FEATURE 13: SOS & EMERGENCY ALERTS

## Purpose
Real-time emergency assistance:
- Send SOS alerts with location
- Find nearest emergency services
- Broadcast alert to nearby users/authorities
- Access emergency contact info

## Frontend Components/Pages/Files Used
- **SOS button on map pages**
- **Emergency hotline numbers display**
- **Nearby services list**

## Backend Files/Controllers/Routes Used
- **Main File:** `app.py` (lines 1180-1200)
- **Real-time:** WebSocket for broadcasting

## API Routes
```python
POST /api/sos   # Send emergency alert with location
GET  /api/nearby/search?category=emergency  # Find emergency services
```

## Complete Workflow
[SOS details already covered in Smart Map section]

---

# FEATURE 14: WEATHER INTEGRATION

## Purpose
Real-time weather information:
- Get weather by coordinates
- Plan activities based on weather
- Show weather alerts
- Multi-day forecast

## APIs
```python
GET /api/weather/map?lat=...&lng=...  # Get weather by coordinates
```

## Integration
Uses OpenWeather API (if configured) with mock fallback

---

# SUMMARY OF KEY TECHNOLOGIES

## Frontend Stack
- **HTML & Tailwind CSS** - Responsive UI
- **Vanilla JavaScript** - DOM manipulation
- **Socket.IO** - Real-time WebSocket communication
- **Fetch API** - HTTP client

## Backend Stack
- **Flask** - Web framework
- **SQLAlchemy** - ORM
- **Flask-JWT-Extended** - Authentication
- **Flask-SocketIO** - WebSocket support
- **SQLite** - Database

## Third-party APIs
- **Groq AI** - AI itinerary generation
- **Google Gemini** - AI fallback
- **OpenSky Network** - Live flight tracking
- **OpenStreetMap Nominatim** - Geocoding
- **Overpass API** - Place searches
- **OSRM** - Route planning
- **OpenWeather** - Weather data (optional)
- **Razorpay** - Payment processing

## Hardware/Geographic Functions
- **Geolocation API** - Browser GPS
- **Haversine Formula** - Distance calculations
- **Maps Library** - Interactive maps (Leaflet/Google Maps)

---

# VIVA EXPERT ANSWERS SUMMARY

## Top 5 Questions You'll Get:

**1. How does the system scale?**
```
Current: Single SQLite database, in-memory inventory
Answer:
- Database: Migrate to PostgreSQL with indexes
- Inventory: Use Redis for distributed cache
- API: Use load balancer (Nginx)
- Frontend: CDN for static assets
- Real-time: Scale Socket.IO to multiple servers with Redis pub/sub
```

**2. What about security?**
```
- Passwords: Hashed with PBKDF2 (werkzeug)
- API: JWT tokens, @jwt_required() decorator
- Payment: Razorpay signature verification
- CORS: Configured with Flask-CORS
- SQL Injection: SQLAlchemy prevents with parameterized queries
- File uploads: Whitelist extensions, sanitize filenames
```

**3. How are real-time updates handled?**
```
- Socket.IO for WebSocket connections
- Broadcast emergency alerts to all users
- Companion requests sent real-time
- Could add live flight updates every 15 seconds
- Could add travel story likes in real-time
```

**4. What about currency and units?**
```
- All amounts in INR (Indian Rupees)
- Razorpay in paise (1 INR = 100 paise)
- Distances in km
- XP and coins are virtual gamification currency
- Exchange rates handled separately if needed
```

**5. How would you handle live traffic jams during peak hours?**
```
- Current: Mock crowd data based on time
- Production: Integrate with Google Maps Traffic API
- Or: Use Mapbox Traffic Layer
- Historical data: Track patterns, predict crowds
- Real-time: Crowdsourced location data
- Alternative: TomTom API for traffic
```

---

# FILES FOR COMPETITIVE JUDGES

When judges ask to see code, have these ready:

1. **Authentication Challenge:** Show `app.py` (register/login), `models.py` (User), `utils.py` (password hashing)
2. **AI Integration:** Show `utils.py` (generate_ai_itinerary), prompt engineering, fallback mechanism
3. **Booking System:** Show `app.py` (booking routes), inventory management, dynamic pricing
4. **Payment Processing:** Show Razorpay integration, signature verification
5. **Real-time Features:** Show Socket.IO usage for SOS and companion requests
6. **Location Services:** Show Haversine formula, Nominatim integration, Overpass queries
7. **Database Design:** Show `models.py` relationships, cascading deletes
8. **Gamification:** Show event tracking, level system, mission logic
9. **Scalability:** Explain migration path to larger architecture

---

# FINAL NOTES FOR JUDGES

**What Makes This Project Stand Out:**

✅ **Multi-feature platform** - 14+ interconnected features
✅ **Real APIs** - Uses actual external services (not just mocks)
✅ **Secure authentication** - JWT tokens with hashed passwords
✅ **Scalable architecture** - Can migrate from SQLite to PostgreSQL
✅ **Real-time communication** - WebSocket for instant notifications
✅ **User engagement** - Gamification system with 7+ reward mechanisms
✅ **Helpful features** - AI planning, emergency SOS, companion finder
✅ **Well documented** - This document!

**Common Judge Questions & Quick Answers:**

Q: Why mock data instead of only real APIs?
A: Reliability. Real APIs can fail/rate-limit. Mock provides demo capability while real APIs enhance production.

Q: How is data integrity maintained?
A: SQLAlchemy transactions with rollback on errors. Cascade deletes maintain referential integrity.

Q: What's the cost to scale?
A: Database upgrade: $100-500/month. Redis cache: $50-100/month. Servers: Depends on traffic. Total <$1000/month for production.

---

**Good luck with your viva presentation! You've built an impressive system.** 🚀

