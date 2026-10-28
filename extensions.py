from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
# Use threading mode for Python 3.13 compatibility
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
jwt = JWTManager()