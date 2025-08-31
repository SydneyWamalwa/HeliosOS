"""
Enhanced AI Agent for HeliosOS
Advanced AI system that can receive commands via Leo and manipulate all applications
including dynamically installed ones.
"""

import os
import re
import json
import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import psutil
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentCapability(Enum):
    """Capabilities of the AI agent"""
    APPLICATION_MANAGEMENT = "application_management"
    SYSTEM_MONITORING = "system_monitoring"
    FILE_OPERATIONS = "file_operations"
    WORKFLOW_AUTOMATION = "workflow_automation"
    CONTEXT_AWARENESS = "context_awareness"
    LEARNING = "learning"
    SECURITY = "security"

class CommandComplexity(Enum):
    """Complexity levels of commands"""
    SIMPLE = "simple"          # Single action commands
    COMPOUND = "compound"      # Multiple related actions
    WORKFLOW = "workflow"      # Complex multi-step processes
    ADAPTIVE = "adaptive"      # Context-dependent actions

@dataclass
class ApplicationInfo:
    """Information about an application"""
    name: str
    executable: str
    category: str
    description: str
    version: Optional[str] = None
    installed_path: Optional[str] = None
    desktop_file: Optional[str] = None
    is_running: bool = False
    pid: Optional[int] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    user_rating: Optional[float] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class CommandContext:
    """Context information for command execution"""
    user_id: str
    session_id: str
    timestamp: datetime
    location: Optional[str] = None
    current_applications: List[str] = field(default_factory=list)
    recent_commands: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    side_effects: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

class EnhancedAIAgent:
    """Enhanced AI Agent with advanced capabilities"""
    
    def __init__(self, data_dir: str = "/tmp/heliosos_agent"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize databases
        self.db_path = self.data_dir / "agent.db"
        self._init_database()
        
        # Application registry
        self.applications: Dict[str, ApplicationInfo] = {}
        self.application_aliases: Dict[str, str] = {}
        
        # Command patterns and processors
        self.command_patterns = self._init_command_patterns()
        self.context_processors = self._init_context_processors()
        
        # Learning and adaptation
        self.command_history: List[Dict[str, Any]] = []
        self.user_patterns: Dict[str, Any] = {}
        
        # Initialize capabilities
        self._init_capabilities()
        
        # Start background tasks
        asyncio.create_task(self._background_monitor())
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    name TEXT PRIMARY KEY,
                    executable TEXT,
                    category TEXT,
                    description TEXT,
                    version TEXT,
                    installed_path TEXT,
                    desktop_file TEXT,
                    usage_count INTEGER DEFAULT 0,
                    user_rating REAL,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Command history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_id TEXT,
                    command_text TEXT,
                    intent TEXT,
                    success BOOLEAN,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    preferences TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Application usage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS application_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    app_name TEXT,
                    action TEXT,
                    duration INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _init_command_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize enhanced command patterns with better NLP"""
        return {
            # Application management
            "app_launch": [
                {
                    "patterns": [
                        r"(?:open|launch|start|run|execute)\s+(.+)",
                        r"(?:i want to|can you|please)\s+(?:open|launch|start)\s+(.+)",
                        r"(?:show me|display)\s+(.+)",
                        r"(?:bring up|fire up)\s+(.+)"
                    ],
                    "confidence": 0.9,
                    "extract": "application"
                }
            ],
            "app_close": [
                {
                    "patterns": [
                        r"(?:close|quit|exit|stop|kill|terminate)\s+(.+)",
                        r"(?:shut down|turn off)\s+(.+)",
                        r"(?:i'm done with|finished with)\s+(.+)"
                    ],
                    "confidence": 0.9,
                    "extract": "application"
                }
            ],
            "app_switch": [
                {
                    "patterns": [
                        r"(?:switch to|go to|focus on)\s+(.+)",
                        r"(?:bring|show)\s+(.+)\s+(?:to front|forward)"
                    ],
                    "confidence": 0.8,
                    "extract": "application"
                }
            ],
            
            # System operations
            "system_status": [
                {
                    "patterns": [
                        r"(?:show|display|get|check)\s+(?:system\s+)?(?:status|info|information)",
                        r"(?:how is|what's)\s+(?:the\s+)?(?:system|computer)\s+(?:doing|running)",
                        r"(?:system\s+)?(?:health|performance)\s+(?:check|report)"
                    ],
                    "confidence": 0.9,
                    "extract": None
                }
            ],
            "list_apps": [
                {
                    "patterns": [
                        r"(?:list|show|display)\s+(?:all\s+)?(?:applications|apps|programs)",
                        r"(?:what\s+)?(?:applications|apps|programs)\s+(?:are\s+)?(?:available|installed)",
                        r"(?:show me|tell me)\s+(?:what\s+)?(?:apps|applications)\s+(?:i have|are here)"
                    ],
                    "confidence": 0.9,
                    "extract": None
                }
            ],
            
            # File operations
            "file_create": [
                {
                    "patterns": [
                        r"(?:create|make|new)\s+(?:a\s+)?(?:file|document)\s+(?:called\s+|named\s+)?(.+)",
                        r"(?:touch|create)\s+(.+)",
                        r"(?:new\s+)?(?:file|document)\s+(.+)"
                    ],
                    "confidence": 0.8,
                    "extract": "filename"
                }
            ],
            "file_open": [
                {
                    "patterns": [
                        r"(?:open|edit|view)\s+(?:file\s+)?(.+)",
                        r"(?:show me|display)\s+(?:the\s+)?(?:file\s+)?(.+)"
                    ],
                    "confidence": 0.7,
                    "extract": "filename"
                }
            ],
            
            # Workflow operations
            "workflow_execute": [
                {
                    "patterns": [
                        r"(?:run|execute|start)\s+(?:workflow\s+|routine\s+)?(.+)",
                        r"(?:do\s+)?(?:my\s+)?(.+)\s+(?:workflow|routine)",
                        r"(?:perform|carry out)\s+(.+)\s+(?:sequence|process)"
                    ],
                    "confidence": 0.8,
                    "extract": "workflow"
                }
            ],
            
            # Context-aware commands
            "smart_suggestion": [
                {
                    "patterns": [
                        r"(?:what should i|what can i)\s+(?:do|work on)\s+(?:now|next)",
                        r"(?:suggest|recommend)\s+(?:something|what to do)",
                        r"(?:i'm|i am)\s+(?:bored|free|done)\s*(?:what now|what next)?"
                    ],
                    "confidence": 0.7,
                    "extract": None
                }
            ]
        }
    
    def _init_context_processors(self) -> Dict[str, callable]:
        """Initialize context processors for different scenarios"""
        return {
            "time_based": self._process_time_context,
            "usage_based": self._process_usage_context,
            "application_based": self._process_application_context,
            "user_preference": self._process_user_preference_context
        }
    
    def _init_capabilities(self):
        """Initialize agent capabilities"""
        self.capabilities = {
            AgentCapability.APPLICATION_MANAGEMENT: True,
            AgentCapability.SYSTEM_MONITORING: True,
            AgentCapability.FILE_OPERATIONS: True,
            AgentCapability.WORKFLOW_AUTOMATION: True,
            AgentCapability.CONTEXT_AWARENESS: True,
            AgentCapability.LEARNING: True,
            AgentCapability.SECURITY: True
        }
        logger.info(f"Initialized capabilities: {list(self.capabilities.keys())}")
    
    async def discover_applications(self) -> Dict[str, ApplicationInfo]:
        """Dynamically discover all installed applications"""
        try:
            discovered_apps = {}
            
            # Discover from desktop files
            desktop_dirs = [
                "/usr/share/applications",
                "/usr/local/share/applications",
                "~/.local/share/applications"
            ]
            
            for desktop_dir in desktop_dirs:
                desktop_path = Path(desktop_dir).expanduser()
                if desktop_path.exists():
                    for desktop_file in desktop_path.glob("*.desktop"):
                        app_info = await self._parse_desktop_file(desktop_file)
                        if app_info:
                            discovered_apps[app_info.name] = app_info
            
            # Discover from PATH
            path_apps = await self._discover_path_applications()
            discovered_apps.update(path_apps)
            
            # Discover running processes
            running_apps = await self._discover_running_applications()
            for name, app_info in running_apps.items():
                if name in discovered_apps:
                    discovered_apps[name].is_running = True
                    discovered_apps[name].pid = app_info.pid
                    discovered_apps[name].memory_usage = app_info.memory_usage
                    discovered_apps[name].cpu_usage = app_info.cpu_usage
                else:
                    discovered_apps[name] = app_info
            
            # Update application registry
            self.applications.update(discovered_apps)
            
            # Save to database
            await self._save_applications_to_db(discovered_apps)
            
            logger.info(f"Discovered {len(discovered_apps)} applications")
            return discovered_apps
            
        except Exception as e:
            logger.error(f"Failed to discover applications: {e}")
            return {}
    
    async def _parse_desktop_file(self, desktop_file: Path) -> Optional[ApplicationInfo]:
        """Parse a .desktop file to extract application information"""
        try:
            with open(desktop_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract key information
            name_match = re.search(r'^Name=(.+)$', content, re.MULTILINE)
            exec_match = re.search(r'^Exec=(.+)$', content, re.MULTILINE)
            comment_match = re.search(r'^Comment=(.+)$', content, re.MULTILINE)
            categories_match = re.search(r'^Categories=(.+)$', content, re.MULTILINE)
            
            if not name_match or not exec_match:
                return None
            
            name = name_match.group(1)
            executable = exec_match.group(1).split()[0]  # Get just the command, not args
            description = comment_match.group(1) if comment_match else ""
            categories = categories_match.group(1) if categories_match else ""
            
            # Determine category
            category = self._categorize_application(categories, name, description)
            
            return ApplicationInfo(
                name=name,
                executable=executable,
                category=category,
                description=description,
                desktop_file=str(desktop_file)
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse desktop file {desktop_file}: {e}")
            return None
    
    async def _discover_path_applications(self) -> Dict[str, ApplicationInfo]:
        """Discover applications available in PATH"""
        try:
            apps = {}
            path_dirs = os.environ.get('PATH', '').split(':')
            
            common_apps = [
                'firefox', 'chromium', 'chrome', 'libreoffice', 'gimp', 'vlc',
                'code', 'vim', 'emacs', 'nano', 'gedit', 'kate', 'nautilus',
                'dolphin', 'thunar', 'terminal', 'gnome-terminal', 'konsole',
                'calculator', 'gnome-calculator', 'kcalc'
            ]
            
            for app_name in common_apps:
                for path_dir in path_dirs:
                    app_path = Path(path_dir) / app_name
                    if app_path.exists() and app_path.is_file():
                        apps[app_name] = ApplicationInfo(
                            name=app_name,
                            executable=str(app_path),
                            category=self._categorize_application("", app_name, ""),
                            description=f"Application: {app_name}",
                            installed_path=str(app_path)
                        )
                        break
            
            return apps
            
        except Exception as e:
            logger.error(f"Failed to discover PATH applications: {e}")
            return {}
    
    async def _discover_running_applications(self) -> Dict[str, ApplicationInfo]:
        """Discover currently running applications"""
        try:
            running_apps = {}
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    name = proc_info['name']
                    
                    # Filter out system processes
                    if self._is_user_application(name):
                        running_apps[name] = ApplicationInfo(
                            name=name,
                            executable=name,
                            category="running",
                            description=f"Running process: {name}",
                            is_running=True,
                            pid=proc_info['pid'],
                            memory_usage=proc_info['memory_percent'],
                            cpu_usage=proc_info['cpu_percent']
                        )
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return running_apps
            
        except Exception as e:
            logger.error(f"Failed to discover running applications: {e}")
            return {}
    
    def _categorize_application(self, categories: str, name: str, description: str) -> str:
        """Categorize an application based on available information"""
        categories_lower = categories.lower()
        name_lower = name.lower()
        description_lower = description.lower()
        
        # Category mapping
        if any(cat in categories_lower for cat in ['office', 'wordprocessor', 'spreadsheet']):
            return "office"
        elif any(cat in categories_lower for cat in ['development', 'programming']):
            return "development"
        elif any(cat in categories_lower for cat in ['graphics', 'photography']):
            return "graphics"
        elif any(cat in categories_lower for cat in ['webbrowser', 'network']):
            return "internet"
        elif any(cat in categories_lower for cat in ['audiovideo', 'player']):
            return "multimedia"
        elif any(cat in categories_lower for cat in ['game']):
            return "games"
        elif any(cat in categories_lower for cat in ['system', 'utility']):
            return "system"
        elif any(cat in categories_lower for cat in ['education']):
            return "education"
        
        # Name-based categorization
        if any(word in name_lower for word in ['firefox', 'chrome', 'browser']):
            return "internet"
        elif any(word in name_lower for word in ['office', 'writer', 'calc']):
            return "office"
        elif any(word in name_lower for word in ['gimp', 'inkscape', 'blender']):
            return "graphics"
        elif any(word in name_lower for word in ['terminal', 'console']):
            return "system"
        elif any(word in name_lower for word in ['player', 'vlc']):
            return "multimedia"
        
        return "other"
    
    def _is_user_application(self, process_name: str) -> bool:
        """Determine if a process is a user application"""
        system_processes = {
            'systemd', 'kthreadd', 'ksoftirqd', 'migration', 'rcu_', 'watchdog',
            'dbus', 'NetworkManager', 'pulseaudio', 'gdm', 'Xorg', 'gnome-shell'
        }
        
        return not any(sys_proc in process_name for sys_proc in system_processes)
    
    async def process_command(self, command_text: str, context: CommandContext) -> ExecutionResult:
        """Process a natural language command with enhanced capabilities"""
        start_time = datetime.now()
        
        try:
            # Preprocess command
            processed_command = await self._preprocess_command(command_text, context)
            
            # Parse command with enhanced NLP
            parsed_result = await self._enhanced_parse_command(processed_command, context)
            
            if not parsed_result:
                return ExecutionResult(
                    success=False,
                    message="I couldn't understand that command. Could you please rephrase it?",
                    error="Command parsing failed"
                )
            
            # Execute command with context awareness
            result = await self._execute_enhanced_command(parsed_result, context)
            
            # Learn from execution
            await self._learn_from_execution(command_text, parsed_result, result, context)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing command '{command_text}': {e}")
            return ExecutionResult(
                success=False,
                message="An error occurred while processing your command.",
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _preprocess_command(self, command_text: str, context: CommandContext) -> str:
        """Preprocess command text with context awareness"""
        # Normalize text
        processed = command_text.strip().lower()
        
        # Resolve pronouns and references
        processed = await self._resolve_references(processed, context)
        
        # Expand abbreviations
        processed = await self._expand_abbreviations(processed)
        
        return processed
    
    async def _resolve_references(self, command: str, context: CommandContext) -> str:
        """Resolve pronouns and contextual references"""
        # Simple reference resolution
        if "it" in command and context.current_applications:
            last_app = context.current_applications[-1]
            command = command.replace("it", last_app)
        
        if "that" in command and context.recent_commands:
            # Could refer to last mentioned application
            pass
        
        return command
    
    async def _expand_abbreviations(self, command: str) -> str:
        """Expand common abbreviations"""
        abbreviations = {
            "calc": "calculator",
            "browser": "firefox",
            "editor": "text editor",
            "fm": "file manager"
        }
        
        for abbr, full in abbreviations.items():
            command = command.replace(abbr, full)
        
        return command
    
    async def _enhanced_parse_command(self, command: str, context: CommandContext) -> Optional[Dict[str, Any]]:
        """Enhanced command parsing with better pattern matching"""
        best_match = None
        best_confidence = 0.0
        
        for intent, pattern_groups in self.command_patterns.items():
            for pattern_group in pattern_groups:
                for pattern in pattern_group["patterns"]:
                    match = re.search(pattern, command, re.IGNORECASE)
                    if match:
                        confidence = pattern_group["confidence"]
                        
                        # Boost confidence based on context
                        confidence = await self._adjust_confidence_by_context(
                            confidence, intent, match, context
                        )
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                "intent": intent,
                                "match": match,
                                "pattern_group": pattern_group,
                                "confidence": confidence
                            }
        
        if not best_match or best_confidence < 0.5:
            return None
        
        # Extract parameters
        parameters = await self._extract_parameters(best_match, context)
        
        return {
            "intent": best_match["intent"],
            "parameters": parameters,
            "confidence": best_confidence,
            "original_command": command
        }
    
    async def _adjust_confidence_by_context(self, base_confidence: float, intent: str, 
                                          match: re.Match, context: CommandContext) -> float:
        """Adjust confidence based on context"""
        confidence = base_confidence
        
        # Time-based adjustments
        current_hour = datetime.now().hour
        if intent == "app_launch":
            if 9 <= current_hour <= 17:  # Work hours
                if any(work_app in match.group(0) for work_app in ["office", "calc", "writer"]):
                    confidence += 0.1
        
        # Usage pattern adjustments
        if context.recent_commands:
            similar_commands = [cmd for cmd in context.recent_commands if intent in cmd]
            if similar_commands:
                confidence += 0.05
        
        # Application context adjustments
        if intent.startswith("app_") and context.current_applications:
            # If referring to currently running app, boost confidence
            app_mentioned = match.group(1) if match.lastindex else ""
            if any(app in app_mentioned for app in context.current_applications):
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _extract_parameters(self, match_info: Dict[str, Any], context: CommandContext) -> Dict[str, Any]:
        """Extract parameters from matched command"""
        parameters = {}
        match = match_info["match"]
        pattern_group = match_info["pattern_group"]
        extract_type = pattern_group.get("extract")
        
        if extract_type and match.lastindex:
            extracted_value = match.group(1).strip()
            
            if extract_type == "application":
                # Resolve application name
                app_name = await self._resolve_application_name(extracted_value, context)
                parameters["application"] = app_name
                parameters["raw_application"] = extracted_value
                
            elif extract_type == "filename":
                parameters["filename"] = extracted_value
                
            elif extract_type == "workflow":
                parameters["workflow"] = extracted_value
        
        return parameters
    
    async def _resolve_application_name(self, app_name: str, context: CommandContext) -> str:
        """Resolve application name with enhanced matching"""
        app_name_lower = app_name.lower()
        
        # Direct match
        if app_name_lower in self.applications:
            return app_name_lower
        
        # Alias match
        if app_name_lower in self.application_aliases:
            return self.application_aliases[app_name_lower]
        
        # Fuzzy matching
        best_match = None
        best_score = 0
        
        for app_key, app_info in self.applications.items():
            # Check name similarity
            if app_name_lower in app_key.lower() or app_key.lower() in app_name_lower:
                score = len(app_name_lower) / max(len(app_key), len(app_name_lower))
                if score > best_score:
                    best_score = score
                    best_match = app_key
            
            # Check description similarity
            if app_info.description and app_name_lower in app_info.description.lower():
                score = 0.8
                if score > best_score:
                    best_score = score
                    best_match = app_key
        
        return best_match if best_match and best_score > 0.6 else app_name_lower
    
    async def _execute_enhanced_command(self, parsed_command: Dict[str, Any], 
                                      context: CommandContext) -> ExecutionResult:
        """Execute command with enhanced capabilities"""
        intent = parsed_command["intent"]
        parameters = parsed_command["parameters"]
        
        try:
            if intent.startswith("app_"):
                return await self._execute_application_command(intent, parameters, context)
            elif intent.startswith("system_"):
                return await self._execute_system_command(intent, parameters, context)
            elif intent.startswith("file_"):
                return await self._execute_file_command(intent, parameters, context)
            elif intent.startswith("workflow_"):
                return await self._execute_workflow_command(intent, parameters, context)
            elif intent == "smart_suggestion":
                return await self._execute_smart_suggestion(context)
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Command type '{intent}' is not supported yet.",
                    error="Unsupported command type"
                )
                
        except Exception as e:
            logger.error(f"Error executing command with intent '{intent}': {e}")
            return ExecutionResult(
                success=False,
                message="Failed to execute command.",
                error=str(e)
            )
    
    async def _execute_application_command(self, intent: str, parameters: Dict[str, Any], 
                                         context: CommandContext) -> ExecutionResult:
        """Execute application-related commands"""
        app_name = parameters.get("application")
        
        if not app_name:
            return ExecutionResult(
                success=False,
                message="No application specified.",
                error="Missing application parameter"
            )
        
        if intent == "app_launch":
            return await self._launch_application_enhanced(app_name, context)
        elif intent == "app_close":
            return await self._close_application_enhanced(app_name, context)
        elif intent == "app_switch":
            return await self._switch_application(app_name, context)
        else:
            return ExecutionResult(
                success=False,
                message=f"Application action '{intent}' not supported.",
                error="Unsupported application action"
            )
    
    async def _launch_application_enhanced(self, app_name: str, context: CommandContext) -> ExecutionResult:
        """Launch application with enhanced capabilities"""
        try:
            # Find application info
            app_info = self.applications.get(app_name)
            
            if not app_info:
                # Try to discover if not found
                await self.discover_applications()
                app_info = self.applications.get(app_name)
            
            if not app_info:
                return ExecutionResult(
                    success=False,
                    message=f"Application '{app_name}' not found. Try 'list applications' to see available apps.",
                    error="Application not found",
                    suggestions=[
                        "Try 'list applications' to see what's available",
                        "Check if the application is installed",
                        "Try using a different name for the application"
                    ]
                )
            
            # Check if already running
            if app_info.is_running:
                return ExecutionResult(
                    success=True,
                    message=f"{app_info.name} is already running.",
                    data={"application": app_name, "already_running": True},
                    suggestions=["Try 'switch to {app_name}' to focus on it"]
                )
            
            # Launch the application
            executable = app_info.executable
            
            # Handle different executable formats
            if app_info.desktop_file:
                # Use desktop file for better integration
                process = await asyncio.create_subprocess_exec(
                    "gtk-launch", Path(app_info.desktop_file).stem,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                # Direct executable launch
                process = await asyncio.create_subprocess_exec(
                    executable,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            # Update application info
            app_info.is_running = True
            app_info.pid = process.pid
            app_info.last_used = datetime.now()
            app_info.usage_count += 1
            
            # Update context
            context.current_applications.append(app_name)
            
            # Log usage
            await self._log_application_usage(context.user_id, app_name, "launch")
            
            return ExecutionResult(
                success=True,
                message=f"Successfully launched {app_info.name}.",
                data={
                    "application": app_name,
                    "pid": process.pid,
                    "display_name": app_info.name
                },
                side_effects=[f"Added {app_name} to current applications"],
                suggestions=[
                    f"You can close {app_name} by saying 'close {app_name}'",
                    "Try asking for suggestions if you need help with what to do next"
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to launch application {app_name}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to launch {app_name}: {str(e)}",
                error=str(e)
            )
    
    async def _close_application_enhanced(self, app_name: str, context: CommandContext) -> ExecutionResult:
        """Close application with enhanced capabilities"""
        try:
            app_info = self.applications.get(app_name)
            
            if not app_info or not app_info.is_running:
                return ExecutionResult(
                    success=False,
                    message=f"{app_name} is not currently running.",
                    error="Application not running"
                )
            
            # Try graceful shutdown first
            if app_info.pid:
                try:
                    process = psutil.Process(app_info.pid)
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    await asyncio.sleep(2)
                    
                    if process.is_running():
                        process.kill()
                        
                except psutil.NoSuchProcess:
                    pass  # Already closed
            else:
                # Use pkill as fallback
                process = await asyncio.create_subprocess_exec(
                    "pkill", "-f", app_info.executable,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            # Update application info
            app_info.is_running = False
            app_info.pid = None
            
            # Update context
            if app_name in context.current_applications:
                context.current_applications.remove(app_name)
            
            # Log usage
            await self._log_application_usage(context.user_id, app_name, "close")
            
            return ExecutionResult(
                success=True,
                message=f"Successfully closed {app_info.name}.",
                data={"application": app_name},
                side_effects=[f"Removed {app_name} from current applications"]
            )
            
        except Exception as e:
            logger.error(f"Failed to close application {app_name}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to close {app_name}: {str(e)}",
                error=str(e)
            )
    
    async def _switch_application(self, app_name: str, context: CommandContext) -> ExecutionResult:
        """Switch focus to an application"""
        try:
            app_info = self.applications.get(app_name)
            
            if not app_info or not app_info.is_running:
                return ExecutionResult(
                    success=False,
                    message=f"{app_name} is not currently running. Would you like me to launch it?",
                    error="Application not running",
                    suggestions=[f"Try 'launch {app_name}' to start it first"]
                )
            
            # Use wmctrl to switch to application (if available)
            try:
                process = await asyncio.create_subprocess_exec(
                    "wmctrl", "-a", app_info.name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return ExecutionResult(
                        success=True,
                        message=f"Switched to {app_info.name}.",
                        data={"application": app_name}
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        message=f"Could not switch to {app_name}. Window manager control not available.",
                        error="wmctrl failed"
                    )
                    
            except FileNotFoundError:
                return ExecutionResult(
                    success=False,
                    message=f"Window switching not available. {app_name} is running but cannot be focused programmatically.",
                    error="wmctrl not available"
                )
                
        except Exception as e:
            logger.error(f"Failed to switch to application {app_name}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to switch to {app_name}: {str(e)}",
                error=str(e)
            )
    
    async def _execute_system_command(self, intent: str, parameters: Dict[str, Any], 
                                    context: CommandContext) -> ExecutionResult:
        """Execute system-related commands"""
        if intent == "system_status":
            return await self._get_enhanced_system_status(context)
        elif intent == "list_apps":
            return await self._list_applications_enhanced(context)
        else:
            return ExecutionResult(
                success=False,
                message=f"System command '{intent}' not supported.",
                error="Unsupported system command"
            )
    
    async def _get_enhanced_system_status(self, context: CommandContext) -> ExecutionResult:
        """Get comprehensive system status"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get running applications
            running_apps = [app for app in self.applications.values() if app.is_running]
            
            # Get system uptime
            boot_time = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(boot_time)
            
            status_data = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available // (1024**3),  # GB
                "disk_usage": disk.percent,
                "disk_free": disk.free // (1024**3),  # GB
                "uptime_hours": uptime.total_seconds() // 3600,
                "running_applications": len(running_apps),
                "total_applications": len(self.applications)
            }
            
            # Create status message
            message = f"""System Status:
• CPU Usage: {cpu_percent:.1f}%
• Memory Usage: {memory.percent:.1f}% ({memory.available // (1024**3)} GB available)
• Disk Usage: {disk.percent:.1f}% ({disk.free // (1024**3)} GB free)
• Uptime: {uptime.total_seconds() // 3600:.1f} hours
• Running Applications: {len(running_apps)}/{len(self.applications)}"""
            
            return ExecutionResult(
                success=True,
                message=message,
                data=status_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return ExecutionResult(
                success=False,
                message="Failed to retrieve system status.",
                error=str(e)
            )
    
    async def _list_applications_enhanced(self, context: CommandContext) -> ExecutionResult:
        """List applications with enhanced information"""
        try:
            # Refresh application discovery
            await self.discover_applications()
            
            # Group applications by category
            categories = {}
            for app_name, app_info in self.applications.items():
                category = app_info.category
                if category not in categories:
                    categories[category] = []
                categories[category].append(app_info)
            
            # Create formatted message
            message_parts = ["Available Applications:\n"]
            
            for category, apps in sorted(categories.items()):
                message_parts.append(f"\n{category.title()}:")
                for app in sorted(apps, key=lambda x: x.name):
                    status = " (running)" if app.is_running else ""
                    message_parts.append(f"  • {app.name}{status}")
            
            message = "\n".join(message_parts)
            
            # Prepare data
            app_data = {}
            for app_name, app_info in self.applications.items():
                app_data[app_name] = {
                    "name": app_info.name,
                    "category": app_info.category,
                    "description": app_info.description,
                    "is_running": app_info.is_running,
                    "usage_count": app_info.usage_count
                }
            
            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "applications": app_data,
                    "categories": list(categories.keys()),
                    "total_count": len(self.applications)
                },
                suggestions=[
                    "Try 'open [application name]' to launch an app",
                    "Say 'show system status' for system information"
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to list applications: {e}")
            return ExecutionResult(
                success=False,
                message="Failed to list applications.",
                error=str(e)
            )
    
    async def _execute_file_command(self, intent: str, parameters: Dict[str, Any], 
                                  context: CommandContext) -> ExecutionResult:
        """Execute file operation commands"""
        filename = parameters.get("filename")
        
        if not filename:
            return ExecutionResult(
                success=False,
                message="No filename specified.",
                error="Missing filename parameter"
            )
        
        if intent == "file_create":
            return await self._create_file(filename, context)
        elif intent == "file_open":
            return await self._open_file(filename, context)
        else:
            return ExecutionResult(
                success=False,
                message=f"File operation '{intent}' not supported.",
                error="Unsupported file operation"
            )
    
    async def _create_file(self, filename: str, context: CommandContext) -> ExecutionResult:
        """Create a new file"""
        try:
            # Ensure filename has extension
            if '.' not in filename:
                filename += '.txt'
            
            # Create file path (use user's home directory or current working directory)
            file_path = Path.home() / filename
            
            # Create the file
            file_path.touch()
            
            return ExecutionResult(
                success=True,
                message=f"Created file '{filename}' successfully.",
                data={"filename": filename, "path": str(file_path)},
                suggestions=[f"Try 'open {filename}' to edit the file"]
            )
            
        except Exception as e:
            logger.error(f"Failed to create file {filename}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to create file '{filename}': {str(e)}",
                error=str(e)
            )
    
    async def _open_file(self, filename: str, context: CommandContext) -> ExecutionResult:
        """Open a file with appropriate application"""
        try:
            # Find file path
            file_path = Path.home() / filename
            
            if not file_path.exists():
                return ExecutionResult(
                    success=False,
                    message=f"File '{filename}' not found.",
                    error="File not found",
                    suggestions=[f"Try 'create {filename}' to create the file first"]
                )
            
            # Open with default application
            process = await asyncio.create_subprocess_exec(
                "xdg-open", str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            return ExecutionResult(
                success=True,
                message=f"Opened file '{filename}' successfully.",
                data={"filename": filename, "path": str(file_path)}
            )
            
        except Exception as e:
            logger.error(f"Failed to open file {filename}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to open file '{filename}': {str(e)}",
                error=str(e)
            )
    
    async def _execute_workflow_command(self, intent: str, parameters: Dict[str, Any], 
                                      context: CommandContext) -> ExecutionResult:
        """Execute workflow commands"""
        workflow_name = parameters.get("workflow")
        
        if not workflow_name:
            return ExecutionResult(
                success=False,
                message="No workflow specified.",
                error="Missing workflow parameter"
            )
        
        if intent == "workflow_execute":
            return await self._execute_workflow(workflow_name, context)
        else:
            return ExecutionResult(
                success=False,
                message=f"Workflow operation '{intent}' not supported.",
                error="Unsupported workflow operation"
            )
    
    async def _execute_workflow(self, workflow_name: str, context: CommandContext) -> ExecutionResult:
        """Execute a predefined workflow"""
        try:
            # Define some common workflows
            workflows = {
                "morning": [
                    "open firefox",
                    "open libreoffice-calc",
                    "show system status"
                ],
                "development": [
                    "open code",
                    "open firefox",
                    "open terminal"
                ],
                "office": [
                    "open libreoffice-writer",
                    "open libreoffice-calc",
                    "open firefox"
                ]
            }
            
            workflow_steps = workflows.get(workflow_name.lower())
            
            if not workflow_steps:
                return ExecutionResult(
                    success=False,
                    message=f"Workflow '{workflow_name}' not found.",
                    error="Workflow not found",
                    suggestions=[
                        "Available workflows: morning, development, office",
                        "Try creating a custom workflow"
                    ]
                )
            
            # Execute workflow steps
            results = []
            for step in workflow_steps:
                step_result = await self.process_command(step, context)
                results.append({
                    "step": step,
                    "success": step_result.success,
                    "message": step_result.message
                })
            
            successful_steps = sum(1 for r in results if r["success"])
            
            return ExecutionResult(
                success=successful_steps > 0,
                message=f"Workflow '{workflow_name}' executed: {successful_steps}/{len(workflow_steps)} steps successful.",
                data={
                    "workflow_name": workflow_name,
                    "steps": results,
                    "success_rate": successful_steps / len(workflow_steps)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_name}: {e}")
            return ExecutionResult(
                success=False,
                message=f"Failed to execute workflow '{workflow_name}': {str(e)}",
                error=str(e)
            )
    
    async def _execute_smart_suggestion(self, context: CommandContext) -> ExecutionResult:
        """Provide smart suggestions based on context"""
        try:
            suggestions = []
            
            # Time-based suggestions
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 12:
                suggestions.append("Start your morning routine with 'run morning workflow'")
            elif 13 <= current_hour <= 17:
                suggestions.append("Focus on productivity - try opening LibreOffice or your development environment")
            elif 18 <= current_hour <= 22:
                suggestions.append("Wind down with some light browsing or entertainment apps")
            
            # Usage-based suggestions
            if not context.current_applications:
                suggestions.append("No applications are running. Try 'open firefox' to start browsing")
            elif len(context.current_applications) > 5:
                suggestions.append("You have many apps running. Consider closing some to improve performance")
            
            # User preference suggestions (would be based on learned patterns)
            suggestions.append("Based on your usage patterns, you might want to open your most-used applications")
            
            return ExecutionResult(
                success=True,
                message="Here are some suggestions based on your current context:",
                data={"suggestions": suggestions},
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Failed to generate smart suggestions: {e}")
            return ExecutionResult(
                success=False,
                message="Failed to generate suggestions.",
                error=str(e)
            )
    
    async def _learn_from_execution(self, original_command: str, parsed_command: Dict[str, Any], 
                                  result: ExecutionResult, context: CommandContext):
        """Learn from command execution for future improvements"""
        try:
            # Store in command history
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": context.user_id,
                "session_id": context.session_id,
                "original_command": original_command,
                "parsed_intent": parsed_command["intent"],
                "success": result.success,
                "execution_time": result.execution_time,
                "confidence": parsed_command["confidence"]
            }
            
            self.command_history.append(history_entry)
            
            # Save to database
            await self._save_command_to_db(history_entry)
            
            # Update user patterns
            user_id = context.user_id
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {
                    "common_commands": {},
                    "preferred_applications": {},
                    "usage_times": [],
                    "success_rate": 0.0
                }
            
            # Update patterns
            intent = parsed_command["intent"]
            if intent in self.user_patterns[user_id]["common_commands"]:
                self.user_patterns[user_id]["common_commands"][intent] += 1
            else:
                self.user_patterns[user_id]["common_commands"][intent] = 1
            
            # Update application preferences
            if "application" in parsed_command["parameters"]:
                app_name = parsed_command["parameters"]["application"]
                if app_name in self.user_patterns[user_id]["preferred_applications"]:
                    self.user_patterns[user_id]["preferred_applications"][app_name] += 1
                else:
                    self.user_patterns[user_id]["preferred_applications"][app_name] = 1
            
            # Update usage times
            self.user_patterns[user_id]["usage_times"].append(datetime.now().hour)
            
            # Calculate success rate
            user_commands = [h for h in self.command_history if h["user_id"] == user_id]
            if user_commands:
                success_count = sum(1 for h in user_commands if h["success"])
                self.user_patterns[user_id]["success_rate"] = success_count / len(user_commands)
            
        except Exception as e:
            logger.error(f"Failed to learn from execution: {e}")
    
    async def _save_command_to_db(self, history_entry: Dict[str, Any]):
        """Save command history to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO command_history 
                (user_id, session_id, command_text, intent, success, execution_time, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                history_entry["user_id"],
                history_entry["session_id"],
                history_entry["original_command"],
                history_entry["parsed_intent"],
                history_entry["success"],
                history_entry["execution_time"],
                history_entry["timestamp"]
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save command to database: {e}")
    
    async def _save_applications_to_db(self, applications: Dict[str, ApplicationInfo]):
        """Save applications to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            for app_name, app_info in applications.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO applications 
                    (name, executable, category, description, version, installed_path, 
                     desktop_file, usage_count, user_rating, tags, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    app_info.name,
                    app_info.executable,
                    app_info.category,
                    app_info.description,
                    app_info.version,
                    app_info.installed_path,
                    app_info.desktop_file,
                    app_info.usage_count,
                    app_info.user_rating,
                    json.dumps(app_info.tags),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save applications to database: {e}")
    
    async def _log_application_usage(self, user_id: str, app_name: str, action: str):
        """Log application usage for analytics"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO application_usage (user_id, app_name, action, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, app_name, action, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log application usage: {e}")
    
    async def _background_monitor(self):
        """Background monitoring task"""
        while True:
            try:
                # Update running application status
                await self._update_running_applications()
                
                # Clean old command history
                await self._cleanup_old_data()
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Background monitor error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _update_running_applications(self):
        """Update the running status of applications"""
        try:
            running_processes = {proc.info['name']: proc.info for proc in 
                               psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent'])}
            
            for app_name, app_info in self.applications.items():
                if app_info.executable in running_processes:
                    proc_info = running_processes[app_info.executable]
                    app_info.is_running = True
                    app_info.pid = proc_info['pid']
                    app_info.memory_usage = proc_info['memory_percent']
                    app_info.cpu_usage = proc_info['cpu_percent']
                else:
                    app_info.is_running = False
                    app_info.pid = None
                    app_info.memory_usage = None
                    app_info.cpu_usage = None
                    
        except Exception as e:
            logger.error(f"Failed to update running applications: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old data from database"""
        try:
            # Keep only last 1000 command history entries per user
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM command_history 
                WHERE id NOT IN (
                    SELECT id FROM command_history 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                )
            ''')
            
            # Clean old application usage data (keep last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute('''
                DELETE FROM application_usage 
                WHERE timestamp < ?
            ''', (thirty_days_ago,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    # Context processors
    async def _process_time_context(self, context: CommandContext) -> Dict[str, Any]:
        """Process time-based context"""
        current_time = datetime.now()
        return {
            "hour": current_time.hour,
            "day_of_week": current_time.weekday(),
            "is_weekend": current_time.weekday() >= 5,
            "is_work_hours": 9 <= current_time.hour <= 17
        }
    
    async def _process_usage_context(self, context: CommandContext) -> Dict[str, Any]:
        """Process usage-based context"""
        user_pattern = self.user_patterns.get(context.user_id, {})
        return {
            "common_commands": user_pattern.get("common_commands", {}),
            "preferred_applications": user_pattern.get("preferred_applications", {}),
            "success_rate": user_pattern.get("success_rate", 0.0)
        }
    
    async def _process_application_context(self, context: CommandContext) -> Dict[str, Any]:
        """Process application-based context"""
        running_apps = [app for app in self.applications.values() if app.is_running]
        return {
            "running_count": len(running_apps),
            "running_categories": list(set(app.category for app in running_apps)),
            "high_usage_apps": [app.name for app in running_apps if app.cpu_usage and app.cpu_usage > 10]
        }
    
    async def _process_user_preference_context(self, context: CommandContext) -> Dict[str, Any]:
        """Process user preference context"""
        return context.user_preferences

# Global instance
enhanced_ai_agent = EnhancedAIAgent()

