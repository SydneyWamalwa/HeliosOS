import time
import logging
import subprocess
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import text
from app import db
from app.models import CommandAudit, AIInteraction
from app.ai_client import get_ai_service

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Main application page"""
    return render_template('index.html')

@main_bp.route('/vnc.html')
@login_required
def vnc_page():
    """VNC desktop page"""
    import os
    return send_from_directory(os.path.dirname(current_app.root_path), 'vnc.html')

@main_bp.route('/health')
def health_check():
    """System health check endpoint"""
    try:
        # Database health check with proper text() wrapper
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = 'unhealthy'

    # AI service health check
    try:
        ai_service = get_ai_service()
        ai_health = ai_service.health_check()
        ai_status = ai_health.get('status', 'unknown')
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        ai_status = 'unhealthy'

    # Overall system status
    system_status = 'healthy' if db_status == 'healthy' and ai_status == 'healthy' else 'degraded'

    status_data = {
        'status': system_status,
        'timestamp': time.time(),
        'components': {
            'database': db_status,
            'ai_service': {
                'status': ai_status,
                'models_available': ['facebook/bart-large-cnn', 'microsoft/DialoGPT-medium']
            }
        }
    }

    return jsonify(status_data)

@main_bp.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI chat endpoint"""
    start_time = time.time()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        messages = data.get('messages', [])

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        # Get AI service
        ai_service = get_ai_service()

        # Generate response
        response_text = ai_service.chat(messages)
        response_time = time.time() - start_time

        # Log the AI interaction
        try:
            interaction = AIInteraction(
                user_id=current_user.id,
                interaction_type='chat',
                input_text=str(messages[-1].get('content', ''))[:1000],
                output_text=response_text[:2000],
                model_used='chat-model',
                success=True,
                response_time=response_time
            )
            db.session.add(interaction)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log AI interaction: {e}")
            db.session.rollback()

        return jsonify({
            'success': True,
            'response': response_text
        })

    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"AI chat failed: {e}")

        # Log failed interaction
        try:
            interaction = AIInteraction(
                user_id=current_user.id if current_user.is_authenticated else None,
                interaction_type='chat',
                input_text=str(request.get_json().get('messages', []))[:1000] if request.get_json() else '',
                output_text=None,
                model_used='chat-model',
                success=False,
                error_message=str(e),
                response_time=response_time
            )
            db.session.add(interaction)
            db.session.commit()
        except Exception as log_error:
            logger.error(f"Failed to log failed AI interaction: {log_error}")
            db.session.rollback()

        return jsonify({'error': 'AI service unavailable'}), 500

@main_bp.route('/api/ai/summarize', methods=['POST'])
@login_required
def ai_summarize():
    """AI text summarization endpoint"""
    start_time = time.time()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        text = data.get('text', '').strip()

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        if len(text) > 10000:  # Limit text size
            return jsonify({'error': 'Text too long (max 10,000 characters)'}), 400

        # Get AI service
        ai_service = get_ai_service()

        # Generate summary
        summary = ai_service.summarize(text)
        response_time = time.time() - start_time

        original_length = len(text)
        summary_length = len(summary)
        compression_ratio = round(original_length / summary_length, 2) if summary_length > 0 else 0

        # Log the AI interaction
        try:
            interaction = AIInteraction(
                user_id=current_user.id,
                interaction_type='summarize',
                input_text=text[:1000],
                output_text=summary[:2000],
                model_used='summary-model',
                success=True,
                response_time=response_time
            )
            db.session.add(interaction)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log AI interaction: {e}")
            db.session.rollback()

        return jsonify({
            'success': True,
            'summary': summary,
            'original_length': original_length,
            'summary_length': summary_length,
            'compression_ratio': compression_ratio
        })

    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"AI summarization failed: {e}")

        # Log failed interaction
        try:
            interaction = AIInteraction(
                user_id=current_user.id if current_user.is_authenticated else None,
                interaction_type='summarize',
                input_text=str(request.get_json().get('text', ''))[:1000] if request.get_json() else '',
                output_text=None,
                model_used='summary-model',
                success=False,
                error_message=str(e),
                response_time=response_time
            )
            db.session.add(interaction)
            db.session.commit()
        except Exception as log_error:
            logger.error(f"Failed to log failed AI interaction: {log_error}")
            db.session.rollback()

        return jsonify({'error': 'Summarization service unavailable'}), 500

@main_bp.route('/api/exec', methods=['POST'])
@login_required
def execute_command():
    """Execute system command with security restrictions"""
    start_time = time.time()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        command = data.get('command', '').strip()

        if not command:
            return jsonify({'error': 'No command provided'}), 400

        # Security: Whitelist of allowed commands
        allowed_commands = {
            'ls', 'pwd', 'whoami', 'date', 'uptime', 'df', 'free', 'ps',
            'top', 'htop', 'lscpu', 'lsmem', 'uname', 'hostname', 'id',
            'groups', 'env', 'printenv', 'which', 'whereis', 'locate',
            'find', 'grep', 'cat', 'head', 'tail', 'wc', 'sort', 'uniq'
        }

        # Extract base command
        base_cmd = command.split()[0] if command.split() else ''

        if base_cmd not in allowed_commands:
            return jsonify({
                'error': f'Command "{base_cmd}" not allowed. Allowed commands: {", ".join(sorted(allowed_commands))}'
            }), 403

        # Execute command
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.path.expanduser('~')  # Run in user home directory
            )

            execution_time = time.time() - start_time
            output = result.stdout + result.stderr

            # Log the command execution
            try:
                audit = CommandAudit(
                    user_id=current_user.id,
                    username=current_user.username,
                    command=command,
                    return_code=result.returncode,
                    stdout=result.stdout[:2000],  # Limit output size
                    stderr=result.stderr[:2000],
                    execution_time=execution_time,
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to log command audit: {e}")
                db.session.rollback()

            return jsonify({
                'success': True,
                'output': output,
                'exit_code': result.returncode,
                'execution_time': round(execution_time, 3)
            })

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f'Command "{command}" timed out after 30 seconds'

            # Log timeout
            try:
                audit = CommandAudit(
                    user_id=current_user.id,
                    username=current_user.username,
                    command=command,
                    return_code=-1,
                    stderr=error_msg,
                    execution_time=execution_time,
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to log command audit: {e}")
                db.session.rollback()

            return jsonify({'error': error_msg}), 408

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f'Command execution failed: {str(e)}'

            # Log execution error
            try:
                audit = CommandAudit(
                    user_id=current_user.id,
                    username=current_user.username,
                    command=command,
                    return_code=-1,
                    stderr=error_msg,
                    execution_time=execution_time,
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to log command audit: {e}")
                db.session.rollback()

            return jsonify({'error': error_msg}), 500

    except Exception as e:
        logger.error(f"Command execution endpoint failed: {e}")
        return jsonify({'error': 'Command execution service unavailable'}), 500

@main_bp.route('/api/audit/commands')
@login_required
def get_command_audit():
    """Get command audit history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page

        # Admin can see all audits, regular users only their own
        if current_user.is_admin:
            query = CommandAudit.query
        else:
            query = CommandAudit.query.filter_by(user_id=current_user.id)

        audits = query.order_by(CommandAudit.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        audit_data = [audit.to_dict(include_output=False) for audit in audits.items]

        return jsonify({
            'success': True,
            'audits': audit_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': audits.total,
                'pages': audits.pages,
                'has_next': audits.has_next,
                'has_prev': audits.has_prev
            }
        })

    except Exception as e:
        logger.error(f"Failed to get command audit: {e}")
        return jsonify({'error': 'Audit service unavailable'}), 500

@main_bp.route('/api/audit/ai')
@login_required
def get_ai_audit():
    """Get AI interaction audit history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page

        # Admin can see all interactions, regular users only their own
        if current_user.is_admin:
            query = AIInteraction.query
        else:
            query = AIInteraction.query.filter_by(user_id=current_user.id)

        interactions = query.order_by(AIInteraction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        interaction_data = []
        for interaction in interactions.items:
            data = {
                'id': interaction.id,
                'type': interaction.interaction_type,
                'model': interaction.model_used,
                'success': interaction.success,
                'response_time': interaction.response_time,
                'created_at': interaction.created_at.isoformat() if interaction.created_at else None
            }
            # Only include error message if not successful
            if not interaction.success and interaction.error_message:
                data['error_message'] = interaction.error_message
            interaction_data.append(data)

        return jsonify({
            'success': True,
            'interactions': interaction_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': interactions.total,
                'pages': interactions.pages,
                'has_next': interactions.has_next,
                'has_prev': interactions.has_prev
            }
        })

    except Exception as e:
        logger.error(f"Failed to get AI audit: {e}")
        return jsonify({'error': 'Audit service unavailable'}), 500

@main_bp.route('/api/user/profile')
@login_required
def get_user_profile():
    """Get current user's profile"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict(include_sensitive=True)
        })
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        return jsonify({'error': 'Profile service unavailable'}), 500

@main_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def update_user_profile():
    """Update current user's profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Allow updating email and profile data
        if 'email' in data:
            email = data['email'].strip()
            if email:
                # Check if email is already taken by another user
                existing = db.session.query(User).filter(
                    User.email == email,
                    User.id != current_user.id
                ).first()
                if existing:
                    return jsonify({'error': 'Email already taken'}), 400
                current_user.email = email
            else:
                current_user.email = None

        if 'profile' in data and isinstance(data['profile'], dict):
            current_user.profile = {**current_user.profile, **data['profile']}

        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'user': current_user.to_dict(include_sensitive=True)
        })

    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@main_bp.route('/api/stats')
@login_required
def get_user_stats():
    """Get user statistics"""
    try:
        # Get command execution stats
        total_commands = CommandAudit.query.filter_by(user_id=current_user.id).count()
        successful_commands = CommandAudit.query.filter_by(
            user_id=current_user.id,
            return_code=0
        ).count()

        # Get AI interaction stats
        total_ai_interactions = AIInteraction.query.filter_by(user_id=current_user.id).count()
        successful_ai_interactions = AIInteraction.query.filter_by(
            user_id=current_user.id,
            success=True
        ).count()

        # Calculate success rates
        cmd_success_rate = (successful_commands / total_commands * 100) if total_commands > 0 else 0
        ai_success_rate = (successful_ai_interactions / total_ai_interactions * 100) if total_ai_interactions > 0 else 0

        stats = {
            'commands': {
                'total': total_commands,
                'successful': successful_commands,
                'success_rate': round(cmd_success_rate, 1)
            },
            'ai_interactions': {
                'total': total_ai_interactions,
                'successful': successful_ai_interactions,
                'success_rate': round(ai_success_rate, 1)
            },
            'user': {
                'username': current_user.username,
                'member_since': current_user.created_at.strftime('%Y-%m-%d') if current_user.created_at else None,
                'last_login': current_user.last_login.strftime('%Y-%m-%d %H:%M') if current_user.last_login else None
            }
        }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        return jsonify({'error': 'Stats service unavailable'}), 500

# Admin-only routes
@main_bp.route('/api/admin/users')
@login_required
def admin_get_users():
    """Admin: Get all users"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        users = User.query.order_by(User.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        user_data = [user.to_dict() for user in users.items]

        return jsonify({
            'success': True,
            'users': user_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages
            }
        })

    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({'error': 'User service unavailable'}), 500

@main_bp.route('/api/admin/system')
@login_required
def admin_system_info():
    """Admin: Get system information"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    try:
        import psutil
        import platform

        system_info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'resources': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                }
            },
            'uptime': time.time() - psutil.boot_time()
        }

        return jsonify({
            'success': True,
            'system': system_info
        })

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return jsonify({'error': 'System info unavailable'}), 500