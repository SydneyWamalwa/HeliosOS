#!/usr/bin/env python3
"""
WSGI entry point for HeliosOS
This file is used by production WSGI servers like Gunicorn
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set environment variables
os.environ.setdefault('FLASK_ENV', 'production')

# Import and create the Flask application
from app import create_app, db
from app.models import User

def create_application():
    """Create and configure the WSGI application"""
    app = create_app()

    # Initialize database and default users
    with app.app_context():
        try:
            # Create tables
            db.create_all()

            # Create default users if they don't exist
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@heliosos.com',
                    is_admin=True,
                    is_active=True,
                    profile={
                        'user_type': 'business',
                        'display_name': 'Administrator'
                    }
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)

                demo_user = User(
                    username='demo',
                    email='demo@heliosos.com',
                    is_admin=False,
                    is_active=True,
                    profile={
                        'user_type': 'casual',
                        'display_name': 'Demo User'
                    }
                )
                demo_user.set_password('demo123')
                db.session.add(demo_user)

                db.session.commit()
                print("✅ Default users created")

        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")
            db.session.rollback()

    return app

# Create the WSGI application
application = create_application()

# For debugging
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000, debug=True)