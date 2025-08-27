import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import extensions from extensions module
from app.extensions import db, migrate, login_manager, limiter

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///helios.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # AI Service Configuration
    app.config['HUGGINGFACE_API_KEY'] = os.environ.get('HUGGINGFACE_API_KEY', '')
    app.config['SUMMARY_MODEL'] = os.environ.get('SUMMARY_MODEL', 'facebook/bart-large-cnn')
    app.config['CHAT_MODEL'] = os.environ.get('CHAT_MODEL', 'facebook/blenderbot-400M-distill')
    app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    from datetime import timedelta
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    # Logging configuration
    app.config['LOG_FILE'] = os.environ.get('LOG_FILE', 'helios.log')
    app.config['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    login_manager.init_app(app)

    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Enable CORS for development
    if config_name == 'development':
        CORS(app)

    # Setup logging
    setup_logging(app)

    # Import and register blueprints
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.enhanced_routes import enhanced_bp
    from app.enhanced_routes_v2 import enhanced_v2_bp
    from app.routes_health import health_bp
    
    # Try to import full AI routes, fallback to basic ones if dependencies missing
    try:
        from app.enhanced_ai_routes import register_enhanced_ai_routes
        register_enhanced_ai_routes(app)
        app.logger.info("Full AI routes registered")
    except ImportError as e:
        app.logger.warning(f"Full AI routes not available ({str(e)}), using fallback")
        from app.enhanced_ai_routes_fallback import register_fallback_ai_routes
        register_fallback_ai_routes(app)
        app.logger.info("Fallback AI routes registered")

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(enhanced_bp)
    app.register_blueprint(enhanced_v2_bp)
    app.register_blueprint(health_bp)

    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)

    # Register error handlers
    register_error_handlers(app)

    # Create database tables and initialize system
    with app.app_context():
        try:
            # Import all models to ensure they're registered
            from app.models import User, CommandAudit, AIInteraction, UserSession
            db.create_all()
            app.logger.info('Database tables created successfully')

            # Initialize background services
            initialize_background_services(app)

        except Exception as e:
            app.logger.error(f'Failed to create database tables: {e}')

    return app

def setup_logging(app):
    """Setup logging to a file if not in debug or testing mode."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = logging.FileHandler(f'logs/{app.config["LOG_FILE"]}')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))

def initialize_background_services(app):
    """Initialize background services for HeliosOS."""
    try:
        # Initialize AI services
        from app.ai_client import get_ai_service
        ai_service = get_ai_service()
        app.logger.info('AI services initialized')

        # Initialize application manager
        from app.application_manager import application_manager
        app.logger.info('Application manager initialized')

        # Initialize workflow engine
        from app.workflow_engine import workflow_engine
        app.logger.info('Workflow engine initialized')

        # Initialize enhanced AI client
        from app.enhanced_ai_client import enhanced_ai_client
        app.logger.info('Enhanced AI client initialized')

        # Try to initialize full AI modules, fallback to basic ones if dependencies missing
        try:
            from app.ai_action_automation import get_automation_system
            from app.ai_content_processor import get_content_processor
            from app.ai_innovative_features import get_innovative_features
            
            automation_system = get_automation_system()
            content_processor = get_content_processor()
            innovative_features = get_innovative_features()
            
            app.logger.info('Full AI modules initialized')
        except ImportError as e:
            app.logger.warning(f'Full AI modules not available ({str(e)}), using fallback')
            from app.ai_fallback_modules import (
                get_automation_system, 
                get_content_processor, 
                get_innovative_features
            )
            
            automation_system = get_automation_system()
            content_processor = get_content_processor()
            innovative_features = get_innovative_features()
            
            app.logger.info('Fallback AI modules initialized')

    except Exception as e:
        app.logger.error(f'Failed to initialize background services: {e}')

def register_error_handlers(app):
    """Register custom error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal server error: {error}')
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(429)
    def rate_limit_handler(e):
        return {'error': f'Rate limit exceeded: {e.description}'}, 429

    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden'}, 403