"""
Health check routes for HeliosOS deployment monitoring
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import os
import psutil

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint for deployment monitoring."""
    try:
        # Check database connection
        from app.extensions import db
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        db_status = 'unhealthy'
    
    # Get system info
    try:
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk_info = psutil.disk_usage('/')
        
        system_info = {
            'memory_used_percent': memory_info.percent,
            'cpu_percent': cpu_percent,
            'disk_used_percent': (disk_info.used / disk_info.total) * 100
        }
    except Exception as e:
        current_app.logger.error(f"System info collection failed: {str(e)}")
        system_info = {'error': 'Unable to collect system info'}
    
    # Overall health status
    overall_status = 'healthy' if db_status == 'healthy' else 'degraded'
    
    health_data = {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'services': {
            'database': db_status,
            'ai_fallback': 'healthy'  # Our fallback AI is always available
        },
        'system': system_info
    }
    
    status_code = 200 if overall_status == 'healthy' else 503
    return jsonify(health_data), status_code

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check for deployment."""
    try:
        # Check if all critical services are ready
        from app.extensions import db
        db.session.execute('SELECT 1')
        
        # Check if AI fallback modules are available
        from app.ai_fallback_modules import get_automation_system
        automation_system = get_automation_system()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': 'ready',
                'ai_fallback': 'ready'
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Liveness check for deployment."""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

