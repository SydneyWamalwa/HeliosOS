"""
Enhanced AI Routes for HeliosOS

This module provides Flask routes for all AI-powered features including:
- Action automation and pattern learning
- Content processing and summarization
- Innovative AI features and proactive assistance
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Blueprint, request, jsonify, current_app, g
from flask_cors import cross_origin

from .ai_action_automation import get_automation_system
from .ai_content_processor import get_content_processor
from .ai_innovative_features import get_innovative_features

logger = logging.getLogger(__name__)

# Create blueprint for enhanced AI routes
enhanced_ai_bp = Blueprint('enhanced_ai', __name__, url_prefix='/api/ai')

@enhanced_ai_bp.route('/health', methods=['GET'])
@cross_origin()
def ai_health_check():
    """Check health of all AI systems."""
    try:
        automation_system = get_automation_system()
        content_processor = get_content_processor()
        innovative_features = get_innovative_features()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'systems': {
                'action_automation': {
                    'status': 'healthy',
                    'stats': automation_system.get_stats()
                },
                'content_processing': {
                    'status': 'healthy',
                    'stats': content_processor.get_processing_stats()
                },
                'innovative_features': {
                    'status': 'healthy',
                    'features': innovative_features.get_feature_status()
                }
            }
        }
        
        return jsonify(health_status)
    
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Action Automation Routes
@enhanced_ai_bp.route('/command', methods=['POST'])
@cross_origin()
def process_command():
    """Process natural language command."""
    try:
        data = request.get_json()
        command = data.get('command', '')
        context = data.get('context', {})
        
        if not command:
            return jsonify({'error': 'Command is required'}), 400
        
        automation_system = get_automation_system()
        result = automation_system.process_command(command, context)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Command processing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/automation/suggestions', methods=['GET'])
@cross_origin()
def get_automation_suggestions():
    """Get automation suggestions based on user patterns."""
    try:
        automation_system = get_automation_system()
        suggestions = automation_system.get_automation_suggestions()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get automation suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/automation/create', methods=['POST'])
@cross_origin()
def create_automation():
    """Create automation from suggestion."""
    try:
        data = request.get_json()
        sequence_key = data.get('sequence_key', '')
        name = data.get('name', '')
        
        if not sequence_key or not name:
            return jsonify({'error': 'sequence_key and name are required'}), 400
        
        automation_system = get_automation_system()
        success = automation_system.create_automation(sequence_key, name)
        
        return jsonify({
            'success': success,
            'message': f"Automation '{name}' created successfully" if success else "Failed to create automation",
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to create automation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/automation/toggle-learning', methods=['POST'])
@cross_origin()
def toggle_pattern_learning():
    """Toggle pattern learning on/off."""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        
        automation_system = get_automation_system()
        automation_system.toggle_learning(enabled)
        
        return jsonify({
            'success': True,
            'learning_enabled': enabled,
            'message': f"Pattern learning {'enabled' if enabled else 'disabled'}",
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to toggle pattern learning: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Content Processing Routes
@enhanced_ai_bp.route('/summarize', methods=['POST'])
@cross_origin()
def summarize_content():
    """Summarize text content."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        method = data.get('method', 'hybrid')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        content_processor = get_content_processor()
        summary = content_processor.summarize_text(text, method=method)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'method': method,
            'original_length': len(text),
            'summary_length': len(summary),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Text summarization failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/analyze-content', methods=['POST'])
@cross_origin()
def analyze_content():
    """Analyze content and extract insights."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        content_type = data.get('content_type', 'auto')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        content_processor = get_content_processor()
        analysis = content_processor.analyze_content(text, content_type)
        
        return jsonify({
            'success': True,
            'analysis': analysis.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Content analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/process-email', methods=['POST'])
@cross_origin()
def process_email():
    """Process email content."""
    try:
        data = request.get_json()
        email_content = data.get('content', '')
        sender = data.get('sender', '')
        subject = data.get('subject', '')
        
        if not email_content:
            return jsonify({'error': 'Email content is required'}), 400
        
        content_processor = get_content_processor()
        processed_email = content_processor.process_email(email_content, sender, subject)
        
        return jsonify({
            'success': True,
            'processed_email': processed_email.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Email processing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Innovative Features Routes
@enhanced_ai_bp.route('/context/update', methods=['POST'])
@cross_origin()
def update_context():
    """Update user context."""
    try:
        data = request.get_json()
        
        innovative_features = get_innovative_features()
        innovative_features.update_user_context(**data)
        
        return jsonify({
            'success': True,
            'message': 'Context updated successfully',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Context update failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/suggestions/proactive', methods=['GET'])
@cross_origin()
def get_proactive_suggestions():
    """Get proactive suggestions."""
    try:
        innovative_features = get_innovative_features()
        suggestions = innovative_features.get_proactive_suggestions()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get proactive suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/notifications/smart', methods=['GET'])
@cross_origin()
def get_smart_notifications():
    """Get smart notifications."""
    try:
        innovative_features = get_innovative_features()
        notifications = innovative_features.get_smart_notifications()
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get smart notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/notifications/create', methods=['POST'])
@cross_origin()
def create_notification():
    """Create a smart notification."""
    try:
        data = request.get_json()
        title = data.get('title', '')
        message = data.get('message', '')
        priority = data.get('priority', 'normal')
        category = data.get('category', 'general')
        
        if not title or not message:
            return jsonify({'error': 'Title and message are required'}), 400
        
        innovative_features = get_innovative_features()
        success = innovative_features.create_notification(
            title, message, priority=priority, category=category
        )
        
        return jsonify({
            'success': success,
            'message': 'Notification created successfully' if success else 'Failed to create notification',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/ui/adaptations', methods=['GET'])
@cross_origin()
def get_ui_adaptations():
    """Get UI adaptations."""
    try:
        innovative_features = get_innovative_features()
        adaptations = innovative_features.get_ui_adaptations()
        
        return jsonify({
            'success': True,
            'adaptations': adaptations,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get UI adaptations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/voice/command', methods=['POST'])
@cross_origin()
def process_voice_command():
    """Process voice command."""
    try:
        data = request.get_json()
        audio_text = data.get('audio_text', '')
        
        if not audio_text:
            return jsonify({'error': 'Audio text is required'}), 400
        
        innovative_features = get_innovative_features()
        result = innovative_features.process_voice_command(audio_text)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Voice command processing failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/insights/productivity', methods=['GET'])
@cross_origin()
def get_productivity_insights():
    """Get productivity insights."""
    try:
        innovative_features = get_innovative_features()
        insights = innovative_features.get_productivity_insights()
        
        return jsonify({
            'success': True,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get productivity insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/insights/system', methods=['GET'])
@cross_origin()
def get_system_insights():
    """Get comprehensive system insights."""
    try:
        innovative_features = get_innovative_features()
        insights = innovative_features.get_system_insights()
        
        return jsonify({
            'success': True,
            'insights': insights,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get system insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/features/toggle', methods=['POST'])
@cross_origin()
def toggle_feature():
    """Toggle AI feature on/off."""
    try:
        data = request.get_json()
        feature_name = data.get('feature_name', '')
        enabled = data.get('enabled', True)
        
        if not feature_name:
            return jsonify({'error': 'Feature name is required'}), 400
        
        innovative_features = get_innovative_features()
        innovative_features.toggle_feature(feature_name, enabled)
        
        return jsonify({
            'success': True,
            'feature_name': feature_name,
            'enabled': enabled,
            'message': f"Feature '{feature_name}' {'enabled' if enabled else 'disabled'}",
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to toggle feature: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@enhanced_ai_bp.route('/features/status', methods=['GET'])
@cross_origin()
def get_feature_status():
    """Get status of all AI features."""
    try:
        innovative_features = get_innovative_features()
        status = innovative_features.get_feature_status()
        
        return jsonify({
            'success': True,
            'features': status,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to get feature status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Batch processing routes
@enhanced_ai_bp.route('/batch/summarize', methods=['POST'])
@cross_origin()
def batch_summarize():
    """Batch summarize multiple texts."""
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        method = data.get('method', 'hybrid')
        
        if not texts:
            return jsonify({'error': 'Texts array is required'}), 400
        
        content_processor = get_content_processor()
        summaries = []
        
        for i, text in enumerate(texts):
            try:
                summary = content_processor.summarize_text(text, method=method)
                summaries.append({
                    'index': i,
                    'summary': summary,
                    'original_length': len(text),
                    'summary_length': len(summary)
                })
            except Exception as e:
                summaries.append({
                    'index': i,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'summaries': summaries,
            'total_processed': len(summaries),
            'method': method,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Batch summarization failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Error handlers
@enhanced_ai_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors."""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(error),
        'timestamp': datetime.now().isoformat()
    }), 400

@enhanced_ai_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error),
        'timestamp': datetime.now().isoformat()
    }), 500

# Register blueprint function
def register_enhanced_ai_routes(app):
    """Register enhanced AI routes with Flask app."""
    app.register_blueprint(enhanced_ai_bp)
    logger.info("Enhanced AI routes registered successfully")

