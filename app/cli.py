"""
Flask CLI Commands for HeliosOS
Provides command-line tools for managing the HeliosOS system
"""

import click
import asyncio
from flask import current_app
from flask.cli import with_appcontext

from app import db
from app.models import User, CommandAudit, AIInteraction
from app.application_manager import application_manager
from app.workflow_engine import workflow_engine


@click.command()
@with_appcontext
def init_db():
    """Initialize the database with tables and default data."""
    click.echo('Initializing database...')
    
    # Create all tables
    db.create_all()
    
    # Create default admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@heliosos.com',
            is_admin=True,
            is_active=True,
            profile={
                'user_type': 'business',
                'display_name': 'System Administrator',
                'preferences': {
                    'theme': 'dark',
                    'notifications': True,
                    'auto_suggestions': True,
                    'workflow_notifications': True
                }
            }
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create demo user
    demo = User.query.filter_by(username='demo').first()
    if not demo:
        demo = User(
            username='demo',
            email='demo@heliosos.com',
            is_admin=False,
            is_active=True,
            profile={
                'user_type': 'casual',
                'display_name': 'Demo User',
                'preferences': {
                    'theme': 'dark',
                    'notifications': True,
                    'auto_suggestions': True,
                    'help_mode': True
                }
            }
        )
        demo.set_password('demo123')
        db.session.add(demo)
    
    # Create student user
    student = User.query.filter_by(username='student').first()
    if not student:
        student = User(
            username='student',
            email='student@heliosos.com',
            is_admin=False,
            is_active=True,
            profile={
                'user_type': 'student',
                'display_name': 'Student User',
                'preferences': {
                    'theme': 'dark',
                    'notifications': True,
                    'auto_suggestions': True,
                    'help_mode': True,
                    'learning_mode': True
                }
            }
        )
        student.set_password('student123')
        db.session.add(student)
    
    # Create programmer user
    programmer = User.query.filter_by(username='programmer').first()
    if not programmer:
        programmer = User(
            username='programmer',
            email='dev@heliosos.com',
            is_admin=False,
            is_active=True,
            profile={
                'user_type': 'programmer',
                'display_name': 'Developer User',
                'preferences': {
                    'theme': 'dark',
                    'notifications': True,
                    'auto_suggestions': True,
                    'workflow_notifications': True,
                    'preferred_applications': ['vscode', 'gitea', 'portainer']
                }
            }
        )
        programmer.set_password('dev123')
        db.session.add(programmer)
    
    db.session.commit()
    click.echo('✅ Database initialized successfully!')
    click.echo('👤 Default users created:')
    click.echo('   • admin / admin123 (Administrator)')
    click.echo('   • demo / demo123 (Casual User)')
    click.echo('   • student / student123 (Student)')
    click.echo('   • programmer / dev123 (Developer)')


@click.command()
@with_appcontext
def reset_db():
    """Reset the database (WARNING: This will delete all data)."""
    if click.confirm('This will delete ALL data. Are you sure?'):
        click.echo('Resetting database...')
        db.drop_all()
        db.create_all()
        click.echo('✅ Database reset complete!')


@click.command()
@with_appcontext
def test_ai():
    """Test AI services."""
    click.echo('Testing AI services...')
    
    try:
        from app.ai_client import get_ai_service
        
        ai_service = get_ai_service()
        health = ai_service.health_check()
        
        click.echo(f'AI Service Status: {health.get("status", "unknown")}')
        
        # Test summarization
        test_text = "This is a test document for the HeliosOS AI system. It contains multiple sentences to test the summarization functionality."
        summary = ai_service.summarize(test_text)
        click.echo(f'Summarization Test: {summary[:100]}...')
        
        # Test chat
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        response = ai_service.chat(messages)
        click.echo(f'Chat Test: {response[:100]}...')
        
        click.echo('✅ AI services are working!')
        
    except Exception as e:
        click.echo(f'❌ AI services error: {e}')


@click.command()
@with_appcontext
def list_apps():
    """List all available applications."""
    click.echo('Available Applications:')
    click.echo('=' * 50)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        apps = loop.run_until_complete(application_manager.list_applications())
        
        for app in apps:
            status = "🟢" if app['status'] == 'running' else "🔴"
            click.echo(f'{status} {app["display_name"]} ({app["name"]}) - {app["category"]}')
            if app.get('web_interface') and app.get('web_port'):
                click.echo(f'   🌐 Web interface: http://localhost:{app["web_port"]}')
        
        click.echo(f'\nTotal applications: {len(apps)}')
        
    except Exception as e:
        click.echo(f'❌ Error listing applications: {e}')


@click.command()
@click.argument('app_name')
@with_appcontext
def start_app(app_name):
    """Start an application."""
    click.echo(f'Starting application: {app_name}')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(application_manager.start_application(app_name))
        
        if result.get('success'):
            click.echo(f'✅ {result.get("message")}')
            if result.get('web_url'):
                click.echo(f'🌐 Access at: {result["web_url"]}')
        else:
            click.echo(f'❌ Failed: {result.get("error")}')
            
    except Exception as e:
        click.echo(f'❌ Error starting application: {e}')


@click.command()
@click.argument('app_name')
@with_appcontext
def stop_app(app_name):
    """Stop an application."""
    click.echo(f'Stopping application: {app_name}')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(application_manager.stop_application(app_name))
        
        if result.get('success'):
            click.echo(f'✅ {result.get("message")}')
        else:
            click.echo(f'❌ Failed: {result.get("error")}')
            
    except Exception as e:
        click.echo(f'❌ Error stopping application: {e}')


@click.command()
@with_appcontext
def list_workflows():
    """List all available workflows."""
    click.echo('Available Workflows:')
    click.echo('=' * 50)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        workflows = loop.run_until_complete(workflow_engine.list_workflows())
        
        for workflow in workflows:
            click.echo(f'🔄 {workflow["display_name"]} ({workflow["name"]})')
            click.echo(f'   Category: {workflow["category"]}')
            click.echo(f'   Steps: {workflow["step_count"]}')
            click.echo(f'   Estimated duration: {workflow["estimated_duration"]}s')
            click.echo()
        
        click.echo(f'Total workflows: {len(workflows)}')
        
    except Exception as e:
        click.echo(f'❌ Error listing workflows: {e}')


@click.command()
@click.argument('workflow_name')
@with_appcontext
def run_workflow(workflow_name):
    """Execute a workflow."""
    click.echo(f'Executing workflow: {workflow_name}')
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Use admin user for CLI execution
        execution_id = loop.run_until_complete(
            workflow_engine.execute_workflow(workflow_name, 'admin')
        )
        
        click.echo(f'✅ Workflow started with execution ID: {execution_id}')
        click.echo('Use "flask workflow-status <execution_id>" to check progress')
        
    except Exception as e:
        click.echo(f'❌ Error executing workflow: {e}')


@click.command('workflow-status')
@click.argument('execution_id')
@with_appcontext
def workflow_status(execution_id):
    """Check workflow execution status."""
    click.echo(f'Checking workflow execution: {execution_id}')
    
    try:
        status = workflow_engine.get_execution_status(execution_id)
        
        if status:
            click.echo(f'Workflow: {status["workflow_name"]}')
            click.echo(f'Status: {status["status"]}')
            click.echo(f'Progress: {status["current_step"]}/{status["total_steps"]}')
            click.echo(f'Started: {status["started_at"]}')
            
            if status["completed_at"]:
                click.echo(f'Completed: {status["completed_at"]}')
                
            if status["error_message"]:
                click.echo(f'Error: {status["error_message"]}')
                
        else:
            click.echo('❌ Execution not found')
            
    except Exception as e:
        click.echo(f'❌ Error checking workflow status: {e}')


@click.command()
@with_appcontext
def stats():
    """Show system statistics."""
    click.echo('HeliosOS System Statistics')
    click.echo('=' * 50)
    
    try:
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        click.echo(f'👥 Users:')
        click.echo(f'   Total: {total_users}')
        click.echo(f'   Active: {active_users}')
        click.echo(f'   Administrators: {admin_users}')
        
        # Command audit statistics
        total_commands = CommandAudit.query.count()
        successful_commands = CommandAudit.query.filter_by(return_code=0).count()
        
        click.echo(f'\n💻 Commands:')
        click.echo(f'   Total executed: {total_commands}')
        click.echo(f'   Successful: {successful_commands}')
        if total_commands > 0:
            success_rate = (successful_commands / total_commands) * 100
            click.echo(f'   Success rate: {success_rate:.1f}%')
        
        # AI interaction statistics
        total_ai = AIInteraction.query.count()
        successful_ai = AIInteraction.query.filter_by(success=True).count()
        
        click.echo(f'\n🤖 AI Interactions:')
        click.echo(f'   Total: {total_ai}')
        click.echo(f'   Successful: {successful_ai}')
        if total_ai > 0:
            ai_success_rate = (successful_ai / total_ai) * 100
            click.echo(f'   Success rate: {ai_success_rate:.1f}%')
        
        # Application statistics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        apps = loop.run_until_complete(application_manager.list_applications())
        running_apps = [app for app in apps if app['status'] == 'running']
        
        click.echo(f'\n🚀 Applications:')
        click.echo(f'   Total available: {len(apps)}')
        click.echo(f'   Currently running: {len(running_apps)}')
        
    except Exception as e:
        click.echo(f'❌ Error getting statistics: {e}')


# Register commands
def register_commands(app):
    """Register all CLI commands with the Flask app."""
    app.cli.add_command(init_db)
    app.cli.add_command(reset_db)
    app.cli.add_command(test_ai)
    app.cli.add_command(list_apps)
    app.cli.add_command(start_app)
    app.cli.add_command(stop_app)
    app.cli.add_command(list_workflows)
    app.cli.add_command(run_workflow)
    app.cli.add_command(workflow_status)
    app.cli.add_command(stats)
