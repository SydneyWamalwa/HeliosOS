"""
Enhanced Routes for HeliosOS AI-Powered Features
Extends the existing routes with new AI command processing and application management
"""

import asyncio
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.ai_command_processor import ai_command_processor
from app.application_manager import application_manager, ApplicationCategory
from app.models import AIInteraction, db

logger = logging.getLogger(__name__)

# Create blueprint for enhanced routes
enhanced_bp = Blueprint('enhanced', __name__, url_prefix='/api/v2')

@enhanced_bp.route('/ai/command', methods=['POST'])
@login_required
async def process_ai_command():
    """Process natural language AI commands"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        command_text = data.get('command', '').strip()
        if not command_text:
            return jsonify({'error': 'No command provided'}), 400

        # Prepare user context
        user_context = {
            'user_id': current_user.id,
            'username': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Process the command
        result = await ai_command_processor.process_command(command_text, user_context)

        # Log the AI interaction
        try:
            interaction = AIInteraction(
                user_id=current_user.id,
                interaction_type='command',
                input_text=command_text[:1000],
                output_text=result.message[:2000] if result.message else None,
                model_used='ai-command-processor',
                success=result.success,
                error_message=result.error if not result.success else None,
                response_time=0.0  # Would be calculated in a real implementation
            )
            db.session.add(interaction)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log AI interaction: {e}")
            db.session.rollback()

        response = {
            'success': result.success,
            'message': result.message,
            'data': result.data
        }

        if not result.success:
            response['error'] = result.error

        return jsonify(response)

    except Exception as e:
        logger.error(f"AI command processing failed: {e}")
        return jsonify({'error': 'AI command processing failed'}), 500

@enhanced_bp.route('/applications', methods=['GET'])
@login_required
async def list_applications():
    """List available applications"""
    try:
        category_param = request.args.get('category')
        category = None
        
        if category_param:
            try:
                category = ApplicationCategory(category_param.lower())
            except ValueError:
                return jsonify({'error': f'Invalid category: {category_param}'}), 400

        applications = await application_manager.list_applications(category)
        
        return jsonify({
            'success': True,
            'applications': applications
        })

    except Exception as e:
        logger.error(f"Failed to list applications: {e}")
        return jsonify({'error': 'Failed to list applications'}), 500

@enhanced_bp.route('/applications/<app_name>/start', methods=['POST'])
@login_required
async def start_application(app_name):
    """Start an application"""
    try:
        result = await application_manager.start_application(app_name)
        
        # Log the action
        logger.info(f"User {current_user.username} started application {app_name}")
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to start application {app_name}: {e}")
        return jsonify({'error': f'Failed to start application {app_name}'}), 500

@enhanced_bp.route('/applications/<app_name>/stop', methods=['POST'])
@login_required
async def stop_application(app_name):
    """Stop an application"""
    try:
        result = await application_manager.stop_application(app_name)
        
        # Log the action
        logger.info(f"User {current_user.username} stopped application {app_name}")
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to stop application {app_name}: {e}")
        return jsonify({'error': f'Failed to stop application {app_name}'}), 500

@enhanced_bp.route('/applications/<app_name>/restart', methods=['POST'])
@login_required
async def restart_application(app_name):
    """Restart an application"""
    try:
        result = await application_manager.restart_application(app_name)
        
        # Log the action
        logger.info(f"User {current_user.username} restarted application {app_name}")
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to restart application {app_name}: {e}")
        return jsonify({'error': f'Failed to restart application {app_name}'}), 500

@enhanced_bp.route('/applications/<app_name>', methods=['GET'])
@login_required
async def get_application_info(app_name):
    """Get detailed information about an application"""
    try:
        app_info = await application_manager.get_application_info(app_name)
        
        if app_info is None:
            return jsonify({'error': f'Application {app_name} not found'}), 404
        
        return jsonify({
            'success': True,
            'application': app_info
        })

    except Exception as e:
        logger.error(f"Failed to get application info for {app_name}: {e}")
        return jsonify({'error': f'Failed to get application info'}), 500

@enhanced_bp.route('/applications/running', methods=['GET'])
@login_required
async def get_running_applications():
    """Get list of currently running applications"""
    try:
        running_apps = await application_manager.get_running_applications()
        
        return jsonify({
            'success': True,
            'running_applications': running_apps
        })

    except Exception as e:
        logger.error(f"Failed to get running applications: {e}")
        return jsonify({'error': 'Failed to get running applications'}), 500

@enhanced_bp.route('/applications/<app_name>/action', methods=['POST'])
@login_required
async def execute_application_action(app_name):
    """Execute a specific action within an application"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        action = data.get('action')
        parameters = data.get('parameters', {})

        if not action:
            return jsonify({'error': 'No action specified'}), 400

        result = await application_manager.execute_application_action(app_name, action, parameters)
        
        # Log the action
        logger.info(f"User {current_user.username} executed action {action} on application {app_name}")
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to execute action on application {app_name}: {e}")
        return jsonify({'error': f'Failed to execute action on application {app_name}'}), 500

@enhanced_bp.route('/system/status', methods=['GET'])
@login_required
async def get_system_status():
    """Get comprehensive system status"""
    try:
        # Get running applications
        running_apps = await application_manager.get_running_applications()
        
        # Get system information (placeholder - would be more comprehensive in real implementation)
        import psutil
        
        system_info = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'running_applications': len(running_apps),
            'total_applications': len(application_manager.applications)
        }
        
        return jsonify({
            'success': True,
            'system_status': system_info,
            'running_applications': running_apps
        })

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return jsonify({'error': 'Failed to get system status'}), 500

@enhanced_bp.route('/ai/suggestions', methods=['GET'])
@login_required
async def get_ai_suggestions():
    """Get AI-powered suggestions based on user context"""
    try:
        # Get user's recent activity (placeholder implementation)
        user_context = {
            'recent_commands': [],  # Would be populated from database
            'running_applications': await application_manager.get_running_applications(),
            'time_of_day': datetime.now().hour,
            'user_type': current_user.profile.get('user_type', 'general') if current_user.profile else 'general'
        }
        
        # Generate suggestions based on context
        suggestions = []
        
        # Time-based suggestions
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            suggestions.append({
                'type': 'application',
                'title': 'Start your workday',
                'description': 'Open LibreOffice to work on documents',
                'command': 'open libreoffice',
                'priority': 'medium'
            })
        
        # User type based suggestions
        user_type = user_context.get('user_type', 'general')
        if user_type == 'programmer':
            suggestions.append({
                'type': 'application',
                'title': 'Development Environment',
                'description': 'Launch VS Code for coding',
                'command': 'open vs code',
                'priority': 'high'
            })
        elif user_type == 'student':
            suggestions.append({
                'type': 'application',
                'title': 'Note Taking',
                'description': 'Open Joplin for taking notes',
                'command': 'open joplin',
                'priority': 'high'
            })
        
        # Running applications based suggestions
        running_apps = user_context.get('running_applications', [])
        if not running_apps:
            suggestions.append({
                'type': 'system',
                'title': 'Get Started',
                'description': 'No applications are running. Try saying "open firefox" to start browsing',
                'command': 'open firefox',
                'priority': 'low'
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'context': user_context
        })

    except Exception as e:
        logger.error(f"Failed to get AI suggestions: {e}")
        return jsonify({'error': 'Failed to get AI suggestions'}), 500

@enhanced_bp.route('/workflows', methods=['GET'])
@login_required
async def list_workflows():
    """List available workflows"""
    try:
        # Placeholder implementation - would be stored in database
        workflows = [
            {
                'name': 'morning_routine',
                'display_name': 'Morning Work Routine',
                'description': 'Opens email, calendar, and task manager',
                'steps': [
                    'open firefox',
                    'open libreoffice calc',
                    'show system status'
                ],
                'category': 'business'
            },
            {
                'name': 'development_setup',
                'display_name': 'Development Environment Setup',
                'description': 'Sets up complete development environment',
                'steps': [
                    'open vs code',
                    'open gitea',
                    'open portainer'
                ],
                'category': 'programmer'
            },
            {
                'name': 'study_session',
                'display_name': 'Study Session Setup',
                'description': 'Prepares environment for studying',
                'steps': [
                    'open joplin',
                    'open zotero',
                    'open firefox'
                ],
                'category': 'student'
            }
        ]
        
        return jsonify({
            'success': True,
            'workflows': workflows
        })

    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return jsonify({'error': 'Failed to list workflows'}), 500

@enhanced_bp.route('/workflows/<workflow_name>/execute', methods=['POST'])
@login_required
async def execute_workflow(workflow_name):
    """Execute a predefined workflow"""
    try:
        # This would be implemented to execute a series of commands
        # For now, it's a placeholder
        
        result = {
            'success': True,
            'message': f'Workflow {workflow_name} execution started',
            'workflow_name': workflow_name,
            'status': 'in_progress'
        }
        
        logger.info(f"User {current_user.username} executed workflow {workflow_name}")
        
        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_name}: {e}")
        return jsonify({'error': f'Failed to execute workflow {workflow_name}'}), 500

# Error handlers for the enhanced blueprint
@enhanced_bp.errorhandler(404)
def enhanced_not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@enhanced_bp.errorhandler(500)
def enhanced_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

