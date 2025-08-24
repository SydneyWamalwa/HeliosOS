"""
Extensions module for Flask extensions
This module defines Flask extensions that are shared across the application
to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_cors import CORS

# Initialize extensions - SINGLE INSTANCES ONLY
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Flask-Limiter (can set Redis/Memcached storage for production)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)