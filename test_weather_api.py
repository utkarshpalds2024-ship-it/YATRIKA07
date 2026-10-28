#!/usr/bin/env python3
"""Test weather API endpoints"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('Open_weather')
print(f"API Key loaded: {api_key[:10]}..." if api_key else "❌ No API key found!")

# Test 1: City-based weather
print("\n" + "="*60)
print("TEST 1: City-based weather (/api/weather)")
print("="*60)
try:
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Thane&appid={api_key}&units=metric"
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    data = response.json()
    if response.status_code == 200:
        print(f"✅ City: {data.get('name')}")
        print(f"✅ Temperature: {data.get('main', {}).get('temp')}°C")
        print(f"✅ Description: {data.get('weather', [{}])[0].get('main')}")
    else:
        print(f"❌ Error: {data}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Coordinate-based weather
print("\n" + "="*60)
print("TEST 2: Coordinate-based weather (/api/weather/map)")
print("="*60)
try:
    # Thane coordinates: 19.2183, 72.9781
    url = f"https://api.openweathermap.org/data/2.5/weather?lat=19.2183&lon=72.9781&appid={api_key}&units=metric"
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    data = response.json()
    if response.status_code == 200:
        print(f"✅ City: {data.get('name')}")
        print(f"✅ Temperature: {data.get('main', {}).get('temp')}°C")
        print(f"✅ Description: {data.get('weather', [{}])[0].get('main')}")
    else:
        print(f"❌ Error: {data}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*60)
print("✅ API tests completed!")
print("="*60)
