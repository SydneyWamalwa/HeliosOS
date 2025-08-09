import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
import jwt
from flask import current_app, request, jsonify, g, Blueprint
from app.models import User, UserSession, db

class AuthError(Exception):
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code

auth_bp = Blueprint('auth', __name__)

def hash_password(password: str) -> str:
    """Hash password using bcrypt with configurable rounds."""
    rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 13)
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

def create_user_session(user: User, ip_address: str = None, user_agent: str = None) -> UserSession:
    """Create a new user session."""
    session = UserSession(
        user_id=user.id,
        session_token=generate_session_token(),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    )
    db.session.add(session)
    db.session.commit()
    return session

def create_jwt_token(user: User) -> str:
    """Create JWT token for user."""
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_jwt_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError('Token has expired')
    except jwt.InvalidTokenError:
        raise AuthError('Invalid token')

def authenticate_user(username: str, password: str) -> tuple[User, str]:
    """Authenticate user and return user object and token."""
    user = User.query.filter_by(username=username, is_active=True).first()

    if not user or not verify_password(password, user.password_hash):
        raise AuthError('Invalid credentials')

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    token = create_jwt_token(user)
    return user, token

def get_current_user() -> User:
    """Get current authenticated user."""
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        raise AuthError('Missing or invalid authorization header')

    token = auth_header.split(' ', 1)[1]
    payload = decode_jwt_token(token)

    user = User.query.get(payload['user_id'])
    if not user or not user.is_active:
        raise AuthError('User not found or inactive')

    return user

def auth_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            g.current_user = get_current_user()
            return f(*args, **kwargs)
        except AuthError as e:
            return jsonify({'error': e.message}), e.status_code
        except Exception as e:
            current_app.logger.error(f'Auth error: {str(e)}')
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated

def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user = get_current_user()
            if not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            g.current_user = user
            return f(*args, **kwargs)
        except AuthError as e:
            return jsonify({'error': e.message}), e.status_code

    return decorated