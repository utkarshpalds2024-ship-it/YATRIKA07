import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models import (
    User, Trip, Booking, Review, TravelStory,
    Wishlist, Notification, Expense, VisaApplication, Place,
    CompanionProfile, CompanionRequest
)

def setup_database():
    with app.app_context():
        print("📦 Creating database tables...")
        db.create_all()
        print("✅ All tables created successfully!")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n📋 Tables in database: {', '.join(tables)}")
        
        # Verify companion tables
        if 'companion_profiles' in tables:
            print("✅ CompanionProfile table created")
        else:
            print("❌ CompanionProfile table not found")
            
        if 'companion_requests' in tables:
            print("✅ CompanionRequest table created")
        else:
            print("❌ CompanionRequest table not found")

if __name__ == '__main__':
    setup_database()