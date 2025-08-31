"""
Office Applications Handler Plugin for HeliosOS AI Agent
Handles LibreOffice and other office applications
"""

import asyncio
import logging
from typing import Dict, Any
from app.plugin_system import ApplicationHandlerPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)

class OfficeHandlerPlugin(ApplicationHandlerPlugin):
    """Plugin for handling office applications"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_apps = {
            'libreoffice-writer': {
                'executable': 'libreoffice',
                'args': ['--writer'],
                'name': 'LibreOffice Writer',
                'description': 'Word processor'
            },
            'libreoffice-calc': {
                'executable': 'libreoffice',
                'args': ['--calc'],
                'name': 'LibreOffice Calc',
                'description': 'Spreadsheet application'
            },
            'libreoffice-impress': {
                'executable': 'libreoffice',
                'args': ['--impress'],
                'name': 'LibreOffice Impress',
                'description': 'Presentation software'
            },
            'libreoffice-draw': {
                'executable': 'libreoffice',
                'args': ['--draw'],
                'name': 'LibreOffice Draw',
                'description': 'Drawing application'
            }
        }
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="OfficeHandler",
            version="1.0.0",
            description="Handles LibreOffice and other office applications",
            author="HeliosOS Team",
            plugin_type=PluginType.APPLICATION_HANDLER,
            dependencies=[],
            permissions=["execute_applications", "file_access"]
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self.logger.info("Office Handler Plugin initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        try:
            self.logger.info("Office Handler Plugin cleaned up")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup: {e}")
            return False
    
    async def can_handle_application(self, app_name: str) -> bool:
        """Check if this plugin can handle the application"""
        app_name_lower = app_name.lower()
        
        # Direct match
        if app_name_lower in self.supported_apps:
            return True
        
        # Partial matches
        office_keywords = [
            'writer', 'word', 'document',
            'calc', 'spreadsheet', 'excel',
            'impress', 'presentation', 'powerpoint',
            'draw', 'drawing'
        ]
        
        return any(keyword in app_name_lower for keyword in office_keywords)
    
    async def launch_application(self, app_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Launch the office application"""
        try:
            app_name_lower = app_name.lower()
            app_info = None
            
            # Find matching application
            if app_name_lower in self.supported_apps:
                app_info = self.supported_apps[app_name_lower]
            else:
                # Try to match by keywords
                if any(word in app_name_lower for word in ['writer', 'word', 'document']):
                    app_info = self.supported_apps['libreoffice-writer']
                elif any(word in app_name_lower for word in ['calc', 'spreadsheet', 'excel']):
                    app_info = self.supported_apps['libreoffice-calc']
                elif any(word in app_name_lower for word in ['impress', 'presentation', 'powerpoint']):
                    app_info = self.supported_apps['libreoffice-impress']
                elif any(word in app_name_lower for word in ['draw', 'drawing']):
                    app_info = self.supported_apps['libreoffice-draw']
            
            if not app_info:
                return {
                    'success': False,
                    'message': f'Unsupported office application: {app_name}',
                    'error': 'Application not supported'
                }
            
            # Prepare launch command
            cmd = [app_info['executable']] + app_info['args']
            
            # Add file to open if provided
            file_path = parameters.get('file')
            if file_path:
                cmd.append(file_path)
            
            # Launch application
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.logger.info(f"Launched {app_info['name']} with PID {process.pid}")
            
            return {
                'success': True,
                'message': f"Successfully launched {app_info['name']}",
                'data': {
                    'application': app_info['name'],
                    'description': app_info['description'],
                    'pid': process.pid,
                    'file': file_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to launch office application {app_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to launch {app_name}',
                'error': str(e)
            }
    
    async def control_application(self, app_name: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Control the office application"""
        try:
            if action == 'open_file':
                file_path = parameters.get('file')
                if not file_path:
                    return {
                        'success': False,
                        'message': 'No file path provided',
                        'error': 'Missing file path'
                    }
                
                # Launch application with file
                return await self.launch_application(app_name, {'file': file_path})
            
            elif action == 'close':
                # Close LibreOffice
                process = await asyncio.create_subprocess_exec(
                    'pkill', '-f', 'libreoffice',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                return {
                    'success': True,
                    'message': f'Closed {app_name}',
                    'data': {'action': 'close'}
                }
            
            elif action == 'create_document':
                doc_type = parameters.get('type', 'writer')
                template = parameters.get('template')
                
                # Map document types
                type_mapping = {
                    'document': 'libreoffice-writer',
                    'text': 'libreoffice-writer',
                    'writer': 'libreoffice-writer',
                    'spreadsheet': 'libreoffice-calc',
                    'calc': 'libreoffice-calc',
                    'presentation': 'libreoffice-impress',
                    'impress': 'libreoffice-impress',
                    'drawing': 'libreoffice-draw',
                    'draw': 'libreoffice-draw'
                }
                
                app_to_launch = type_mapping.get(doc_type.lower(), 'libreoffice-writer')
                launch_params = {}
                
                if template:
                    launch_params['file'] = template
                
                return await self.launch_application(app_to_launch, launch_params)
            
            else:
                return {
                    'success': False,
                    'message': f'Unsupported action: {action}',
                    'error': 'Action not supported'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to control office application {app_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to control {app_name}',
                'error': str(e)
            }

