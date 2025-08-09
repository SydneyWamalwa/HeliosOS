import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from config import config_by_name

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Flask-Limiter now requires key_func at initialization in v3+
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__,
                static_folder="static",
                template_folder="templates")

    # Load configuration
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Enable CORS for development
    if config_name == 'development':
        CORS(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Error handlers
    register_error_handlers(app)

    return app

def setup_logging(app):
    """Setup logging to a file if not in debug or testing mode."""
    if not app.debug and not app.testing:
        handler = logging.FileHandler(app.config['LOG_FILE'])
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))

def register_error_handlers(app):
    """Register custom error handlers."""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(429)
    def rate_limit_handler(e):
        return {'error': 'Rate limit exceeded'}, 429
