"""
Enhanced Routes v3 for HeliosOS with Leo Integration
Comprehensive API endpoints for AI-powered application manipulation
"""

import asyncio
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.leo_enhanced import enhanced_leo
from app.enhanced_ai_agent import enhanced_ai_agent
from app.plugin_system import plugin_manager
from app.models import AIInteraction, db

logger = logging.getLogger(__name__)

# Create blueprint for enhanced routes v3
enhanced_v3_bp = Blueprint('enhanced_v3', __name__, url_prefix='/api/v3')

@enhanced_v3_bp.route('/leo/command', methods=['POST'])
@login_required
async def leo_process_command():
    """Process natural language command through enhanced Leo"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        command_text = data.get('command', '').strip()
        if not command_text:
            return jsonify({'error': 'No command provided'}), 400

        session_id = data.get('session_id')
        
        # Process command through Leo
        result = await enhanced_leo.process_command(
            command=command_text,
            user_id=str(current_user.id),
            session_id=session_id
        )

        response = {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'suggestions': result.suggestions,
            'execution_time': result.execution_time,
            'context_updates': result.context_updates
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Leo command processing failed: {e}")
        return jsonify({'error': 'Leo command processing failed'}), 500

@enhanced_v3_bp.route('/leo/capabilities', methods=['GET'])
@login_required
async def get_leo_capabilities():
    """Get Leo's current capabilities and status"""
    try:
        capabilities = await enhanced_leo.get_capabilities()
        return jsonify({
            'success': True,
            'capabilities': capabilities
        })

    except Exception as e:
        logger.error(f"Failed to get Leo capabilities: {e}")
        return jsonify({'error': 'Failed to get capabilities'}), 500

@enhanced_v3_bp.route('/leo/suggestions', methods=['GET'])
@login_required
async def get_leo_suggestions():
    """Get personalized suggestions from Leo"""
    try:
        session_id = request.args.get('session_id')
        suggestions = await enhanced_leo.get_suggestions(
            user_id=str(current_user.id),
            session_id=session_id
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.error(f"Failed to get Leo suggestions: {e}")
        return jsonify({'error': 'Failed to get suggestions'}), 500

@enhanced_v3_bp.route('/applications/discover', methods=['POST'])
@login_required
async def discover_applications():
    """Trigger application discovery"""
    try:
        discovered_apps = await enhanced_ai_agent.discover_applications()
        
        return jsonify({
            'success': True,
            'message': f'Discovered {len(discovered_apps)} applications',
            'applications': {
                name: {
                    'name': app.name,
                    'category': app.category,
                    'description': app.description,
                    'is_running': app.is_running
                }
                for name, app in discovered_apps.items()
            }
        })

    except Exception as e:
        logger.error(f"Failed to discover applications: {e}")
        return jsonify({'error': 'Failed to discover applications'}), 500

@enhanced_v3_bp.route('/applications/<app_name>/manipulate', methods=['POST'])
@login_required
async def manipulate_application(app_name):
    """Manipulate an application directly"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        action = data.get('action')
        parameters = data.get('parameters', {})

        if not action:
            return jsonify({'error': 'No action specified'}), 400

        # Use Leo for application manipulation
        result = await enhanced_leo.handle_application_manipulation(
            app_name=app_name,
            action=action,
            parameters=parameters
        )

        response = {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'suggestions': result.suggestions
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Failed to manipulate application {app_name}: {e}")
        return jsonify({'error': f'Failed to manipulate application {app_name}'}), 500

@enhanced_v3_bp.route('/applications/bulk-action', methods=['POST'])
@login_required
async def bulk_application_action():
    """Perform bulk actions on multiple applications"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        applications = data.get('applications', [])
        action = data.get('action')
        parameters = data.get('parameters', {})

        if not applications or not action:
            return jsonify({'error': 'Applications list and action are required'}), 400

        results = []
        for app_name in applications:
            try:
                result = await enhanced_leo.handle_application_manipulation(
                    app_name=app_name,
                    action=action,
                    parameters=parameters
                )
                results.append({
                    'application': app_name,
                    'success': result.success,
                    'message': result.message
                })
            except Exception as e:
                results.append({
                    'application': app_name,
                    'success': False,
                    'message': str(e)
                })

        successful_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': successful_count > 0,
            'message': f'Bulk action completed: {successful_count}/{len(applications)} successful',
            'results': results,
            'summary': {
                'total': len(applications),
                'successful': successful_count,
                'failed': len(applications) - successful_count
            }
        })

    except Exception as e:
        logger.error(f"Failed to perform bulk application action: {e}")
        return jsonify({'error': 'Failed to perform bulk action'}), 500

@enhanced_v3_bp.route('/workflows/<workflow_name>/execute', methods=['POST'])
@login_required
async def execute_workflow(workflow_name):
    """Execute a workflow through Leo"""
    try:
        data = request.get_json() or {}
        parameters = data.get('parameters', {})

        result = await enhanced_leo.execute_workflow(
            workflow_name=workflow_name,
            user_id=str(current_user.id),
            parameters=parameters
        )

        response = {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'suggestions': result.suggestions
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_name}: {e}")
        return jsonify({'error': f'Failed to execute workflow {workflow_name}'}), 500

@enhanced_v3_bp.route('/plugins', methods=['GET'])
@login_required
async def list_plugins():
    """List all loaded plugins"""
    try:
        plugins = plugin_manager.list_plugins()
        
        plugin_data = []
        for plugin in plugins:
            plugin_data.append({
                'name': plugin.metadata.name,
                'version': plugin.metadata.version,
                'description': plugin.metadata.description,
                'author': plugin.metadata.author,
                'type': plugin.metadata.plugin_type.value,
                'status': plugin.status.value,
                'dependencies': plugin.metadata.dependencies,
                'permissions': plugin.metadata.permissions,
                'error_message': plugin.error_message
            })

        return jsonify({
            'success': True,
            'plugins': plugin_data,
            'summary': {
                'total': len(plugins),
                'active': len([p for p in plugins if p.status.value == 'active']),
                'inactive': len([p for p in plugins if p.status.value == 'inactive']),
                'error': len([p for p in plugins if p.status.value == 'error'])
            }
        })

    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        return jsonify({'error': 'Failed to list plugins'}), 500

@enhanced_v3_bp.route('/plugins/<plugin_name>/reload', methods=['POST'])
@login_required
async def reload_plugin(plugin_name):
    """Reload a specific plugin"""
    try:
        success = await plugin_manager.reload_plugin(plugin_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Plugin {plugin_name} reloaded successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to reload plugin {plugin_name}'
            }), 400

    except Exception as e:
        logger.error(f"Failed to reload plugin {plugin_name}: {e}")
        return jsonify({'error': f'Failed to reload plugin {plugin_name}'}), 500

@enhanced_v3_bp.route('/system/comprehensive-status', methods=['GET'])
@login_required
async def get_comprehensive_system_status():
    """Get comprehensive system status including applications and plugins"""
    try:
        # Get Leo capabilities
        leo_capabilities = await enhanced_leo.get_capabilities()
        
        # Get application status
        applications = enhanced_ai_agent.applications
        running_apps = [app for app in applications.values() if app.is_running]
        
        # Get plugin status
        plugins = plugin_manager.list_plugins()
        active_plugins = [p for p in plugins if p.status.value == 'active']
        
        # Get system metrics
        import psutil
        system_metrics = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': psutil.boot_time()
        }

        return jsonify({
            'success': True,
            'system_status': {
                'leo': leo_capabilities,
                'applications': {
                    'total_discovered': len(applications),
                    'currently_running': len(running_apps),
                    'categories': list(set(app.category for app in applications.values())),
                    'running_apps': [
                        {
                            'name': app.name,
                            'category': app.category,
                            'pid': app.pid,
                            'memory_usage': app.memory_usage,
                            'cpu_usage': app.cpu_usage
                        }
                        for app in running_apps
                    ]
                },
                'plugins': {
                    'total_loaded': len(plugins),
                    'active': len(active_plugins),
                    'types': list(set(p.metadata.plugin_type.value for p in active_plugins))
                },
                'system_metrics': system_metrics,
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Failed to get comprehensive system status: {e}")
        return jsonify({'error': 'Failed to get system status'}), 500

@enhanced_v3_bp.route('/ai/context/<session_id>', methods=['GET'])
@login_required
async def get_ai_context(session_id):
    """Get AI context for a session"""
    try:
        # Get session context from Leo
        if session_id in enhanced_leo.active_sessions:
            session_data = enhanced_leo.active_sessions[session_id]
            
            return jsonify({
                'success': True,
                'context': {
                    'session_id': session_id,
                    'user_id': session_data['user_id'],
                    'created_at': session_data['created_at'].isoformat(),
                    'current_applications': session_data['current_applications'],
                    'recent_commands': session_data['recent_commands'],
                    'last_activity': session_data.get('last_activity', session_data['created_at']).isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404

    except Exception as e:
        logger.error(f"Failed to get AI context: {e}")
        return jsonify({'error': 'Failed to get AI context'}), 500

@enhanced_v3_bp.route('/ai/learning/patterns', methods=['GET'])
@login_required
async def get_learning_patterns():
    """Get AI learning patterns for the current user"""
    try:
        user_id = str(current_user.id)
        patterns = enhanced_ai_agent.user_patterns.get(user_id, {})
        
        return jsonify({
            'success': True,
            'patterns': {
                'common_commands': patterns.get('common_commands', {}),
                'preferred_applications': patterns.get('preferred_applications', {}),
                'usage_times': patterns.get('usage_times', []),
                'success_rate': patterns.get('success_rate', 0.0)
            }
        })

    except Exception as e:
        logger.error(f"Failed to get learning patterns: {e}")
        return jsonify({'error': 'Failed to get learning patterns'}), 500

@enhanced_v3_bp.route('/applications/smart-launch', methods=['POST'])
@login_required
async def smart_application_launch():
    """Smart application launch with context awareness"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        app_name = data.get('application')
        context_hints = data.get('context', {})
        
        if not app_name:
            return jsonify({'error': 'No application specified'}), 400

        # Build smart command with context
        command = f"open {app_name}"
        
        # Add context hints to command
        if context_hints.get('url'):
            command += f" with url {context_hints['url']}"
        if context_hints.get('file'):
            command += f" file {context_hints['file']}"
        if context_hints.get('workspace'):
            command += f" in {context_hints['workspace']} workspace"

        # Process through Leo
        result = await enhanced_leo.process_command(
            command=command,
            user_id=str(current_user.id)
        )

        response = {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'suggestions': result.suggestions
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Failed smart application launch: {e}")
        return jsonify({'error': 'Failed smart application launch'}), 500

@enhanced_v3_bp.route('/automation/create-workflow', methods=['POST'])
@login_required
async def create_custom_workflow():
    """Create a custom workflow from commands"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        workflow_name = data.get('name')
        commands = data.get('commands', [])
        description = data.get('description', '')

        if not workflow_name or not commands:
            return jsonify({'error': 'Workflow name and commands are required'}), 400

        # For now, store in session (in production, would store in database)
        workflow_data = {
            'name': workflow_name,
            'description': description,
            'commands': commands,
            'created_by': str(current_user.id),
            'created_at': datetime.now().isoformat()
        }

        # This would be stored in a proper workflow management system
        return jsonify({
            'success': True,
            'message': f'Workflow "{workflow_name}" created successfully',
            'workflow': workflow_data
        })

    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        return jsonify({'error': 'Failed to create workflow'}), 500

@enhanced_v3_bp.route('/health/detailed', methods=['GET'])
async def detailed_health_check():
    """Detailed health check for all components"""
    try:
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }

        # Check Leo
        try:
            leo_caps = await enhanced_leo.get_capabilities()
            health_status['components']['leo'] = {
                'status': 'healthy',
                'version': leo_caps.get('version', 'unknown'),
                'capabilities_count': len(leo_caps.get('capabilities', []))
            }
        except Exception as e:
            health_status['components']['leo'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'

        # Check AI Agent
        try:
            app_count = len(enhanced_ai_agent.applications)
            health_status['components']['ai_agent'] = {
                'status': 'healthy',
                'applications_discovered': app_count
            }
        except Exception as e:
            health_status['components']['ai_agent'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'

        # Check Plugin Manager
        try:
            plugins = plugin_manager.list_plugins()
            active_plugins = [p for p in plugins if p.status.value == 'active']
            health_status['components']['plugin_manager'] = {
                'status': 'healthy',
                'total_plugins': len(plugins),
                'active_plugins': len(active_plugins)
            }
        except Exception as e:
            health_status['components']['plugin_manager'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'

        # Check Database
        try:
            db.session.execute('SELECT 1')
            health_status['components']['database'] = {
                'status': 'healthy'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'unhealthy'

        status_code = 200 if health_status['overall_status'] == 'healthy' else 503
        return jsonify(health_status), status_code

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unhealthy',
            'error': str(e)
        }), 503

# Error handlers for the enhanced v3 blueprint
@enhanced_v3_bp.errorhandler(404)
def enhanced_v3_not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@enhanced_v3_bp.errorhandler(500)
def enhanced_v3_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@enhanced_v3_bp.errorhandler(400)
def enhanced_v3_bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

