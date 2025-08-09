import logging
from flask import Blueprint, current_app, render_template, request, jsonify, g
from flask_limiter import RateLimitExceeded
from app import db, limiter
from app.models import User, CommandAudit, AIInteraction
from app.auth import hash_password, authenticate_user, auth_required, admin_required
from app.ai_client import get_ai_service, AIServiceError
from app.exec_service import get_command_executor, CommandExecutionError
from app.utils import validate_json, sanitize_input

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# Rate limiting decorators
def api_rate_limit():
    return limiter.limit("100 per hour, 1000 per day")

def auth_rate_limit():
    return limiter.limit("10 per minute, 100 per hour")

@main_bp.errorhandler(RateLimitExceeded)
def handle_rate_limit(error):
    return jsonify({
        'error': 'rate_limit_exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': error.retry_after
    }), 429

@main_bp.route('/')
def index():
    """Main application interface."""
    return render_template('index.html')

@main_bp.route('/health')
def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Database check
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = 'unhealthy'

    # AI service check
    try:
        ai_service = get_ai_service()
        ai_health = ai_service.health_check()
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        ai_health = {'status': 'error', 'error': str(e)}

    overall_status = 'healthy' if db_status == 'healthy' and ai_health['status'] == 'healthy' else 'degraded'

    return jsonify({
        'service': 'helios-os',
        'status': overall_status,
        'components': {
            'database': db_status,
            'ai_service': ai_health,
            'command_executor': 'healthy'
        },
        'version': '1.0.0',
        'timestamp': time.time()
    })

# Authentication endpoints
@main_bp.route('/api/auth/register', methods=['POST'])
@auth_rate_limit()
def register():
    """User registration endpoint."""
    try:
        data = validate_json(request.get_json())
        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')
        email = sanitize_input(data.get('email', ''))

        # Validation
        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400

        if not password or len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409

        if email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409

        # Create user
        user = User(
            username=username,
            email=email if email else None,
            password_hash=hash_password(password),
            profile={'created_via': 'registration'}
        )

        db.session.add(user)
        db.session.commit()

        logger.info(f"New user registered: {username}")

        # Create session token
        _, token = authenticate_user(username, password)

        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@main_bp.route('/api/auth/login', methods=['POST'])
@auth_rate_limit()
def login():
    """User login endpoint."""
    try:
        data = validate_json(request.get_json())
        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        user, token = authenticate_user(username, password)

        logger.info(f"User logged in: {username}")

        return jsonify({
            'success': True,
            'token': token,
            'user': user.to_dict(include_sensitive=True)
        })

    except Exception as e:
        logger.warning(f"Login failed for {username}: {str(e)}")
        return jsonify({'error': 'Invalid credentials'}), 401

@main_bp.route('/api/auth/logout', methods=['POST'])
@auth_required
def logout():
    """User logout endpoint."""
    # In a production system, you'd invalidate the token
    # For now, we'll just log the logout
    logger.info(f"User logged out: {g.current_user.username}")
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# AI endpoints
@main_bp.route('/api/ai/summarize', methods=['POST'])
@auth_required
@api_rate_limit()
def summarize_text():
    """Text summarization endpoint."""
    try:
        data = validate_json(request.get_json())
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'summary': '', 'word_count': 0})

        if len(text) > 10000:  # Limit input size
            return jsonify({'error': 'Text too long (max 10,000 characters)'}), 400

        ai_service = get_ai_service()
        summary = ai_service.summarize(text)

        return jsonify({
            'success': True,
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary),
            'compression_ratio': round(len(summary) / len(text), 2) if text else 0
        })

    except AIServiceError as e:
        logger.error(f"AI summarization error: {str(e)}")
        return jsonify({'error': 'Summarization service unavailable'}), 503

    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        return jsonify({'error': 'Summarization failed'}), 500

@main_bp.route('/api/ai/chat', methods=['POST'])
@auth_required
@api_rate_limit()
def chat_with_leo():
    """Chat with Leo AI assistant."""
    try:
        data = validate_json(request.get_json())
        messages = data.get('messages', [])

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        # Validate message format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return jsonify({'error': 'Invalid message format'}), 400

        # Limit conversation history
        messages = messages[-10:]  # Keep last 10 messages

        ai_service = get_ai_service()
        response = ai_service.chat(messages)

        return jsonify({
            'success': True,
            'response': response,
            'conversation_length': len(messages)
        })

    except AIServiceError as e:
        logger.error(f"AI chat error: {str(e)}")
        return jsonify({'error': 'Chat service unavailable'}), 503

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Chat failed'}), 500

# Command execution endpoints
@main_bp.route('/api/exec/run', methods=['POST'])
@auth_required
@limiter.limit("30 per minute")
def execute_command():
    """Execute system command."""
    try:
        data = validate_json(request.get_json())
        command = sanitize_input(data.get('command', ''))

        if not command:
            return jsonify({'error': 'No command provided'}), 400

        executor = get_command_executor()
        result, status_code = executor.execute_command(command, g.current_user)

        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return jsonify({'error': 'Command execution failed'}), 500

@main_bp.route('/api/exec/commands', methods=['GET'])
@auth_required
def get_allowed_commands():
    """Get list of allowed commands."""
    executor = get_command_executor()
    commands = executor.get_allowed_commands()

    return jsonify({
        'success': True,
        'commands': commands,
        'total': len(commands)
    })

# Audit and monitoring endpoints
@main_bp.route('/api/audit/commands', methods=['GET'])
@auth_required
def get_command_audit():
    """Get command execution audit trail."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Users can only see their own audits unless they're admin
        query = CommandAudit.query
        if not g.current_user.is_admin:
            query = query.filter_by(user_id=g.current_user.id)

        audits = query.order_by(CommandAudit.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'audits': [audit.to_dict() for audit in audits.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': audits.total,
                'pages': audits.pages
            }
        })

    except Exception as e:
        logger.error(f"Audit retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve audit data'}), 500

@main_bp.route('/api/audit/ai', methods=['GET'])
@auth_required
def get_ai_audit():
    """Get AI interaction audit trail."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        query = AIInteraction.query
        if not g.current_user.is_admin:
            query = query.filter_by(user_id=g.current_user.id)

        interactions = query.order_by(AIInteraction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'interactions': [
                {
                    'id': i.id,
                    'type': i.interaction_type,
                    'model': i.model_used,
                    'response_time': i.response_time,
                    'success': i.success,
                    'created_at': i.created_at.isoformat()
                } for i in interactions.items
            ],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': interactions.total,
                'pages': interactions.pages
            }
        })

    except Exception as e:
        logger.error(f"AI audit retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve AI audit data'}), 500

# Admin endpoints
@main_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users (admin only)."""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'total': len(users)
        })
    except Exception as e:
        logger.error(f"User retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@main_bp.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_system_stats():
    """Get system statistics (admin only)."""
    try:
        from sqlalchemy import func

        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()

        # Command statistics
        total_commands = CommandAudit.query.count()
        recent_commands = CommandAudit.query.filter(
            CommandAudit.created_at > func.now() - timedelta(days=7)
        ).count()

        # AI statistics
        total_ai_interactions = AIInteraction.query.count()
        successful_ai = AIInteraction.query.filter_by(success=True).count()

        return jsonify({
            'success': True,
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users
                },
                'commands': {
                    'total': total_commands,
                    'last_7_days': recent_commands
                },
                'ai_interactions': {
                    'total': total_ai_interactions,
                    'success_rate': round(successful_ai / total_ai_interactions * 100, 2) if total_ai_interactions > 0 else 0
                }
            }
        })

    except Exception as e:
        logger.error(f"Stats retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500