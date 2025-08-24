"""
Enhanced AI Client for HeliosOS
Provides advanced natural language understanding and application-specific AI interactions
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import openai
from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """Structured AI response"""
    content: str
    confidence: float
    intent: str
    entities: Dict[str, Any]
    suggested_actions: List[Dict[str, Any]]
    context: Dict[str, Any]

class EnhancedAIClient:
    """Enhanced AI client with advanced NLU capabilities"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_openai()
        self.conversation_history = {}
        self.application_contexts = {}
        
    def _initialize_openai(self):
        """Initialize OpenAI client if API key is available"""
        try:
            api_key = None
            if has_app_context():
                api_key = current_app.config.get('OPENAI_API_KEY')
            else:
                import os
                api_key = os.getenv('OPENAI_API_KEY')
            
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not found, using fallback methods")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    async def process_natural_language_command(self, command: str, user_context: Dict[str, Any] = None) -> AIResponse:
        """Process natural language command with advanced understanding"""
        try:
            # First, try to use OpenAI for better understanding
            if self.openai_client:
                return await self._process_with_openai(command, user_context)
            else:
                return await self._process_with_fallback(command, user_context)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return AIResponse(
                content="I encountered an error processing your command. Please try again.",
                confidence=0.0,
                intent="error",
                entities={},
                suggested_actions=[],
                context={"error": str(e)}
            )
    
    async def _process_with_openai(self, command: str, user_context: Dict[str, Any] = None) -> AIResponse:
        """Process command using OpenAI API"""
        try:
            # Build system prompt for HeliosOS context
            system_prompt = self._build_system_prompt(user_context)
            
            # Create messages for the conversation
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ]
            
            # Add conversation history if available
            user_id = user_context.get('user_id') if user_context else 'default'
            if user_id in self.conversation_history:
                # Add last few messages for context
                history = self.conversation_history[user_id][-6:]  # Last 3 exchanges
                messages.extend(history)
            
            # Add current command
            messages.append({"role": "user", "content": command})
            
            # Call OpenAI API
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                functions=[
                    {
                        "name": "execute_system_action",
                        "description": "Execute a system action based on user command",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action_type": {
                                    "type": "string",
                                    "enum": ["launch_app", "close_app", "file_operation", "system_info", "search", "workflow"],
                                    "description": "Type of action to execute"
                                },
                                "target": {
                                    "type": "string",
                                    "description": "Target of the action (app name, file name, etc.)"
                                },
                                "parameters": {
                                    "type": "object",
                                    "description": "Additional parameters for the action"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confidence level (0-1) in the interpretation"
                                }
                            },
                            "required": ["action_type", "confidence"]
                        }
                    }
                ],
                function_call="auto"
            )
            
            # Process the response
            message = response.choices[0].message
            
            if message.function_call:
                # AI wants to execute a function
                function_args = json.loads(message.function_call.arguments)
                return self._create_action_response(function_args, command)
            else:
                # Regular conversational response
                return self._create_conversational_response(message.content, command)
                
        except Exception as e:
            logger.error(f"OpenAI processing failed: {e}")
            return await self._process_with_fallback(command, user_context)
    
    def _build_system_prompt(self, user_context: Dict[str, Any] = None) -> str:
        """Build system prompt for HeliosOS AI assistant"""
        base_prompt = """You are Leo, the AI assistant for HeliosOS, a cloud-based operating system. 
        
Your capabilities include:
- Launching and managing applications (LibreOffice, VS Code, Firefox, etc.)
- File operations (create, open, save, search)
- System information and monitoring
- Workflow automation
- Helping users with productivity tasks

Available applications:
- Business: LibreOffice Suite, Odoo ERP, Rocket.Chat
- Development: VS Code, Gitea, Portainer
- General: Firefox, File Manager, Calculator
- Student: Joplin Notes, Zotero

When users give you commands, determine the appropriate action and respond helpfully. 
If you need to execute a system action, use the execute_system_action function.
Always be helpful, concise, and professional."""
        
        if user_context:
            user_type = user_context.get('user_type', 'general')
            if user_type == 'programmer':
                base_prompt += "\n\nThe user is a programmer, so prioritize development tools and coding-related assistance."
            elif user_type == 'student':
                base_prompt += "\n\nThe user is a student, so prioritize educational tools and study assistance."
            elif user_type == 'business':
                base_prompt += "\n\nThe user is a business professional, so prioritize office applications and productivity tools."
        
        return base_prompt
    
    def _create_action_response(self, function_args: Dict[str, Any], original_command: str) -> AIResponse:
        """Create response for action-based commands"""
        action_type = function_args.get('action_type')
        target = function_args.get('target', '')
        parameters = function_args.get('parameters', {})
        confidence = function_args.get('confidence', 0.8)
        
        # Map action types to intents
        intent_map = {
            'launch_app': 'application_launch',
            'close_app': 'application_close',
            'file_operation': 'file_operation',
            'system_info': 'system_info',
            'search': 'search',
            'workflow': 'workflow'
        }
        
        intent = intent_map.get(action_type, 'unknown')
        
        # Create suggested actions
        suggested_actions = [{
            'type': action_type,
            'target': target,
            'parameters': parameters,
            'description': f"Execute {action_type} on {target}" if target else f"Execute {action_type}"
        }]
        
        # Generate appropriate response content
        if action_type == 'launch_app':
            content = f"I'll launch {target} for you."
        elif action_type == 'close_app':
            content = f"I'll close {target} for you."
        elif action_type == 'file_operation':
            operation = parameters.get('operation', 'unknown')
            content = f"I'll {operation} the file {target}."
        elif action_type == 'system_info':
            content = "I'll get the system information for you."
        elif action_type == 'search':
            content = f"I'll search for '{target}' for you."
        elif action_type == 'workflow':
            content = f"I'll execute the {target} workflow for you."
        else:
            content = f"I'll help you with {original_command}."
        
        return AIResponse(
            content=content,
            confidence=confidence,
            intent=intent,
            entities={'target': target, 'parameters': parameters},
            suggested_actions=suggested_actions,
            context={'action_type': action_type, 'original_command': original_command}
        )
    
    def _create_conversational_response(self, content: str, original_command: str) -> AIResponse:
        """Create response for conversational interactions"""
        return AIResponse(
            content=content,
            confidence=0.9,
            intent='conversation',
            entities={},
            suggested_actions=[],
            context={'original_command': original_command, 'type': 'conversational'}
        )
    
    async def _process_with_fallback(self, command: str, user_context: Dict[str, Any] = None) -> AIResponse:
        """Fallback processing using pattern matching"""
        command_lower = command.lower().strip()
        
        # Application launch patterns
        launch_patterns = [
            (r'(?:open|launch|start|run)\s+(.+)', 'application_launch'),
            (r'(?:i want to|can you)\s+(?:open|launch|start)\s+(.+)', 'application_launch')
        ]
        
        # Application close patterns
        close_patterns = [
            (r'(?:close|quit|exit|stop)\s+(.+)', 'application_close'),
            (r'(?:shut down|terminate)\s+(.+)', 'application_close')
        ]
        
        # File operation patterns
        file_patterns = [
            (r'(?:create|make|new)\s+(?:a\s+)?(?:file|document)\s+(?:called\s+|named\s+)?(.+)', 'file_create'),
            (r'(?:open|edit)\s+(?:file\s+)?(.+)', 'file_open'),
            (r'(?:save|write)\s+(?:file\s+)?(?:as\s+)?(.+)', 'file_save')
        ]
        
        # Search patterns
        search_patterns = [
            (r'(?:search|find|look for)\s+(.+)', 'search')
        ]
        
        # System info patterns
        system_patterns = [
            (r'(?:show|display|get)\s+(?:system\s+)?(?:info|information|status)', 'system_info')
        ]
        
        # Try to match patterns
        all_patterns = [
            (launch_patterns, 'launch_app'),
            (close_patterns, 'close_app'),
            (file_patterns, 'file_operation'),
            (search_patterns, 'search'),
            (system_patterns, 'system_info')
        ]
        
        for pattern_group, action_type in all_patterns:
            for pattern, intent in pattern_group:
                match = re.search(pattern, command_lower)
                if match:
                    target = match.group(1).strip() if match.groups() else ''
                    
                    # Resolve application aliases
                    if action_type in ['launch_app', 'close_app']:
                        target = self._resolve_application_alias(target)
                    
                    return AIResponse(
                        content=f"I understand you want to {intent.replace('_', ' ')} {target}." if target else f"I understand you want {intent.replace('_', ' ')}.",
                        confidence=0.8,
                        intent=intent,
                        entities={'target': target},
                        suggested_actions=[{
                            'type': action_type,
                            'target': target,
                            'parameters': {},
                            'description': f"Execute {action_type} on {target}" if target else f"Execute {action_type}"
                        }],
                        context={'pattern_matched': pattern, 'fallback': True}
                    )
        
        # No pattern matched - conversational response
        return AIResponse(
            content="I'm not sure I understand that command. Could you please rephrase it? You can try commands like 'open firefox', 'create a new document', or 'show system status'.",
            confidence=0.3,
            intent='unknown',
            entities={},
            suggested_actions=[],
            context={'fallback': True, 'no_pattern_match': True}
        )
    
    def _resolve_application_alias(self, app_name: str) -> str:
        """Resolve application name using aliases"""
        aliases = {
            'writer': 'libreoffice-writer',
            'word': 'libreoffice-writer',
            'calc': 'libreoffice-calc',
            'excel': 'libreoffice-calc',
            'impress': 'libreoffice-impress',
            'powerpoint': 'libreoffice-impress',
            'code': 'vscode',
            'vs code': 'vscode',
            'visual studio code': 'vscode',
            'browser': 'firefox',
            'web browser': 'firefox',
            'file manager': 'nautilus',
            'files': 'nautilus',
            'terminal': 'gnome-terminal',
            'command line': 'gnome-terminal',
            'notes': 'joplin',
            'calculator': 'gnome-calculator'
        }
        return aliases.get(app_name.lower(), app_name)
    
    async def get_application_specific_help(self, app_name: str, user_query: str) -> AIResponse:
        """Get help for specific application usage"""
        try:
            if self.openai_client:
                system_prompt = f"""You are an expert assistant for {app_name}. 
                Help the user with their question about using {app_name}.
                Provide specific, actionable advice."""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ]
                
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=300
                )
                
                content = response.choices[0].message.content
                
                return AIResponse(
                    content=content,
                    confidence=0.9,
                    intent='application_help',
                    entities={'application': app_name, 'query': user_query},
                    suggested_actions=[],
                    context={'application_specific': True}
                )
            else:
                # Fallback help
                return AIResponse(
                    content=f"I'd be happy to help you with {app_name}. However, I need more specific information to provide detailed assistance. What would you like to do with {app_name}?",
                    confidence=0.6,
                    intent='application_help',
                    entities={'application': app_name},
                    suggested_actions=[],
                    context={'fallback_help': True}
                )
                
        except Exception as e:
            logger.error(f"Error getting application help: {e}")
            return AIResponse(
                content=f"I'm having trouble accessing help for {app_name} right now. Please try again later.",
                confidence=0.3,
                intent='error',
                entities={},
                suggested_actions=[],
                context={'error': str(e)}
            )
    
    async def generate_workflow_suggestions(self, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate workflow suggestions based on user context"""
        try:
            user_type = user_context.get('user_type', 'general')
            time_of_day = datetime.now().hour
            
            suggestions = []
            
            # Time-based suggestions
            if 8 <= time_of_day <= 10:  # Morning
                if user_type == 'business':
                    suggestions.append({
                        'name': 'morning_business_routine',
                        'title': 'Start Your Business Day',
                        'description': 'Open email, calendar, and productivity tools',
                        'commands': ['open firefox', 'open libreoffice calc', 'show system status'],
                        'estimated_time': '2 minutes'
                    })
                elif user_type == 'programmer':
                    suggestions.append({
                        'name': 'dev_environment_setup',
                        'title': 'Setup Development Environment',
                        'description': 'Launch coding tools and project management',
                        'commands': ['open vscode', 'open gitea', 'open terminal'],
                        'estimated_time': '1 minute'
                    })
                elif user_type == 'student':
                    suggestions.append({
                        'name': 'study_session_prep',
                        'title': 'Prepare for Study Session',
                        'description': 'Open note-taking and research tools',
                        'commands': ['open joplin', 'open zotero', 'open firefox'],
                        'estimated_time': '1 minute'
                    })
            
            # Context-based suggestions
            running_apps = user_context.get('running_applications', [])
            if not running_apps:
                suggestions.append({
                    'name': 'quick_start',
                    'title': 'Quick Start',
                    'description': 'Get started with essential applications',
                    'commands': ['open firefox', 'open file manager'],
                    'estimated_time': '30 seconds'
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating workflow suggestions: {e}")
            return []
    
    def update_conversation_history(self, user_id: str, user_message: str, ai_response: str):
        """Update conversation history for context"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ])
        
        # Keep only last 10 messages (5 exchanges)
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

# Global instance
enhanced_ai_client = EnhancedAIClient()

