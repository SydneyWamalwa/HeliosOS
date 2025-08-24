#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced HeliosOS
Tests all major components and integrations
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HeliosOSTestSuite:
    """Comprehensive test suite for HeliosOS"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    async def run_all_tests(self):
        """Run all test suites"""
        self.start_time = time.time()
        logger.info("Starting HeliosOS Enhanced System Tests")
        
        test_suites = [
            ("Core Components", self.test_core_components),
            ("AI Command Processor", self.test_ai_command_processor),
            ("Application Manager", self.test_application_manager),
            ("Workflow Engine", self.test_workflow_engine),
            ("Enhanced AI Client", self.test_enhanced_ai_client),
            ("Database Models", self.test_database_models),
            ("API Routes", self.test_api_routes),
            ("Configuration", self.test_configuration)
        ]
        
        for suite_name, test_func in test_suites:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running {suite_name} Tests")
            logger.info(f"{'='*50}")
            
            try:
                await test_func()
                self.test_results.append({
                    'suite': suite_name,
                    'status': 'PASSED',
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"✅ {suite_name} tests PASSED")
            except Exception as e:
                self.test_results.append({
                    'suite': suite_name,
                    'status': 'FAILED',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"❌ {suite_name} tests FAILED: {e}")
        
        await self.generate_test_report()
    
    async def test_core_components(self):
        """Test core component imports and basic functionality"""
        logger.info("Testing core component imports...")
        
        # Test imports
        try:
            from app import create_app
            from app.models import User, AIInteraction, CommandAudit
            from app.auth import auth_bp
            from app.routes import main_bp
            logger.info("✓ Core imports successful")
        except ImportError as e:
            raise Exception(f"Core import failed: {e}")
        
        # Test Flask app creation
        try:
            app = create_app()
            assert app is not None
            logger.info("✓ Flask app creation successful")
        except Exception as e:
            raise Exception(f"Flask app creation failed: {e}")
        
        # Test app configuration
        try:
            with app.app_context():
                assert app.config['SECRET_KEY'] is not None
                logger.info("✓ App configuration valid")
        except Exception as e:
            raise Exception(f"App configuration invalid: {e}")
    
    async def test_ai_command_processor(self):
        """Test AI command processor functionality"""
        logger.info("Testing AI command processor...")
        
        try:
            from app.ai_command_processor import ai_command_processor, CommandResult
            
            # Test basic command processing
            result = await ai_command_processor.process_command(
                "test command", 
                {"user_id": "test_user"}
            )
            
            assert isinstance(result, CommandResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'message')
            logger.info("✓ AI command processor basic functionality works")
            
        except Exception as e:
            raise Exception(f"AI command processor test failed: {e}")
    
    async def test_application_manager(self):
        """Test application manager functionality"""
        logger.info("Testing application manager...")
        
        try:
            from app.application_manager import application_manager, ApplicationCategory
            
            # Test listing applications
            apps = await application_manager.list_applications()
            assert isinstance(apps, list)
            assert len(apps) > 0
            logger.info(f"✓ Found {len(apps)} applications")
            
            # Test application categories
            business_apps = await application_manager.list_applications(ApplicationCategory.BUSINESS)
            programmer_apps = await application_manager.list_applications(ApplicationCategory.PROGRAMMER)
            student_apps = await application_manager.list_applications(ApplicationCategory.STUDENT)
            
            assert len(business_apps) > 0
            assert len(programmer_apps) > 0
            assert len(student_apps) > 0
            logger.info("✓ Application categorization works")
            
            # Test application info retrieval
            app_info = await application_manager.get_application_info("firefox")
            assert app_info is not None
            assert 'name' in app_info
            logger.info("✓ Application info retrieval works")
            
        except Exception as e:
            raise Exception(f"Application manager test failed: {e}")
    
    async def test_workflow_engine(self):
        """Test workflow engine functionality"""
        logger.info("Testing workflow engine...")
        
        try:
            from app.workflow_engine import workflow_engine, WorkflowStatus
            
            # Test listing workflows
            workflows = await workflow_engine.list_workflows()
            assert isinstance(workflows, list)
            assert len(workflows) > 0
            logger.info(f"✓ Found {len(workflows)} workflows")
            
            # Test workflow templates
            templates = workflow_engine.get_workflow_templates()
            assert isinstance(templates, list)
            assert len(templates) > 0
            logger.info(f"✓ Found {len(templates)} workflow templates")
            
            # Test workflow creation
            test_workflow = {
                'name': 'test_workflow',
                'display_name': 'Test Workflow',
                'description': 'A test workflow',
                'category': 'test',
                'steps': [
                    {
                        'type': 'delay',
                        'name': 'Test Step',
                        'description': 'A test step',
                        'parameters': {'duration': 1}
                    }
                ]
            }
            
            workflow_id = await workflow_engine.create_workflow(test_workflow, 'test_user')
            assert workflow_id is not None
            logger.info("✓ Workflow creation works")
            
            # Clean up test workflow
            workflow_engine.delete_workflow(workflow_id, 'test_user')
            
        except Exception as e:
            raise Exception(f"Workflow engine test failed: {e}")
    
    async def test_enhanced_ai_client(self):
        """Test enhanced AI client functionality"""
        logger.info("Testing enhanced AI client...")
        
        try:
            from app.enhanced_ai_client import enhanced_ai_client, AIResponse
            
            # Test natural language processing (fallback mode)
            response = await enhanced_ai_client.process_natural_language_command(
                "open firefox",
                {"user_id": "test_user", "user_type": "general"}
            )
            
            assert isinstance(response, AIResponse)
            assert hasattr(response, 'content')
            assert hasattr(response, 'confidence')
            assert hasattr(response, 'intent')
            logger.info("✓ Enhanced AI client natural language processing works")
            
            # Test workflow suggestions
            suggestions = await enhanced_ai_client.generate_workflow_suggestions({
                'user_type': 'programmer',
                'running_applications': []
            })
            
            assert isinstance(suggestions, list)
            logger.info(f"✓ Generated {len(suggestions)} workflow suggestions")
            
        except Exception as e:
            raise Exception(f"Enhanced AI client test failed: {e}")
    
    async def test_database_models(self):
        """Test database models"""
        logger.info("Testing database models...")
        
        try:
            from app.models import User, AIInteraction, CommandAudit, UserSession
            from app import create_app, db
            
            app = create_app()
            with app.app_context():
                # Test model creation (without actually saving to DB)
                user = User(
                    username='test_user',
                    email='test@example.com'
                )
                user.set_password('test_password')
                
                assert user.username == 'test_user'
                assert user.check_password('test_password')
                assert not user.check_password('wrong_password')
                logger.info("✓ User model works")
                
                # Test AI interaction model
                interaction = AIInteraction(
                    user_id=1,
                    interaction_type='test',
                    input_text='test input',
                    output_text='test output',
                    model_used='test_model',
                    success=True,
                    response_time=0.5
                )
                
                assert interaction.user_id == 1
                assert interaction.success is True
                logger.info("✓ AIInteraction model works")
                
        except Exception as e:
            raise Exception(f"Database models test failed: {e}")
    
    async def test_api_routes(self):
        """Test API routes structure"""
        logger.info("Testing API routes...")
        
        try:
            from app.routes import main_bp
            from app.auth import auth_bp
            from app.enhanced_routes import enhanced_bp
            from app.enhanced_routes_v2 import enhanced_v2_bp
            
            # Test blueprint registration
            assert main_bp is not None
            assert auth_bp is not None
            assert enhanced_bp is not None
            assert enhanced_v2_bp is not None
            logger.info("✓ All blueprints imported successfully")
            
            # Test blueprint URL prefixes
            assert enhanced_bp.url_prefix == '/api/v2'
            assert enhanced_v2_bp.url_prefix == '/api/v3'
            logger.info("✓ Blueprint URL prefixes correct")
            
        except Exception as e:
            raise Exception(f"API routes test failed: {e}")
    
    async def test_configuration(self):
        """Test configuration files and Docker setup"""
        logger.info("Testing configuration...")
        
        # Test Docker Compose file
        docker_compose_path = Path('docker-compose-enhanced.yml')
        if docker_compose_path.exists():
            logger.info("✓ Docker Compose configuration exists")
        else:
            raise Exception("Docker Compose configuration missing")
        
        # Test Nginx configuration
        nginx_config_path = Path('nginx.conf')
        if nginx_config_path.exists():
            logger.info("✓ Nginx configuration exists")
        else:
            raise Exception("Nginx configuration missing")
        
        # Test enhanced Dockerfile
        dockerfile_path = Path('Dockerfile.enhanced')
        if dockerfile_path.exists():
            logger.info("✓ Enhanced Dockerfile exists")
        else:
            raise Exception("Enhanced Dockerfile missing")
        
        # Test requirements files
        requirements_path = Path('requirements_enhanced.txt')
        if requirements_path.exists():
            logger.info("✓ Enhanced requirements file exists")
        else:
            raise Exception("Enhanced requirements file missing")
        
        # Test frontend structure
        frontend_path = Path('frontend')
        if frontend_path.exists() and frontend_path.is_dir():
            package_json = frontend_path / 'package.json'
            if package_json.exists():
                logger.info("✓ Frontend structure exists")
            else:
                raise Exception("Frontend package.json missing")
        else:
            raise Exception("Frontend directory missing")
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
        total_tests = len(self.test_results)
        
        report = {
            'test_summary': {
                'total_suites': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
                'duration': f"{duration:.2f} seconds",
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'helios_version': '2.0.0-enhanced'
            }
        }
        
        # Save report to file
        report_path = Path('test_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Test Suites: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {report['test_summary']['success_rate']}")
        logger.info(f"Duration: {report['test_summary']['duration']}")
        logger.info(f"Report saved to: {report_path.absolute()}")
        
        if failed_tests > 0:
            logger.error("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    logger.error(f"- {result['suite']}: {result.get('error', 'Unknown error')}")
        else:
            logger.info("\n🎉 All tests passed! HeliosOS Enhanced is ready for deployment.")

async def main():
    """Main test runner"""
    test_suite = HeliosOSTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

