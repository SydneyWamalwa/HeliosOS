"""
AI Command Processor for HeliosOS
Handles natural language understanding, intent recognition, and command execution
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

class CommandType(Enum):
    """Types of commands the AI can execute"""
    SYSTEM = "system"
    APPLICATION = "application"
    FILE_OPERATION = "file_operation"
    WORKFLOW = "workflow"
    SEARCH = "search"
    UNKNOWN = "unknown"

class ApplicationAction(Enum):
    """Actions that can be performed on applications"""
    LAUNCH = "launch"
    CLOSE = "close"
    SWITCH = "switch"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    INTERACT = "interact"

@dataclass
class ParsedCommand:
    """Represents a parsed natural language command"""
    original_text: str
    command_type: CommandType
    intent: str
    parameters: Dict[str, Any]
    confidence: float
    application: Optional[str] = None
    action: Optional[ApplicationAction] = None

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AICommandProcessor:
    """Main AI command processor for HeliosOS"""
    
    def __init__(self):
        self.command_patterns = self._initialize_command_patterns()
        self.application_aliases = self._initialize_application_aliases()
        self.workflow_definitions = {}
        
    def _initialize_command_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize command patterns for intent recognition"""
        return {
            "application_launch": [
                {
                    "pattern": r"(?:open|launch|start|run)\s+(.+)",
                    "confidence": 0.9,
                    "extract_app": True
                },
                {
                    "pattern": r"(?:i want to|can you)\s+(?:open|launch|start)\s+(.+)",
                    "confidence": 0.8,
                    "extract_app": True
                }
            ],
            "application_close": [
                {
                    "pattern": r"(?:close|quit|exit)\s+(.+)",
                    "confidence": 0.9,
                    "extract_app": True
                },
                {
                    "pattern": r"(?:shut down|terminate)\s+(.+)",
                    "confidence": 0.8,
                    "extract_app": True
                }
            ],
            "file_create": [
                {
                    "pattern": r"(?:create|make|new)\s+(?:a\s+)?(?:file|document)\s+(?:called\s+|named\s+)?(.+)",
                    "confidence": 0.9,
                    "extract_filename": True
                }
            ],
            "file_open": [
                {
                    "pattern": r"(?:open|edit)\s+(?:file\s+)?(.+)",
                    "confidence": 0.8,
                    "extract_filename": True
                }
            ],
            "file_save": [
                {
                    "pattern": r"(?:save|write)\s+(?:file\s+)?(?:as\s+)?(.+)",
                    "confidence": 0.9,
                    "extract_filename": True
                }
            ],
            "search": [
                {
                    "pattern": r"(?:search|find|look for)\s+(.+)",
                    "confidence": 0.8,
                    "extract_query": True
                }
            ],
            "system_info": [
                {
                    "pattern": r"(?:show|display|get)\s+(?:system\s+)?(?:info|information|status)",
                    "confidence": 0.9
                }
            ],
            "workflow": [
                {
                    "pattern": r"(?:run|execute)\s+workflow\s+(.+)",
                    "confidence": 0.9,
                    "extract_workflow": True
                }
            ]
        }
    
    def _initialize_application_aliases(self) -> Dict[str, str]:
        """Initialize application name aliases"""
        return {
            # Office Suite
            "writer": "libreoffice-writer",
            "word processor": "libreoffice-writer",
            "document editor": "libreoffice-writer",
            "calc": "libreoffice-calc",
            "spreadsheet": "libreoffice-calc",
            "excel": "libreoffice-calc",
            "impress": "libreoffice-impress",
            "presentation": "libreoffice-impress",
            "powerpoint": "libreoffice-impress",
            
            # Development Tools
            "code editor": "vscode",
            "vs code": "vscode",
            "visual studio code": "vscode",
            "text editor": "gedit",
            "terminal": "gnome-terminal",
            "command line": "gnome-terminal",
            
            # Web Browser
            "browser": "firefox",
            "web browser": "firefox",
            "firefox": "firefox",
            
            # File Manager
            "file manager": "nautilus",
            "files": "nautilus",
            "explorer": "nautilus",
            
            # Communication
            "chat": "rocket-chat",
            "messaging": "rocket-chat",
            
            # Project Management
            "project manager": "openproject",
            "tasks": "openproject",
            
            # Note Taking
            "notes": "joplin",
            "note taking": "joplin",
            
            # Image Editor
            "image editor": "gimp",
            "photo editor": "gimp",
            
            # Calculator
            "calculator": "gnome-calculator",
            "calc app": "gnome-calculator"
        }
    
    async def process_command(self, command_text: str, user_context: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Process a natural language command and execute it"""
        try:
            # Parse the command
            parsed_command = await self._parse_command(command_text)
            
            if parsed_command.command_type == CommandType.UNKNOWN:
                return CommandResult(
                    success=False,
                    message="I didn't understand that command. Could you please rephrase it?",
                    error="Unknown command type"
                )
            
            # Execute the command
            result = await self._execute_command(parsed_command, user_context)
            
            # Log the command execution
            await self._log_command_execution(parsed_command, result, user_context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing command '{command_text}': {str(e)}")
            return CommandResult(
                success=False,
                message="An error occurred while processing your command.",
                error=str(e)
            )
    
    async def _parse_command(self, command_text: str) -> ParsedCommand:
        """Parse natural language command into structured format"""
        command_text = command_text.strip().lower()
        
        best_match = None
        best_confidence = 0.0
        
        # Try to match against known patterns
        for intent, patterns in self.command_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                confidence = pattern_info["confidence"]
                
                match = re.search(pattern, command_text, re.IGNORECASE)
                if match and confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        "intent": intent,
                        "match": match,
                        "pattern_info": pattern_info
                    }
        
        if not best_match:
            return ParsedCommand(
                original_text=command_text,
                command_type=CommandType.UNKNOWN,
                intent="unknown",
                parameters={},
                confidence=0.0
            )
        
        # Extract parameters based on the matched pattern
        parameters = {}
        intent = best_match["intent"]
        match = best_match["match"]
        pattern_info = best_match["pattern_info"]
        
        if pattern_info.get("extract_app") and match.group(1):
            app_name = match.group(1).strip()
            parameters["application"] = self._resolve_application_name(app_name)
            parameters["raw_app_name"] = app_name
        
        if pattern_info.get("extract_filename") and match.group(1):
            parameters["filename"] = match.group(1).strip()
        
        if pattern_info.get("extract_query") and match.group(1):
            parameters["query"] = match.group(1).strip()
        
        if pattern_info.get("extract_workflow") and match.group(1):
            parameters["workflow_name"] = match.group(1).strip()
        
        # Determine command type and action
        command_type = self._determine_command_type(intent)
        action = self._determine_application_action(intent)
        
        return ParsedCommand(
            original_text=command_text,
            command_type=command_type,
            intent=intent,
            parameters=parameters,
            confidence=best_confidence,
            application=parameters.get("application"),
            action=action
        )
    
    def _resolve_application_name(self, app_name: str) -> str:
        """Resolve application name using aliases"""
        app_name = app_name.lower().strip()
        return self.application_aliases.get(app_name, app_name)
    
    def _determine_command_type(self, intent: str) -> CommandType:
        """Determine command type from intent"""
        if intent.startswith("application_"):
            return CommandType.APPLICATION
        elif intent.startswith("file_"):
            return CommandType.FILE_OPERATION
        elif intent == "search":
            return CommandType.SEARCH
        elif intent == "system_info":
            return CommandType.SYSTEM
        elif intent == "workflow":
            return CommandType.WORKFLOW
        else:
            return CommandType.UNKNOWN
    
    def _determine_application_action(self, intent: str) -> Optional[ApplicationAction]:
        """Determine application action from intent"""
        action_map = {
            "application_launch": ApplicationAction.LAUNCH,
            "application_close": ApplicationAction.CLOSE,
            "application_switch": ApplicationAction.SWITCH,
            "application_minimize": ApplicationAction.MINIMIZE,
            "application_maximize": ApplicationAction.MAXIMIZE
        }
        return action_map.get(intent)
    
    async def _execute_command(self, parsed_command: ParsedCommand, user_context: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Execute the parsed command"""
        try:
            if parsed_command.command_type == CommandType.APPLICATION:
                return await self._execute_application_command(parsed_command)
            elif parsed_command.command_type == CommandType.FILE_OPERATION:
                return await self._execute_file_operation(parsed_command)
            elif parsed_command.command_type == CommandType.SEARCH:
                return await self._execute_search_command(parsed_command)
            elif parsed_command.command_type == CommandType.SYSTEM:
                return await self._execute_system_command(parsed_command)
            elif parsed_command.command_type == CommandType.WORKFLOW:
                return await self._execute_workflow_command(parsed_command)
            else:
                return CommandResult(
                    success=False,
                    message="Command type not supported yet.",
                    error="Unsupported command type"
                )
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return CommandResult(
                success=False,
                message="Failed to execute command.",
                error=str(e)
            )
    
    async def _execute_application_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute application-related commands"""
        app_name = parsed_command.application
        action = parsed_command.action
        
        if not app_name:
            return CommandResult(
                success=False,
                message="No application specified.",
                error="Missing application name"
            )
        
        if action == ApplicationAction.LAUNCH:
            return await self._launch_application(app_name)
        elif action == ApplicationAction.CLOSE:
            return await self._close_application(app_name)
        else:
            return CommandResult(
                success=False,
                message=f"Action {action} not implemented yet.",
                error="Unsupported action"
            )
    
    async def _launch_application(self, app_name: str) -> CommandResult:
        """Launch an application"""
        try:
            # For now, we'll use simple subprocess calls
            # In a full implementation, this would interface with the container orchestration system
            
            # Map application names to actual commands
            app_commands = {
                "libreoffice-writer": ["libreoffice", "--writer"],
                "libreoffice-calc": ["libreoffice", "--calc"],
                "libreoffice-impress": ["libreoffice", "--impress"],
                "firefox": ["firefox"],
                "gnome-terminal": ["gnome-terminal"],
                "nautilus": ["nautilus"],
                "gedit": ["gedit"],
                "gnome-calculator": ["gnome-calculator"],
                "gimp": ["gimp"]
            }
            
            command = app_commands.get(app_name)
            if not command:
                return CommandResult(
                    success=False,
                    message=f"Application '{app_name}' is not available or not supported.",
                    error="Application not found"
                )
            
            # Launch the application in the background
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            return CommandResult(
                success=True,
                message=f"Successfully launched {app_name}.",
                data={"application": app_name, "pid": process.pid}
            )
            
        except Exception as e:
            logger.error(f"Failed to launch application {app_name}: {str(e)}")
            return CommandResult(
                success=False,
                message=f"Failed to launch {app_name}.",
                error=str(e)
            )
    
    async def _close_application(self, app_name: str) -> CommandResult:
        """Close an application"""
        try:
            # Use pkill to close the application
            process = await asyncio.create_subprocess_exec(
                "pkill", "-f", app_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(
                    success=True,
                    message=f"Successfully closed {app_name}.",
                    data={"application": app_name}
                )
            else:
                return CommandResult(
                    success=False,
                    message=f"Could not find or close {app_name}.",
                    error=stderr.decode() if stderr else "Process not found"
                )
                
        except Exception as e:
            logger.error(f"Failed to close application {app_name}: {str(e)}")
            return CommandResult(
                success=False,
                message=f"Failed to close {app_name}.",
                error=str(e)
            )
    
    async def _execute_file_operation(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute file operations"""
        intent = parsed_command.intent
        filename = parsed_command.parameters.get("filename")
        
        if intent == "file_create":
            return await self._create_file(filename)
        elif intent == "file_open":
            return await self._open_file(filename)
        elif intent == "file_save":
            return await self._save_file(filename)
        else:
            return CommandResult(
                success=False,
                message="File operation not supported.",
                error="Unsupported file operation"
            )
    
    async def _create_file(self, filename: str) -> CommandResult:
        """Create a new file"""
        try:
            if not filename:
                return CommandResult(
                    success=False,
                    message="No filename specified.",
                    error="Missing filename"
                )
            
            # Create the file
            with open(filename, 'w') as f:
                f.write("")
            
            return CommandResult(
                success=True,
                message=f"Successfully created file '{filename}'.",
                data={"filename": filename}
            )
            
        except Exception as e:
            logger.error(f"Failed to create file {filename}: {str(e)}")
            return CommandResult(
                success=False,
                message=f"Failed to create file '{filename}'.",
                error=str(e)
            )
    
    async def _open_file(self, filename: str) -> CommandResult:
        """Open a file"""
        try:
            if not filename:
                return CommandResult(
                    success=False,
                    message="No filename specified.",
                    error="Missing filename"
                )
            
            # Open file with default application
            process = await asyncio.create_subprocess_exec(
                "xdg-open", filename,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            return CommandResult(
                success=True,
                message=f"Successfully opened file '{filename}'.",
                data={"filename": filename}
            )
            
        except Exception as e:
            logger.error(f"Failed to open file {filename}: {str(e)}")
            return CommandResult(
                success=False,
                message=f"Failed to open file '{filename}'.",
                error=str(e)
            )
    
    async def _save_file(self, filename: str) -> CommandResult:
        """Save a file (placeholder implementation)"""
        return CommandResult(
            success=True,
            message=f"File save command received for '{filename}'. This would be handled by the active application.",
            data={"filename": filename}
        )
    
    async def _execute_search_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute search commands"""
        query = parsed_command.parameters.get("query")
        
        if not query:
            return CommandResult(
                success=False,
                message="No search query specified.",
                error="Missing search query"
            )
        
        # Placeholder implementation - would integrate with actual search functionality
        return CommandResult(
            success=True,
            message=f"Search initiated for '{query}'. Results would be displayed in the search interface.",
            data={"query": query}
        )
    
    async def _execute_system_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute system commands"""
        if parsed_command.intent == "system_info":
            return await self._get_system_info()
        else:
            return CommandResult(
                success=False,
                message="System command not supported.",
                error="Unsupported system command"
            )
    
    async def _get_system_info(self) -> CommandResult:
        """Get system information"""
        try:
            # Get basic system information
            process = await asyncio.create_subprocess_exec(
                "uname", "-a",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            system_info = stdout.decode().strip() if stdout else "Unknown"
            
            return CommandResult(
                success=True,
                message="System information retrieved.",
                data={"system_info": system_info}
            )
            
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return CommandResult(
                success=False,
                message="Failed to retrieve system information.",
                error=str(e)
            )
    
    async def _execute_workflow_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Execute workflow commands"""
        workflow_name = parsed_command.parameters.get("workflow_name")
        
        if not workflow_name:
            return CommandResult(
                success=False,
                message="No workflow name specified.",
                error="Missing workflow name"
            )
        
        # Placeholder implementation
        return CommandResult(
            success=True,
            message=f"Workflow '{workflow_name}' execution initiated. This feature is under development.",
            data={"workflow_name": workflow_name}
        )
    
    async def _log_command_execution(self, parsed_command: ParsedCommand, result: CommandResult, user_context: Optional[Dict[str, Any]] = None):
        """Log command execution for audit purposes"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "original_command": parsed_command.original_text,
                "parsed_intent": parsed_command.intent,
                "command_type": parsed_command.command_type.value,
                "success": result.success,
                "message": result.message,
                "user_context": user_context or {}
            }
            
            logger.info(f"AI Command Executed: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to log command execution: {str(e)}")

# Global instance
ai_command_processor = AICommandProcessor()

