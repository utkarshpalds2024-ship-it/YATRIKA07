import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from extensions import db
from models import CompanionProfile, CompanionRequest

def reset_tables():
    with app.app_context():
        print("⚠️  Dropping companion tables...")
        # Drop tables if they exist
        db.drop_all()
        print("✅ Tables dropped!")
        
        print("📦 Creating fresh tables...")
        db.create_all()
        print("✅ Tables created successfully!")
        
        # Verify columns
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('companion_profiles')]
        print(f"\nColumns in companion_profiles: {', '.join(columns)}")
        
        expected = ['id', 'user_id', 'name', 'age', 'gender', 'bio', 'destination', 
                    'start_date', 'end_date', 'interests', 'looking_for', 
                    'latitude', 'longitude', 'last_seen', 'is_active']
        missing = set(expected) - set(columns)
        if missing:
            print(f"❌ Missing columns: {missing}")
        else:
            print("✅ All expected columns present!")

if __name__ == '__main__':
    reset_tables()