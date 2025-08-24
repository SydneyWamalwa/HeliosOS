#!/usr/bin/env python3
"""
HeliosOS - Complete Startup Script
Run this to start the full HeliosOS environment
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('HeliosOS')

def setup_database():
    """Initialize the database with default data"""
    try:
        # Import db from extensions to avoid circular imports
        from app.extensions import db

        # Create default admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@heliosos.com',
                is_admin=True,
                is_active=True,
                profile={
                    'user_type': 'business',
                    'display_name': 'Administrator',
                    'preferences': {
                        'theme': 'dark',
                        'notifications': True,
                        'auto_suggestions': True
                    }
                }
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)

        # Create demo user if it doesn't exist
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            demo_user = User(
                username='demo',
                email='demo@heliosos.com',
                is_admin=False,
                is_active=True,
                profile={
                    'user_type': 'casual',
                    'display_name': 'Demo User',
                    'preferences': {
                        'theme': 'dark',
                        'notifications': True,
                        'auto_suggestions': True
                    }
                }
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)

        db.session.commit()
        logger.info("Database setup completed successfully")

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        db.session.rollback()

def check_docker():
    """Check if Docker is available for application management"""
    try:
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info(f"Docker available: {result.stdout.strip()}")
            return True
        else:
            logger.warning("Docker not available - application management will use fallback mode")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("Docker not found - application management will use fallback mode")
        return False

def start_background_services():
    """Start background services needed for HeliosOS"""

    def start_application_manager():
        """Initialize application manager"""
        try:
            from app.application_manager import application_manager
            logger.info("Application manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize application manager: {e}")

    def start_ai_services():
        """Initialize AI services"""
        try:
            from app.ai_client import get_ai_service
            from app.enhanced_ai_client import enhanced_ai_client

            # Test AI services
            ai_service = get_ai_service()
            health = ai_service.health_check()
            logger.info(f"AI services health: {health.get('status', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}")

    def start_workflow_engine():
        """Initialize workflow engine"""
        try:
            from app.workflow_engine import workflow_engine
            logger.info("Workflow engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize workflow engine: {e}")

    # Start services in background threads
    threading.Thread(target=start_application_manager, daemon=True).start()
    threading.Thread(target=start_ai_services, daemon=True).start()
    threading.Thread(target=start_workflow_engine, daemon=True).start()

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'app/static/uploads',
        'tmp',
        'data'
    ]

    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except PermissionError as e:
            logger.warning(f"Could not create directory {directory}: {e}")
            # Try to create in a different location if needed
            if 'static' in directory:
                alt_directory = directory.replace('static', 'uploads')
                try:
                    Path(alt_directory).mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created alternative directory: {alt_directory}")
                except Exception as alt_e:
                    logger.warning(f"Could not create alternative directory: {alt_e}")
        except Exception as e:
            logger.warning(f"Could not create directory {directory}: {e}")

def print_startup_info():
    """Print startup information"""
    print("\n" + "="*60)
    print("🌞 HeliosOS - AI-Powered Operating System")
    print("="*60)
    print(f"🚀 Starting HeliosOS environment...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    print("="*60)

def print_access_info(host='localhost', port=5000):
    """Print access information"""
    print("\n" + "="*60)
    print("✅ HeliosOS is ready!")
    print("="*60)
    print(f"🌐 Web Interface: http://{host}:5001")
    print(f"🤖 AI Assistant: Leo is ready to help")
    print(f"🖥️  Desktop Environment: Available via web interface")
    print(f"🔧 Application Manager: Ready to launch apps")
    print("\n📝 Default Login Credentials:")
    print("   Admin: admin / admin123")
    print("   Demo:  demo / demo123")
    print("="*60)
    print("💡 Try these commands to Leo:")
    print("   • 'open firefox' - Launch Firefox browser")
    print("   • 'show system status' - View system information")
    print("   • 'list applications' - See available apps")
    print("   • 'run morning routine' - Execute workflow")
    print("="*60)

def main():
    """Main startup function"""
    print_startup_info()

    # Set up environment
    os.environ.setdefault('FLASK_APP', 'app:create_app()')
    os.environ.setdefault('FLASK_ENV', 'development')

    # Create necessary directories
    create_directories()

    # Check Docker availability
    docker_available = check_docker()

    # Create Flask app
    app = create_app()

    # Setup database within app context
    with app.app_context():
        setup_database()

        # Start background services
        start_background_services()

        # Wait a moment for services to initialize
        time.sleep(2)

        logger.info("All services initialized successfully")

    # Print access information
    print_access_info()

    try:
        # Start the Flask development server
        app.run(
            host='0.0.0.0',
            port=5003,
            debug=True,
            use_reloader=False,  # Disable reloader to prevent service restart
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 HeliosOS shutdown initiated...")
        logger.info("HeliosOS shutdown completed")
    except Exception as e:
        logger.error(f"Failed to start HeliosOS: {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())