"""
Web Browser Handler Plugin for HeliosOS AI Agent
Handles web browser applications like Firefox, Chrome, etc.
"""

import asyncio
import logging
from typing import Dict, Any
from app.plugin_system import ApplicationHandlerPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)

class WebBrowserHandlerPlugin(ApplicationHandlerPlugin):
    """Plugin for handling web browser applications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_browsers = {
            'firefox': {
                'executable': 'firefox',
                'name': 'Mozilla Firefox',
                'launch_args': []
            },
            'chrome': {
                'executable': 'google-chrome',
                'name': 'Google Chrome',
                'launch_args': ['--no-sandbox']
            },
            'chromium': {
                'executable': 'chromium-browser',
                'name': 'Chromium',
                'launch_args': []
            }
        }
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="WebBrowserHandler",
            version="1.0.0",
            description="Handles web browser applications",
            author="HeliosOS Team",
            plugin_type=PluginType.APPLICATION_HANDLER,
            dependencies=[],
            permissions=["execute_applications"]
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self.logger.info("Web Browser Handler Plugin initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        try:
            self.logger.info("Web Browser Handler Plugin cleaned up")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")
            return False
    
    async def can_handle_application(self, app_name: str) -> bool:
        """Check if this plugin can handle the application"""
        app_name_lower = app_name.lower()
        return any(browser in app_name_lower for browser in self.supported_browsers.keys())
    
    async def launch_application(self, app_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Launch the web browser application"""
        try:
            app_name_lower = app_name.lower()
            browser_info = None
            
            # Find matching browser
            for browser_key, browser_data in self.supported_browsers.items():
                if browser_key in app_name_lower:
                    browser_info = browser_data
                    break
            
            if not browser_info:
                return {
                    'success': False,
                    'message': f'Unsupported browser: {app_name}',
                    'error': 'Browser not supported'
                }
            
            # Prepare launch command
            cmd = [browser_info['executable']] + browser_info['launch_args']
            
            # Add URL if provided
            url = parameters.get('url')
            if url:
                cmd.append(url)
            
            # Launch browser
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.logger.info(f"Launched {browser_info['name']} with PID {process.pid}")
            
            return {
                'success': True,
                'message': f"Successfully launched {browser_info['name']}",
                'data': {
                    'browser': browser_info['name'],
                    'pid': process.pid,
                    'url': url
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to launch browser {app_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to launch {app_name}',
                'error': str(e)
            }
    
    async def control_application(self, app_name: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Control the web browser application"""
        try:
            if action == 'navigate':
                url = parameters.get('url')
                if not url:
                    return {
                        'success': False,
                        'message': 'No URL provided for navigation',
                        'error': 'Missing URL'
                    }
                
                # For now, we'll launch a new instance with the URL
                # In a full implementation, this would communicate with existing browser
                return await self.launch_application(app_name, {'url': url})
            
            elif action == 'close':
                # Use pkill to close browser
                app_name_lower = app_name.lower()
                executable = None
                
                for browser_key, browser_data in self.supported_browsers.items():
                    if browser_key in app_name_lower:
                        executable = browser_data['executable']
                        break
                
                if executable:
                    process = await asyncio.create_subprocess_exec(
                        'pkill', '-f', executable,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    return {
                        'success': True,
                        'message': f'Closed {app_name}',
                        'data': {'action': 'close'}
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Unknown browser: {app_name}',
                        'error': 'Browser not recognized'
                    }
            
            else:
                return {
                    'success': False,
                    'message': f'Unsupported action: {action}',
                    'error': 'Action not supported'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to control browser {app_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to control {app_name}',
                'error': str(e)
            }

