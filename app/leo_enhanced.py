"""
Enhanced Leo Interface for HeliosOS
Advanced AI assistant that can receive commands and manipulate all applications
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from app.enhanced_ai_agent import enhanced_ai_agent, CommandContext, ExecutionResult
from app.plugin_system import plugin_manager
from app.models import User, AIInteraction, db

logger = logging.getLogger(__name__)

@dataclass
class LeoResponse:
    """Response from Leo"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    execution_time: float = 0.0
    context_updates: Optional[Dict[str, Any]] = None

class EnhancedLeo:
    """Enhanced Leo AI Assistant with advanced capabilities"""
    
    def __init__(self):
        self.name = "Leo"
        self.version = "2.0.0"
        self.capabilities = [
            "Natural Language Processing",
            "Application Management",
            "System Monitoring",
            "Workflow Automation",
            "Context Awareness",
            "Learning and Adaptation",
            "Plugin System Integration"
        ]
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize components
        self.ai_agent = enhanced_ai_agent
        self.plugin_manager = plugin_manager
        
        # Personality and behavior settings
        self.personality = {
            "helpful": True,
            "proactive": True,
            "learning": True,
            "secure": True,
            "verbose": False
        }
    
    async def initialize(self):
        """Initialize Leo and all components"""
        try:
            logger.info("Initializing Enhanced Leo...")
            
            # Initialize plugin manager
            await self.plugin_manager.load_plugins()
            
            # Discover applications
            await self.ai_agent.discover_applications()
            
            logger.info(f"Leo {self.version} initialized successfully")
            logger.info(f"Capabilities: {', '.join(self.capabilities)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Leo: {e}")
            return False
    
    async def process_command(self, command: str, user_id: str, session_id: str = None) -> LeoResponse:
        """Process a natural language command"""
        start_time = datetime.now()
        
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"{user_id}_{int(datetime.now().timestamp())}"
            
            # Get or create session context
            context = await self._get_session_context(user_id, session_id)
            
            # Security validation
            if not await self._validate_command_security(command, context):
                return LeoResponse(
                    success=False,
                    message="Command not allowed due to security restrictions.",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Try plugin-based command processing first
            plugin_result = await self._try_plugin_processing(command, context)
            if plugin_result:
                result = plugin_result
            else:
                # Use enhanced AI agent
                result = await self.ai_agent.process_command(command, context)
            
            # Update session context
            await self._update_session_context(user_id, session_id, command, result)
            
            # Audit the action
            await self._audit_action(command, context, result)
            
            # Log interaction
            await self._log_interaction(user_id, command, result)
            
            # Generate Leo response
            execution_time = (datetime.now() - start_time).total_seconds()
            
            leo_response = LeoResponse(
                success=result.success,
                message=self._personalize_message(result.message, context),
                data=result.data,
                suggestions=result.suggestions,
                execution_time=execution_time,
                context_updates=self._get_context_updates(context)
            )
            
            return leo_response
            
        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return LeoResponse(
                success=False,
                message="I encountered an error while processing your command. Please try again.",
                execution_time=execution_time
            )
    
    async def _get_session_context(self, user_id: str, session_id: str) -> CommandContext:
        """Get or create session context"""
        try:
            # Get existing session or create new one
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "current_applications": [],
                    "recent_commands": [],
                    "user_preferences": {},
                    "system_state": {}
                }
            
            session = self.active_sessions[session_id]
            
            # Get user preferences from database
            user_preferences = await self._get_user_preferences(user_id)
            
            # Get current system state
            system_state = await self._get_system_state()
            
            # Process context through plugins
            context_dict = {
                "user_id": user_id,
                "session_id": session_id,
                "current_applications": session["current_applications"],
                "recent_commands": session["recent_commands"],
                "user_preferences": user_preferences,
                "system_state": system_state
            }
            
            enhanced_context = await self.plugin_manager.process_context(context_dict)
            
            return CommandContext(
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.now(),
                current_applications=enhanced_context.get("current_applications", []),
                recent_commands=enhanced_context.get("recent_commands", []),
                user_preferences=enhanced_context.get("user_preferences", {}),
                system_state=enhanced_context.get("system_state", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            # Return minimal context
            return CommandContext(
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.now()
            )
    
    async def _validate_command_security(self, command: str, context: CommandContext) -> bool:
        """Validate command through security plugins"""
        try:
            user_context = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "timestamp": context.timestamp.isoformat(),
                "recent_commands": context.recent_commands
            }
            
            return await self.plugin_manager.validate_command_security(command, user_context)
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return False  # Fail secure
    
    async def _try_plugin_processing(self, command: str, context: CommandContext) -> Optional[ExecutionResult]:
        """Try to process command using plugins"""
        try:
            context_dict = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "current_applications": context.current_applications,
                "recent_commands": context.recent_commands,
                "user_preferences": context.user_preferences,
                "system_state": context.system_state
            }
            
            # Find command handler plugin
            handler = await self.plugin_manager.find_command_handler(command, context_dict)
            
            if handler:
                plugin_result = await handler.process_command(command, context_dict)
                
                # Convert plugin result to ExecutionResult
                return ExecutionResult(
                    success=plugin_result.get("success", False),
                    message=plugin_result.get("message", ""),
                    data=plugin_result.get("data"),
                    error=plugin_result.get("error"),
                    execution_time=plugin_result.get("execution_time", 0.0),
                    suggestions=plugin_result.get("suggestions", [])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Plugin processing error: {e}")
            return None
    
    async def _update_session_context(self, user_id: str, session_id: str, command: str, result: ExecutionResult):
        """Update session context after command execution"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Add to recent commands
                session["recent_commands"].append(command)
                if len(session["recent_commands"]) > 10:
                    session["recent_commands"] = session["recent_commands"][-10:]
                
                # Update current applications if relevant
                if result.data and "application" in result.data:
                    app_name = result.data["application"]
                    if result.success and "launch" in command.lower():
                        if app_name not in session["current_applications"]:
                            session["current_applications"].append(app_name)
                    elif result.success and "close" in command.lower():
                        if app_name in session["current_applications"]:
                            session["current_applications"].remove(app_name)
                
                session["last_activity"] = datetime.now()
                
        except Exception as e:
            logger.error(f"Failed to update session context: {e}")
    
    async def _audit_action(self, command: str, context: CommandContext, result: ExecutionResult):
        """Audit action through security plugins"""
        try:
            user_context = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "timestamp": context.timestamp.isoformat()
            }
            
            result_dict = {
                "success": result.success,
                "message": result.message,
                "execution_time": result.execution_time
            }
            
            await self.plugin_manager.audit_action(command, user_context, result_dict)
            
        except Exception as e:
            logger.error(f"Audit error: {e}")
    
    async def _log_interaction(self, user_id: str, command: str, result: ExecutionResult):
        """Log interaction to database"""
        try:
            interaction = AIInteraction(
                user_id=user_id,
                interaction_type='leo_command',
                input_text=command[:1000],
                output_text=result.message[:2000] if result.message else None,
                model_used='leo-enhanced-2.0',
                success=result.success,
                error_message=result.error if not result.success else None,
                response_time=result.execution_time
            )
            
            db.session.add(interaction)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            db.session.rollback()
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from database"""
        try:
            user = User.query.get(user_id)
            if user and user.profile:
                return user.profile.get('preferences', {})
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    async def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        try:
            import psutil
            
            return {
                "cpu_usage": psutil.cpu_percent(interval=0.1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "running_processes": len(psutil.pids()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system state: {e}")
            return {}
    
    def _personalize_message(self, message: str, context: CommandContext) -> str:
        """Personalize message based on context and personality"""
        try:
            # Add personality touches
            if self.personality["helpful"] and "successfully" in message.lower():
                message = f"Great! {message}"
            
            if self.personality["proactive"] and context.recent_commands:
                # Add proactive suggestions based on recent commands
                pass
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to personalize message: {e}")
            return message
    
    def _get_context_updates(self, context: CommandContext) -> Dict[str, Any]:
        """Get context updates to send back to client"""
        return {
            "current_applications": context.current_applications,
            "system_state": context.system_state
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get Leo's current capabilities"""
        try:
            # Get plugin information
            plugins = self.plugin_manager.list_plugins()
            active_plugins = [p for p in plugins if p.status.value == "active"]
            
            # Get application count
            app_count = len(self.ai_agent.applications)
            
            return {
                "name": self.name,
                "version": self.version,
                "capabilities": self.capabilities,
                "plugins": {
                    "total": len(plugins),
                    "active": len(active_plugins),
                    "types": list(set(p.metadata.plugin_type.value for p in active_plugins))
                },
                "applications": {
                    "discovered": app_count,
                    "categories": list(set(app.category for app in self.ai_agent.applications.values()))
                },
                "personality": self.personality
            }
            
        except Exception as e:
            logger.error(f"Failed to get capabilities: {e}")
            return {
                "name": self.name,
                "version": self.version,
                "error": "Failed to get full capabilities"
            }
    
    async def get_suggestions(self, user_id: str, session_id: str = None) -> List[str]:
        """Get personalized suggestions for the user"""
        try:
            context = await self._get_session_context(user_id, session_id or f"{user_id}_suggestions")
            
            # Use AI agent to generate smart suggestions
            result = await self.ai_agent.process_command("what should i do", context)
            
            if result.success and result.suggestions:
                return result.suggestions
            
            # Fallback suggestions
            return [
                "Try saying 'list applications' to see what's available",
                "Ask me to 'open firefox' to start browsing",
                "Say 'show system status' to check your computer's health",
                "Try 'run morning routine' to start your daily workflow"
            ]
            
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return ["Ask me anything! I'm here to help."]
    
    async def handle_application_manipulation(self, app_name: str, action: str, parameters: Dict[str, Any] = None) -> LeoResponse:
        """Handle direct application manipulation requests"""
        try:
            parameters = parameters or {}
            
            # Find appropriate plugin handler
            handler = await self.plugin_manager.find_application_handler(app_name)
            
            if handler:
                if action == "launch":
                    result = await handler.launch_application(app_name, parameters)
                else:
                    result = await handler.control_application(app_name, action, parameters)
                
                return LeoResponse(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    data=result.get("data")
                )
            else:
                # Fallback to AI agent
                command = f"{action} {app_name}"
                if parameters:
                    for key, value in parameters.items():
                        command += f" {key}={value}"
                
                # Create minimal context
                context = CommandContext(
                    user_id="system",
                    session_id="direct_manipulation",
                    timestamp=datetime.now()
                )
                
                result = await self.ai_agent.process_command(command, context)
                
                return LeoResponse(
                    success=result.success,
                    message=result.message,
                    data=result.data,
                    suggestions=result.suggestions
                )
                
        except Exception as e:
            logger.error(f"Failed to handle application manipulation: {e}")
            return LeoResponse(
                success=False,
                message=f"Failed to {action} {app_name}: {str(e)}"
            )
    
    async def execute_workflow(self, workflow_name: str, user_id: str, parameters: Dict[str, Any] = None) -> LeoResponse:
        """Execute a workflow"""
        try:
            parameters = parameters or {}
            
            # Find workflow executor plugin
            executor = await self.plugin_manager.find_workflow_executor(workflow_name)
            
            if executor:
                result = await executor.execute_workflow(workflow_name, parameters)
                
                return LeoResponse(
                    success=result.get("success", False),
                    message=result.get("message", ""),
                    data=result.get("data")
                )
            else:
                # Fallback to AI agent
                command = f"run workflow {workflow_name}"
                
                context = await self._get_session_context(user_id, f"{user_id}_workflow")
                result = await self.ai_agent.process_command(command, context)
                
                return LeoResponse(
                    success=result.success,
                    message=result.message,
                    data=result.data,
                    suggestions=result.suggestions
                )
                
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_name}: {e}")
            return LeoResponse(
                success=False,
                message=f"Failed to execute workflow {workflow_name}: {str(e)}"
            )
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Cleanup old inactive sessions"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            sessions_to_remove = []
            for session_id, session_data in self.active_sessions.items():
                last_activity = session_data.get("last_activity", session_data.get("created_at"))
                if last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            if sessions_to_remove:
                logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")

# Global enhanced Leo instance
enhanced_leo = EnhancedLeo()

