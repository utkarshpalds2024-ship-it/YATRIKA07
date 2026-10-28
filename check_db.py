from app import app, db
from models import User

with app.app_context():
    db.create_all()
    print("✅ Tables created/verified")
    # Check if any user exists
    user = User.query.first()
    print(f"Existing user: {user.username if user else 'None'}")