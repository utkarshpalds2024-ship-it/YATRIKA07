#!/usr/bin/env python3
"""Test Flask weather endpoints directly"""
import requests
import time

print("🔍 Testing Flask Weather Endpoints\n")
print("="*60)

# Give Flask a moment to start if needed
base_url = "http://localhost:5000"

# Test 1: City-based weather
print("\n📍 TEST 1: City Search Weather")
print("-" * 60)
try:
    url = f"{base_url}/api/weather?city=Thane"
    print(f"URL: {url}")
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        print(f"✅ SUCCESS!")
        print(f"   City: {data.get('city')}")
        print(f"   Temperature: {data.get('temperature')}°C")
        print(f"   Description: {data.get('description')}")
        print(f"   Humidity: {data.get('humidity')}%")
        print(f"   Alerts: {len(data.get('alerts', []))} alerts found")
    else:
        print(f"❌ FAILED: {data}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    print("   Make sure Flask is running on port 5000!")

# Test 2: Map weather
print("\n🗺️  TEST 2: Map Coordinates Weather")
print("-" * 60)
try:
    # Thane coordinates
    url = f"{base_url}/api/weather/map?lat=19.2183&lng=72.9781"
    print(f"URL: {url}")
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if response.status_code == 200:
        print(f"✅ SUCCESS!")
        print(f"   City: {data.get('city')}")
        print(f"   Temperature: {data.get('temp')}°C")
        print(f"   Description: {data.get('description')}")
        print(f"   Humidity: {data.get('humidity')}%")
    else:
        print(f"❌ FAILED: {data}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    print("   Make sure Flask is running on port 5000!")

print("\n" + "="*60)
print("✅ Endpoint tests completed!")
