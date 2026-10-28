# OpenWeather API Integration - Visa Services

## Overview
Real-time weather data integration has been added to the Visa Services page. When users select a destination country from the dropdown, live weather data is fetched and displayed with intelligent travel alerts.

## Features Implemented

### 1. **Backend Weather API Endpoint** (`/api/weather`)
- **Location**: `app.py` (Flask route)
- **Endpoint**: `GET /api/weather?city={city_name}`
- **API Used**: OpenWeatherMap API
- **Returns**: 
  - Temperature, feels-like temperature
  - Humidity, pressure, wind speed
  - Visibility, UV index
  - Weather description and icon
  - **Custom travel alerts** based on conditions

### 2. **Intelligent Travel Alerts**
The API generates automatic alerts for:
- 🌧️ **Rain Alert**: Heavy rainfall warning with cautions
- ⚡ **Thunderstorm Alert**: Severe weather warning (DANGER level)
- ❄️ **Snow Alert**: Winter conditions and travel hazards
- 🔥 **Extreme Heat Alert**: Temperatures > 40°C (DANGER level)
- ☀️ **High Temperature Alert**: Temperatures 35-40°C (WARNING level)
- 🥶 **Cold Alert**: Freezing temperatures < 0°C
- 💨 **Strong Wind Alert**: Wind speeds > 40 km/h
- 🌫️ **Fog Alert**: Low visibility < 1 km

### 3. **Frontend Weather Display Card**
**Location**: `templates/visa.html`

**Components**:
- Weather icon (from OpenWeatherMap)
- Current temperature and "feels like" temperature
- Wind speed and humidity
- Weather description
- Dynamic travel alerts with color-coded severity levels
- Green checkmark if weather conditions are good for travel

**UI Features**:
- Smooth animations on display
- Color-coded severity indicators:
  - 🟢 Green (Safe): Good travel conditions
  - 🟠 Orange (Warning): Caution advised
  - 🔴 Red (Danger): Avoid outdoor activities
- Responsive design for all screen sizes
- Icons and emojis for quick visual recognition

## How to Use

### From User Perspective:
1. Navigate to the Visa Services page (`/visa`)
2. In the "Visa Requirement Checker" section, select a destination country
3. Weather data automatically fetches and displays above the "Check Requirements" button
4. Review temperature, wind, humidity, and travel alerts
5. Plan your trip based on the weather conditions

### Country-to-City Mapping:
The system maps countries to major capital/tourist cities for weather data:
- USA → New York
- UK → London
- France → Paris
- Germany → Berlin
- Italy → Rome
- Spain → Barcelona
- Australia → Sydney
- Canada → Toronto
- Japan → Tokyo
- Singapore → Singapore
- Thailand → Bangkok
- Malaysia → Kuala Lumpur
- UAE → Dubai
- Turkey → Istanbul
- Egypt → Cairo
- India → New Delhi

## API Key Configuration

**API Key Source**: `.env` file
**Variable**: `Open_weather=0324c349470cf54fbe4517c365bb6503`

The API key is automatically loaded from the `.env` file on app startup.

## Technical Stack

### Backend
- **Framework**: Flask
- **API Integration**: OpenWeatherMap API v2.5
- **Request Library**: Python `requests`
- **Response Format**: JSON

### Frontend
- **Fetch Method**: JavaScript Fetch API (Async/Await)
- **Styling**: Inline CSS with gradient backgrounds
- **Icons**: FontAwesome + Custom Emojis

## Error Handling

The integration includes robust error handling:
- **City not found**: Weather card hides gracefully
- **API timeout**: Fallback to hide weather display
- **Network errors**: Console logging without page breaks
- **Missing API key**: Returns 500 error (alerts developer)

## Future Enhancements

Potential improvements for v2.0:
- [ ] 5-day weather forecast
- [ ] Travel recommendation based on weather
- [ ] Weather alert notifications/emails
- [ ] Air quality index (AQI) data
- [ ] UV index warnings
- [ ] Pollen allergy alerts
- [ ] Multiple city weather comparison
- [ ] Weather-based travel insurance recommendations

## API Response Example

```json
{
  "city": "Paris",
  "country": "FR",
  "temperature": 15,
  "feels_like": 13,
  "humidity": 65,
  "pressure": 1013,
  "description": "Rainy",
  "wind_speed": 18.5,
  "clouds": 80,
  "visibility": 8.5,
  "uvi": 2,
  "icon": "10d",
  "alerts": [
    {
      "type": "rain",
      "message": "Heavy rainfall expected. Bring an umbrella and be cautious on wet roads.",
      "icon": "🌧️",
      "severity": "warning"
    }
  ],
  "has_alerts": true
}
```

## Debugging

### Check Weather Data:
```javascript
// In browser console:
fetch('/api/weather?city=Paris').then(r => r.json()).then(d => console.log(d))
```

### View Endpoint:
- Test endpoint: `http://localhost:5000/api/weather?city=Dubai`
- Expected: Returns JSON with weather data or error message

## Credits
- **Weather Data**: OpenWeatherMap (https://openweathermap.org/)
- **Icons**: FontAwesome & OpenWeather Icons
- **Integration**: YATRIKA Travel Platform
