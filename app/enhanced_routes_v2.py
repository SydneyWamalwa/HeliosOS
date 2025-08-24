"""
Enhanced Routes V2 for HeliosOS
Additional routes for workflow management and advanced AI features
"""

import asyncio
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app.enhanced_ai_client import enhanced_ai_client
from app.workflow_engine import workflow_engine
from app.models import AIInteraction, db

logger = logging.getLogger(__name__)

# Create blueprint for additional enhanced routes
enhanced_v2_bp = Blueprint('enhanced_v2', __name__, url_prefix='/api/v3')

@enhanced_v2_bp.route('/ai/enhanced-command', methods=['POST'])
@login_required
async def process_enhanced_ai_command():
    """Process natural language commands with enhanced AI understanding"""
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
            'user_type': current_user.profile.get('user_type', 'general') if current_user.profile else 'general',
            'timestamp': datetime.utcnow().isoformat()
        }

        # Process with enhanced AI client
        ai_response = await enhanced_ai_client.process_natural_language_command(command_text, user_context)

        # Update conversation history
        enhanced_ai_client.update_conversation_history(
            str(current_user.id), 
            command_text, 
            ai_response.content
        )

        # Log the AI interaction
        try:
            interaction = AIInteraction(
                user_id=current_user.id,
                interaction_type='enhanced_command',
                input_text=command_text[:1000],
                output_text=ai_response.content[:2000],
                model_used='enhanced-ai-client',
                success=ai_response.confidence > 0.5,
                response_time=0.0  # Would be calculated in real implementation
            )
            db.session.add(interaction)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log AI interaction: {e}")
            db.session.rollback()

        return jsonify({
            'success': True,
            'response': ai_response.content,
            'confidence': ai_response.confidence,
            'intent': ai_response.intent,
            'entities': ai_response.entities,
            'suggested_actions': ai_response.suggested_actions,
            'context': ai_response.context
        })

    except Exception as e:
        logger.error(f"Enhanced AI command processing failed: {e}")
        return jsonify({'error': 'Enhanced AI command processing failed'}), 500

@enhanced_v2_bp.route('/ai/application-help', methods=['POST'])
@login_required
async def get_application_help():
    """Get AI-powered help for specific applications"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        app_name = data.get('application', '').strip()
        user_query = data.get('query', '').strip()

        if not app_name or not user_query:
            return jsonify({'error': 'Application name and query are required'}), 400

        # Get application-specific help
        ai_response = await enhanced_ai_client.get_application_specific_help(app_name, user_query)

        return jsonify({
            'success': True,
            'response': ai_response.content,
            'confidence': ai_response.confidence,
            'application': app_name,
            'query': user_query
        })

    except Exception as e:
        logger.error(f"Application help failed: {e}")
        return jsonify({'error': 'Application help failed'}), 500

@enhanced_v2_bp.route('/workflows', methods=['GET'])
@login_required
async def list_workflows():
    """List available workflows"""
    try:
        category = request.args.get('category')
        workflows = await workflow_engine.list_workflows(category, str(current_user.id))
        
        return jsonify({
            'success': True,
            'workflows': workflows
        })

    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return jsonify({'error': 'Failed to list workflows'}), 500

@enhanced_v2_bp.route('/workflows', methods=['POST'])
@login_required
async def create_workflow():
    """Create a new custom workflow"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['name', 'steps']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        workflow_id = await workflow_engine.create_workflow(data, str(current_user.id))
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'message': 'Workflow created successfully'
        })

    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        return jsonify({'error': 'Failed to create workflow'}), 500

@enhanced_v2_bp.route('/workflows/<workflow_id>/execute', methods=['POST'])
@login_required
async def execute_workflow(workflow_id):
    """Execute a workflow"""
    try:
        data = request.get_json() or {}
        context = data.get('context', {})
        
        # Add user context
        context.update({
            'user_id': current_user.id,
            'username': current_user.username,
            'user_type': current_user.profile.get('user_type', 'general') if current_user.profile else 'general'
        })

        execution_id = await workflow_engine.execute_workflow(workflow_id, str(current_user.id), context)
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'message': 'Workflow execution started'
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        return jsonify({'error': 'Failed to execute workflow'}), 500

@enhanced_v2_bp.route('/workflows/executions/<execution_id>', methods=['GET'])
@login_required
async def get_execution_status(execution_id):
    """Get status of a workflow execution"""
    try:
        status = workflow_engine.get_execution_status(execution_id)
        
        if status is None:
            return jsonify({'error': 'Execution not found'}), 404
        
        return jsonify({
            'success': True,
            'execution': status
        })

    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        return jsonify({'error': 'Failed to get execution status'}), 500

@enhanced_v2_bp.route('/workflows/executions/<execution_id>/cancel', methods=['POST'])
@login_required
async def cancel_execution(execution_id):
    """Cancel a running workflow execution"""
    try:
        success = workflow_engine.cancel_execution(execution_id)
        
        if not success:
            return jsonify({'error': 'Execution not found or cannot be cancelled'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Execution cancelled successfully'
        })

    except Exception as e:
        logger.error(f"Failed to cancel execution: {e}")
        return jsonify({'error': 'Failed to cancel execution'}), 500

@enhanced_v2_bp.route('/workflows/<workflow_id>', methods=['DELETE'])
@login_required
async def delete_workflow(workflow_id):
    """Delete a custom workflow"""
    try:
        success = workflow_engine.delete_workflow(workflow_id, str(current_user.id))
        
        if not success:
            return jsonify({'error': 'Workflow not found or cannot be deleted'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Workflow deleted successfully'
        })

    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        return jsonify({'error': 'Failed to delete workflow'}), 500

@enhanced_v2_bp.route('/workflows/templates', methods=['GET'])
@login_required
async def get_workflow_templates():
    """Get workflow templates for creating new workflows"""
    try:
        templates = workflow_engine.get_workflow_templates()
        
        return jsonify({
            'success': True,
            'templates': templates
        })

    except Exception as e:
        logger.error(f"Failed to get workflow templates: {e}")
        return jsonify({'error': 'Failed to get workflow templates'}), 500

@enhanced_v2_bp.route('/ai/suggestions', methods=['GET'])
@login_required
async def get_ai_suggestions():
    """Get AI-powered suggestions and workflow recommendations"""
    try:
        # Get user context
        user_context = {
            'user_id': current_user.id,
            'username': current_user.username,
            'user_type': current_user.profile.get('user_type', 'general') if current_user.profile else 'general',
            'running_applications': []  # Would be populated from application manager
        }

        # Get workflow suggestions
        workflow_suggestions = await enhanced_ai_client.generate_workflow_suggestions(user_context)
        
        # Get general AI suggestions
        general_suggestions = [
            {
                'type': 'tip',
                'title': 'Voice Commands',
                'description': 'Try using voice commands like "open firefox" or "create a new document"',
                'priority': 'low'
            },
            {
                'type': 'feature',
                'title': 'Custom Workflows',
                'description': 'Create custom workflows to automate your daily tasks',
                'priority': 'medium'
            }
        ]

        return jsonify({
            'success': True,
            'workflow_suggestions': workflow_suggestions,
            'general_suggestions': general_suggestions,
            'user_context': user_context
        })

    except Exception as e:
        logger.error(f"Failed to get AI suggestions: {e}")
        return jsonify({'error': 'Failed to get AI suggestions'}), 500

@enhanced_v2_bp.route('/ai/conversation-history', methods=['GET'])
@login_required
async def get_conversation_history():
    """Get user's conversation history with the AI"""
    try:
        user_id = str(current_user.id)
        history = enhanced_ai_client.conversation_history.get(user_id, [])
        
        # Format history for display
        formatted_history = []
        for i in range(0, len(history), 2):
            if i + 1 < len(history):
                formatted_history.append({
                    'user_message': history[i]['content'],
                    'ai_response': history[i + 1]['content'],
                    'timestamp': datetime.now().isoformat()  # Would be stored with actual timestamps
                })
        
        return jsonify({
            'success': True,
            'conversation_history': formatted_history[-10:]  # Last 10 exchanges
        })

    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        return jsonify({'error': 'Failed to get conversation history'}), 500

@enhanced_v2_bp.route('/ai/conversation-history', methods=['DELETE'])
@login_required
async def clear_conversation_history():
    """Clear user's conversation history"""
    try:
        user_id = str(current_user.id)
        if user_id in enhanced_ai_client.conversation_history:
            del enhanced_ai_client.conversation_history[user_id]
        
        return jsonify({
            'success': True,
            'message': 'Conversation history cleared'
        })

    except Exception as e:
        logger.error(f"Failed to clear conversation history: {e}")
        return jsonify({'error': 'Failed to clear conversation history'}), 500

@enhanced_v2_bp.route('/system/advanced-status', methods=['GET'])
@login_required
async def get_advanced_system_status():
    """Get comprehensive system status with AI insights"""
    try:
        # Get basic system info
        import psutil
        
        # Get running workflows
        running_workflows = []
        for execution in workflow_engine.executions.values():
            if execution.status.value == 'running':
                running_workflows.append({
                    'execution_id': execution.id,
                    'workflow_id': execution.workflow_id,
                    'current_step': execution.current_step,
                    'started_at': execution.started_at.isoformat()
                })
        
        # Get AI interaction stats
        recent_interactions = AIInteraction.query.filter_by(user_id=current_user.id)\
            .order_by(AIInteraction.created_at.desc()).limit(10).all()
        
        interaction_stats = {
            'total_interactions': len(recent_interactions),
            'successful_interactions': len([i for i in recent_interactions if i.success]),
            'recent_intents': [i.interaction_type for i in recent_interactions[:5]]
        }
        
        system_status = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'running_workflows': running_workflows,
            'ai_interaction_stats': interaction_stats,
            'system_uptime': psutil.boot_time(),
            'active_processes': len(psutil.pids())
        }
        
        return jsonify({
            'success': True,
            'system_status': system_status
        })

    except Exception as e:
        logger.error(f"Failed to get advanced system status: {e}")
        return jsonify({'error': 'Failed to get advanced system status'}), 500

@enhanced_v2_bp.route('/user/preferences', methods=['GET'])
@login_required
async def get_user_preferences():
    """Get user preferences for AI and system behavior"""
    try:
        preferences = current_user.profile.get('preferences', {}) if current_user.profile else {}
        
        # Default preferences
        default_preferences = {
            'ai_voice_enabled': True,
            'auto_suggestions': True,
            'workflow_notifications': True,
            'preferred_applications': [],
            'ui_theme': 'dark',
            'language': 'en'
        }
        
        # Merge with user preferences
        merged_preferences = {**default_preferences, **preferences}
        
        return jsonify({
            'success': True,
            'preferences': merged_preferences
        })

    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        return jsonify({'error': 'Failed to get user preferences'}), 500

@enhanced_v2_bp.route('/user/preferences', methods=['PUT'])
@login_required
async def update_user_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update user profile with new preferences
        if not current_user.profile:
            current_user.profile = {}
        
        if 'preferences' not in current_user.profile:
            current_user.profile['preferences'] = {}
        
        current_user.profile['preferences'].update(data)
        current_user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully',
            'preferences': current_user.profile['preferences']
        })

    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update user preferences'}), 500

# Error handlers for the enhanced v2 blueprint
@enhanced_v2_bp.errorhandler(404)
def enhanced_v2_not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@enhanced_v2_bp.errorhandler(500)
def enhanced_v2_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

