"""
Plugin System for HeliosOS Enhanced AI Agent
Provides extensible architecture for adding new capabilities and integrations
"""

import os
import json
import logging
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class PluginType(Enum):
    """Types of plugins supported"""
    COMMAND_PROCESSOR = "command_processor"
    APPLICATION_HANDLER = "application_handler"
    CONTEXT_PROCESSOR = "context_processor"
    WORKFLOW_EXECUTOR = "workflow_executor"
    INTEGRATION = "integration"
    SECURITY = "security"

class PluginStatus(Enum):
    """Plugin status"""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    permissions: List[str]
    config_schema: Optional[Dict[str, Any]] = None

@dataclass
class PluginInfo:
    """Plugin information"""
    metadata: PluginMetadata
    module_path: str
    class_name: str
    instance: Optional[Any] = None
    status: PluginStatus = PluginStatus.LOADED
    error_message: Optional[str] = None

class BasePlugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"plugin.{self.__class__.__name__}")
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

class CommandProcessorPlugin(BasePlugin):
    """Base class for command processor plugins"""
    
    @abstractmethod
    async def can_handle_command(self, command: str, context: Dict[str, Any]) -> float:
        """Return confidence score (0.0-1.0) for handling this command"""
        pass
    
    @abstractmethod
    async def process_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the command and return result"""
        pass

class ApplicationHandlerPlugin(BasePlugin):
    """Base class for application handler plugins"""
    
    @abstractmethod
    async def can_handle_application(self, app_name: str) -> bool:
        """Check if this plugin can handle the application"""
        pass
    
    @abstractmethod
    async def launch_application(self, app_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Launch the application"""
        pass
    
    @abstractmethod
    async def control_application(self, app_name: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Control the application"""
        pass

class ContextProcessorPlugin(BasePlugin):
    """Base class for context processor plugins"""
    
    @abstractmethod
    async def process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance context information"""
        pass

class WorkflowExecutorPlugin(BasePlugin):
    """Base class for workflow executor plugins"""
    
    @abstractmethod
    async def can_handle_workflow(self, workflow_name: str) -> bool:
        """Check if this plugin can handle the workflow"""
        pass
    
    @abstractmethod
    async def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        pass

class IntegrationPlugin(BasePlugin):
    """Base class for integration plugins"""
    
    @abstractmethod
    async def get_integration_info(self) -> Dict[str, Any]:
        """Get information about the integration"""
        pass
    
    @abstractmethod
    async def handle_external_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle external requests"""
        pass

class SecurityPlugin(BasePlugin):
    """Base class for security plugins"""
    
    @abstractmethod
    async def validate_command(self, command: str, user_context: Dict[str, Any]) -> bool:
        """Validate if command is allowed for user"""
        pass
    
    @abstractmethod
    async def audit_action(self, action: str, user_context: Dict[str, Any], result: Dict[str, Any]):
        """Audit an action"""
        pass

class PluginManager:
    """Manages plugins for the AI agent"""
    
    def __init__(self, plugins_dir: str = "/tmp/heliosos_plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.plugins: Dict[str, PluginInfo] = {}
        self.active_plugins: Dict[PluginType, List[PluginInfo]] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Initialize plugin type lists
        for plugin_type in PluginType:
            self.active_plugins[plugin_type] = []
    
    async def load_plugins(self):
        """Load all plugins from the plugins directory"""
        try:
            # Load built-in plugins
            await self._load_builtin_plugins()
            
            # Load external plugins
            await self._load_external_plugins()
            
            logger.info(f"Loaded {len(self.plugins)} plugins")
            
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")
    
    async def _load_builtin_plugins(self):
        """Load built-in plugins"""
        builtin_plugins = [
            {
                "name": "WebBrowserHandler",
                "module": "app.plugins.web_browser_plugin",
                "class": "WebBrowserHandlerPlugin"
            },
            {
                "name": "OfficeHandler",
                "module": "app.plugins.office_plugin",
                "class": "OfficeHandlerPlugin"
            },
            {
                "name": "SystemMonitor",
                "module": "app.plugins.system_monitor_plugin",
                "class": "SystemMonitorPlugin"
            },
            {
                "name": "FileManager",
                "module": "app.plugins.file_manager_plugin",
                "class": "FileManagerPlugin"
            }
        ]
        
        for plugin_def in builtin_plugins:
            try:
                await self._load_plugin_from_definition(plugin_def)
            except Exception as e:
                logger.warning(f"Failed to load built-in plugin {plugin_def['name']}: {e}")
    
    async def _load_external_plugins(self):
        """Load external plugins from plugins directory"""
        try:
            for plugin_file in self.plugins_dir.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue
                
                try:
                    await self._load_plugin_from_file(plugin_file)
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {plugin_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to scan plugins directory: {e}")
    
    async def _load_plugin_from_definition(self, plugin_def: Dict[str, str]):
        """Load a plugin from definition"""
        try:
            module_name = plugin_def["module"]
            class_name = plugin_def["class"]
            
            # Try to import the module
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                logger.debug(f"Plugin module {module_name} not found, skipping")
                return
            
            # Get the plugin class
            if not hasattr(module, class_name):
                logger.warning(f"Plugin class {class_name} not found in {module_name}")
                return
            
            plugin_class = getattr(module, class_name)
            
            # Create plugin instance
            config = self.plugin_configs.get(plugin_def["name"], {})
            plugin_instance = plugin_class(config)
            
            # Get metadata
            metadata = plugin_instance.get_metadata()
            
            # Create plugin info
            plugin_info = PluginInfo(
                metadata=metadata,
                module_path=module_name,
                class_name=class_name,
                instance=plugin_instance,
                status=PluginStatus.LOADED
            )
            
            # Initialize plugin
            if await plugin_instance.initialize():
                plugin_info.status = PluginStatus.ACTIVE
                self.active_plugins[metadata.plugin_type].append(plugin_info)
                logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            else:
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = "Initialization failed"
                logger.warning(f"Plugin {metadata.name} failed to initialize")
            
            self.plugins[metadata.name] = plugin_info
            
        except Exception as e:
            logger.error(f"Failed to load plugin from definition: {e}")
    
    async def _load_plugin_from_file(self, plugin_file: Path):
        """Load a plugin from a Python file"""
        try:
            # Read plugin file to find plugin classes
            with open(plugin_file, 'r') as f:
                content = f.read()
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
            if not spec or not spec.loader:
                return
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BasePlugin) and 
                    obj != BasePlugin and 
                    not name.startswith('Base')):
                    
                    # Create plugin instance
                    config = self.plugin_configs.get(name, {})
                    plugin_instance = obj(config)
                    
                    # Get metadata
                    metadata = plugin_instance.get_metadata()
                    
                    # Create plugin info
                    plugin_info = PluginInfo(
                        metadata=metadata,
                        module_path=str(plugin_file),
                        class_name=name,
                        instance=plugin_instance,
                        status=PluginStatus.LOADED
                    )
                    
                    # Initialize plugin
                    if await plugin_instance.initialize():
                        plugin_info.status = PluginStatus.ACTIVE
                        self.active_plugins[metadata.plugin_type].append(plugin_info)
                        logger.info(f"Loaded external plugin: {metadata.name} v{metadata.version}")
                    else:
                        plugin_info.status = PluginStatus.ERROR
                        plugin_info.error_message = "Initialization failed"
                        logger.warning(f"External plugin {metadata.name} failed to initialize")
                    
                    self.plugins[metadata.name] = plugin_info
                    
        except Exception as e:
            logger.error(f"Failed to load plugin from file {plugin_file}: {e}")
    
    async def get_command_processors(self) -> List[CommandProcessorPlugin]:
        """Get all active command processor plugins"""
        return [p.instance for p in self.active_plugins[PluginType.COMMAND_PROCESSOR] 
                if p.status == PluginStatus.ACTIVE]
    
    async def get_application_handlers(self) -> List[ApplicationHandlerPlugin]:
        """Get all active application handler plugins"""
        return [p.instance for p in self.active_plugins[PluginType.APPLICATION_HANDLER] 
                if p.status == PluginStatus.ACTIVE]
    
    async def get_context_processors(self) -> List[ContextProcessorPlugin]:
        """Get all active context processor plugins"""
        return [p.instance for p in self.active_plugins[PluginType.CONTEXT_PROCESSOR] 
                if p.status == PluginStatus.ACTIVE]
    
    async def get_workflow_executors(self) -> List[WorkflowExecutorPlugin]:
        """Get all active workflow executor plugins"""
        return [p.instance for p in self.active_plugins[PluginType.WORKFLOW_EXECUTOR] 
                if p.status == PluginStatus.ACTIVE]
    
    async def get_integrations(self) -> List[IntegrationPlugin]:
        """Get all active integration plugins"""
        return [p.instance for p in self.active_plugins[PluginType.INTEGRATION] 
                if p.status == PluginStatus.ACTIVE]
    
    async def get_security_plugins(self) -> List[SecurityPlugin]:
        """Get all active security plugins"""
        return [p.instance for p in self.active_plugins[PluginType.SECURITY] 
                if p.status == PluginStatus.ACTIVE]
    
    async def find_command_handler(self, command: str, context: Dict[str, Any]) -> Optional[CommandProcessorPlugin]:
        """Find the best plugin to handle a command"""
        best_plugin = None
        best_confidence = 0.0
        
        for plugin in await self.get_command_processors():
            try:
                confidence = await plugin.can_handle_command(command, context)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_plugin = plugin
            except Exception as e:
                logger.error(f"Error checking command handler {plugin.__class__.__name__}: {e}")
        
        return best_plugin if best_confidence > 0.5 else None
    
    async def find_application_handler(self, app_name: str) -> Optional[ApplicationHandlerPlugin]:
        """Find a plugin that can handle an application"""
        for plugin in await self.get_application_handlers():
            try:
                if await plugin.can_handle_application(app_name):
                    return plugin
            except Exception as e:
                logger.error(f"Error checking application handler {plugin.__class__.__name__}: {e}")
        
        return None
    
    async def find_workflow_executor(self, workflow_name: str) -> Optional[WorkflowExecutorPlugin]:
        """Find a plugin that can execute a workflow"""
        for plugin in await self.get_workflow_executors():
            try:
                if await plugin.can_handle_workflow(workflow_name):
                    return plugin
            except Exception as e:
                logger.error(f"Error checking workflow executor {plugin.__class__.__name__}: {e}")
        
        return None
    
    async def validate_command_security(self, command: str, user_context: Dict[str, Any]) -> bool:
        """Validate command through security plugins"""
        for plugin in await self.get_security_plugins():
            try:
                if not await plugin.validate_command(command, user_context):
                    return False
            except Exception as e:
                logger.error(f"Error in security validation {plugin.__class__.__name__}: {e}")
                return False  # Fail secure
        
        return True
    
    async def audit_action(self, action: str, user_context: Dict[str, Any], result: Dict[str, Any]):
        """Audit an action through security plugins"""
        for plugin in await self.get_security_plugins():
            try:
                await plugin.audit_action(action, user_context, result)
            except Exception as e:
                logger.error(f"Error in audit {plugin.__class__.__name__}: {e}")
    
    async def process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process context through all context processor plugins"""
        enhanced_context = context.copy()
        
        for plugin in await self.get_context_processors():
            try:
                plugin_context = await plugin.process_context(enhanced_context)
                enhanced_context.update(plugin_context)
            except Exception as e:
                logger.error(f"Error in context processor {plugin.__class__.__name__}: {e}")
        
        return enhanced_context
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins"""
        return list(self.plugins.values())
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin"""
        try:
            plugin_info = self.plugins.get(plugin_name)
            if not plugin_info:
                return False
            
            # Cleanup old plugin
            if plugin_info.instance:
                await plugin_info.instance.cleanup()
            
            # Remove from active plugins
            for plugin_list in self.active_plugins.values():
                if plugin_info in plugin_list:
                    plugin_list.remove(plugin_info)
            
            # Reload plugin
            if plugin_info.module_path.endswith('.py'):
                await self._load_plugin_from_file(Path(plugin_info.module_path))
            else:
                plugin_def = {
                    "name": plugin_name,
                    "module": plugin_info.module_path,
                    "class": plugin_info.class_name
                }
                await self._load_plugin_from_definition(plugin_def)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_name}: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        try:
            plugin_info = self.plugins.get(plugin_name)
            if not plugin_info:
                return False
            
            # Cleanup plugin
            if plugin_info.instance:
                await plugin_info.instance.cleanup()
            
            # Remove from active plugins
            for plugin_list in self.active_plugins.values():
                if plugin_info in plugin_list:
                    plugin_list.remove(plugin_info)
            
            # Remove from plugins dict
            del self.plugins[plugin_name]
            
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    async def cleanup_all_plugins(self):
        """Cleanup all plugins"""
        for plugin_info in self.plugins.values():
            try:
                if plugin_info.instance:
                    await plugin_info.instance.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_info.metadata.name}: {e}")

# Global plugin manager instance
plugin_manager = PluginManager()

