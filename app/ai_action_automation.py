"""
AI Action Automation Module for HeliosOS

This module provides intelligent action automation capabilities including:
- Natural language command interpretation
- Intent recognition and entity extraction
- Action mapping and execution
- User pattern learning and automation suggestions
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import sqlite3
import threading
from pathlib import Path

from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForTokenClassification, pipeline
)
import torch

logger = logging.getLogger(__name__)

@dataclass
class UserAction:
    """Represents a user action for pattern learning."""
    timestamp: datetime
    action_type: str
    application: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'action_type': self.action_type,
            'application': self.application,
            'parameters': self.parameters or {},
            'context': self.context or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserAction':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            action_type=data['action_type'],
            application=data.get('application'),
            parameters=data.get('parameters'),
            context=data.get('context')
        )

@dataclass
class ActionSequence:
    """Represents a sequence of actions that could be automated."""
    actions: List[UserAction]
    frequency: int
    confidence: float
    suggested_name: str
    
class IntentClassifier:
    """Handles intent recognition from natural language commands."""
    
    def __init__(self):
        self.intent_patterns = {
            'open_application': [
                r'open\s+(\w+)',
                r'launch\s+(\w+)',
                r'start\s+(\w+)',
                r'run\s+(\w+)',
                r'execute\s+(\w+)'
            ],
            'close_application': [
                r'close\s+(\w+)',
                r'quit\s+(\w+)',
                r'exit\s+(\w+)',
                r'stop\s+(\w+)'
            ],
            'search_web': [
                r'search\s+(?:for\s+)?(.+)',
                r'google\s+(.+)',
                r'find\s+(.+)',
                r'look\s+up\s+(.+)'
            ],
            'create_document': [
                r'create\s+(?:a\s+)?(?:new\s+)?(\w+)\s+(?:document|file)',
                r'new\s+(\w+)\s+(?:document|file)',
                r'make\s+(?:a\s+)?(\w+)\s+(?:document|file)'
            ],
            'system_command': [
                r'show\s+system\s+status',
                r'check\s+system\s+health',
                r'system\s+information',
                r'restart\s+system',
                r'shutdown\s+system'
            ],
            'file_operation': [
                r'(?:copy|move|delete)\s+(.+)',
                r'rename\s+(.+)\s+to\s+(.+)',
                r'backup\s+(.+)'
            ],
            'schedule_task': [
                r'schedule\s+(.+)\s+(?:at|for)\s+(.+)',
                r'remind\s+me\s+to\s+(.+)\s+(?:at|in)\s+(.+)',
                r'set\s+(?:a\s+)?(?:reminder|alarm)\s+(.+)'
            ]
        }
        
        # Application mappings
        self.app_mappings = {
            'firefox': ['firefox', 'browser', 'web browser'],
            'chrome': ['chrome', 'google chrome'],
            'terminal': ['terminal', 'console', 'command line', 'cmd'],
            'code': ['code', 'vscode', 'visual studio code', 'editor'],
            'calculator': ['calculator', 'calc'],
            'files': ['files', 'file manager', 'explorer'],
            'settings': ['settings', 'preferences', 'config'],
            'email': ['email', 'mail', 'thunderbird'],
            'music': ['music', 'audio player', 'spotify'],
            'video': ['video', 'video player', 'vlc']
        }
    
    def classify_intent(self, command: str) -> Tuple[str, Dict[str, Any]]:
        """
        Classify user intent from natural language command.
        
        Returns:
            Tuple of (intent, entities) where entities contains extracted information
        """
        command = command.lower().strip()
        entities = {}
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    if intent == 'open_application':
                        app_name = self._resolve_application(match.group(1))
                        entities['application'] = app_name
                    elif intent == 'search_web':
                        entities['query'] = match.group(1).strip()
                    elif intent == 'create_document':
                        entities['document_type'] = match.group(1)
                    elif intent == 'file_operation':
                        entities['operation'] = pattern.split('\\s+')[0].replace('(?:', '').replace('|', ' or ')
                        entities['target'] = match.group(1)
                    elif intent == 'schedule_task':
                        entities['task'] = match.group(1)
                        if len(match.groups()) > 1:
                            entities['time'] = match.group(2)
                    
                    return intent, entities
        
        # Default to general query if no specific intent found
        return 'general_query', {'query': command}
    
    def _resolve_application(self, app_input: str) -> str:
        """Resolve application name from user input."""
        app_input = app_input.lower()
        
        for app_name, aliases in self.app_mappings.items():
            if app_input in aliases:
                return app_name
        
        return app_input

class ActionExecutor:
    """Executes actions based on classified intents."""
    
    def __init__(self):
        self.action_handlers = {
            'open_application': self._open_application,
            'close_application': self._close_application,
            'search_web': self._search_web,
            'create_document': self._create_document,
            'system_command': self._system_command,
            'file_operation': self._file_operation,
            'schedule_task': self._schedule_task,
            'general_query': self._general_query
        }
    
    def execute_action(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action based on intent and entities."""
        handler = self.action_handlers.get(intent, self._general_query)
        
        try:
            result = handler(entities)
            return {
                'success': True,
                'result': result,
                'intent': intent,
                'entities': entities
            }
        except Exception as e:
            logger.error(f"Action execution failed for intent {intent}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'intent': intent,
                'entities': entities
            }
    
    def _open_application(self, entities: Dict[str, Any]) -> str:
        """Handle application opening."""
        app_name = entities.get('application', 'unknown')
        
        # In a real implementation, this would interface with the OS
        # For now, we'll simulate the action
        logger.info(f"Opening application: {app_name}")
        
        return f"Opening {app_name}..."
    
    def _close_application(self, entities: Dict[str, Any]) -> str:
        """Handle application closing."""
        app_name = entities.get('application', 'unknown')
        logger.info(f"Closing application: {app_name}")
        return f"Closing {app_name}..."
    
    def _search_web(self, entities: Dict[str, Any]) -> str:
        """Handle web search."""
        query = entities.get('query', '')
        logger.info(f"Performing web search: {query}")
        return f"Searching the web for: {query}"
    
    def _create_document(self, entities: Dict[str, Any]) -> str:
        """Handle document creation."""
        doc_type = entities.get('document_type', 'text')
        logger.info(f"Creating {doc_type} document")
        return f"Creating new {doc_type} document..."
    
    def _system_command(self, entities: Dict[str, Any]) -> str:
        """Handle system commands."""
        logger.info("Executing system command")
        return "Executing system command..."
    
    def _file_operation(self, entities: Dict[str, Any]) -> str:
        """Handle file operations."""
        operation = entities.get('operation', 'unknown')
        target = entities.get('target', 'unknown')
        logger.info(f"Performing file operation: {operation} on {target}")
        return f"Performing {operation} on {target}..."
    
    def _schedule_task(self, entities: Dict[str, Any]) -> str:
        """Handle task scheduling."""
        task = entities.get('task', 'unknown')
        time_spec = entities.get('time', 'unknown')
        logger.info(f"Scheduling task: {task} at {time_spec}")
        return f"Scheduling task: {task} for {time_spec}"
    
    def _general_query(self, entities: Dict[str, Any]) -> str:
        """Handle general queries."""
        query = entities.get('query', '')
        logger.info(f"Processing general query: {query}")
        return f"I understand you're asking about: {query}. Let me help you with that."

class PatternLearner:
    """Learns user patterns and suggests automation."""
    
    def __init__(self, db_path: str = "user_patterns.db"):
        self.db_path = db_path
        self.action_history: List[UserAction] = []
        self.patterns: Dict[str, ActionSequence] = {}
        self.min_frequency = 3  # Minimum frequency to suggest automation
        self.min_confidence = 0.7  # Minimum confidence to suggest automation
        self._init_database()
        self._load_patterns()
    
    def _init_database(self):
        """Initialize the pattern database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        application TEXT,
                        parameters TEXT,
                        context TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS automation_suggestions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        actions TEXT NOT NULL,
                        frequency INTEGER NOT NULL,
                        confidence REAL NOT NULL,
                        created_at TEXT NOT NULL,
                        accepted BOOLEAN DEFAULT FALSE
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize pattern database: {str(e)}")
    
    def log_action(self, action: UserAction):
        """Log a user action for pattern learning."""
        self.action_history.append(action)
        
        # Store in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO user_actions 
                    (timestamp, action_type, application, parameters, context)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    action.timestamp.isoformat(),
                    action.action_type,
                    action.application,
                    json.dumps(action.parameters) if action.parameters else None,
                    json.dumps(action.context) if action.context else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log action to database: {str(e)}")
        
        # Analyze patterns periodically
        if len(self.action_history) % 10 == 0:
            self._analyze_patterns()
    
    def _load_patterns(self):
        """Load existing patterns from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, action_type, application, parameters, context
                    FROM user_actions
                    ORDER BY timestamp DESC
                    LIMIT 1000
                ''')
                
                for row in cursor:
                    action = UserAction(
                        timestamp=datetime.fromisoformat(row[0]),
                        action_type=row[1],
                        application=row[2],
                        parameters=json.loads(row[3]) if row[3] else None,
                        context=json.loads(row[4]) if row[4] else None
                    )
                    self.action_history.append(action)
        except Exception as e:
            logger.error(f"Failed to load patterns from database: {str(e)}")
    
    def _analyze_patterns(self):
        """Analyze action history to identify patterns."""
        if len(self.action_history) < 5:
            return
        
        # Group actions by time windows
        sequences = self._extract_sequences()
        
        # Find frequent sequences
        sequence_counts = Counter()
        for seq in sequences:
            seq_key = self._sequence_to_key(seq)
            sequence_counts[seq_key] += 1
        
        # Generate suggestions for frequent sequences
        for seq_key, frequency in sequence_counts.items():
            if frequency >= self.min_frequency:
                confidence = min(frequency / len(sequences), 1.0)
                if confidence >= self.min_confidence:
                    actions = self._key_to_sequence(seq_key)
                    suggestion_name = self._generate_suggestion_name(actions)
                    
                    sequence = ActionSequence(
                        actions=actions,
                        frequency=frequency,
                        confidence=confidence,
                        suggested_name=suggestion_name
                    )
                    
                    self.patterns[seq_key] = sequence
    
    def _extract_sequences(self, window_minutes: int = 30) -> List[List[UserAction]]:
        """Extract action sequences within time windows."""
        sequences = []
        current_sequence = []
        
        for i, action in enumerate(self.action_history):
            if not current_sequence:
                current_sequence.append(action)
                continue
            
            # Check if action is within time window
            time_diff = action.timestamp - current_sequence[-1].timestamp
            if time_diff <= timedelta(minutes=window_minutes):
                current_sequence.append(action)
            else:
                # Start new sequence
                if len(current_sequence) >= 2:
                    sequences.append(current_sequence.copy())
                current_sequence = [action]
        
        # Add final sequence if it has multiple actions
        if len(current_sequence) >= 2:
            sequences.append(current_sequence)
        
        return sequences
    
    def _sequence_to_key(self, sequence: List[UserAction]) -> str:
        """Convert action sequence to a hashable key."""
        key_parts = []
        for action in sequence:
            part = f"{action.action_type}"
            if action.application:
                part += f":{action.application}"
            key_parts.append(part)
        return "->".join(key_parts)
    
    def _key_to_sequence(self, key: str) -> List[UserAction]:
        """Convert sequence key back to actions (simplified)."""
        actions = []
        parts = key.split("->")
        
        for part in parts:
            if ":" in part:
                action_type, application = part.split(":", 1)
            else:
                action_type, application = part, None
            
            action = UserAction(
                timestamp=datetime.now(),
                action_type=action_type,
                application=application
            )
            actions.append(action)
        
        return actions
    
    def _generate_suggestion_name(self, actions: List[UserAction]) -> str:
        """Generate a human-readable name for an action sequence."""
        if len(actions) == 1:
            action = actions[0]
            if action.application:
                return f"Open {action.application}"
            return f"Perform {action.action_type}"
        
        # For multiple actions, create a descriptive name
        app_names = [a.application for a in actions if a.application]
        if app_names:
            unique_apps = list(set(app_names))
            if len(unique_apps) == 1:
                return f"Work with {unique_apps[0]}"
            else:
                return f"Multi-app workflow ({', '.join(unique_apps[:2])})"
        
        return f"Custom workflow ({len(actions)} steps)"
    
    def get_automation_suggestions(self) -> List[ActionSequence]:
        """Get current automation suggestions."""
        return list(self.patterns.values())
    
    def create_automation(self, sequence_key: str, name: str) -> bool:
        """Create an automation from a suggested sequence."""
        if sequence_key not in self.patterns:
            return False
        
        sequence = self.patterns[sequence_key]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO automation_suggestions 
                    (name, actions, frequency, confidence, created_at, accepted)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    name,
                    json.dumps([action.to_dict() for action in sequence.actions]),
                    sequence.frequency,
                    sequence.confidence,
                    datetime.now().isoformat(),
                    True
                ))
                conn.commit()
            
            logger.info(f"Created automation: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create automation: {str(e)}")
            return False

class AIActionAutomation:
    """Main class for AI-powered action automation."""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.action_executor = ActionExecutor()
        self.pattern_learner = PatternLearner()
        self.is_learning = True
    
    def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language command and execute the corresponding action.
        
        Args:
            command: Natural language command from user
            context: Optional context information (current app, time, etc.)
        
        Returns:
            Dictionary containing execution result and metadata
        """
        # Classify intent and extract entities
        intent, entities = self.intent_classifier.classify_intent(command)
        
        # Execute the action
        result = self.action_executor.execute_action(intent, entities)
        
        # Log action for pattern learning
        if self.is_learning and result['success']:
            action = UserAction(
                timestamp=datetime.now(),
                action_type=intent,
                application=entities.get('application'),
                parameters=entities,
                context=context
            )
            self.pattern_learner.log_action(action)
        
        return result
    
    def get_automation_suggestions(self) -> List[Dict[str, Any]]:
        """Get current automation suggestions for the user."""
        suggestions = self.pattern_learner.get_automation_suggestions()
        
        return [
            {
                'name': seq.suggested_name,
                'frequency': seq.frequency,
                'confidence': seq.confidence,
                'actions': [action.to_dict() for action in seq.actions],
                'key': self.pattern_learner._sequence_to_key(seq.actions)
            }
            for seq in suggestions
        ]
    
    def create_automation(self, sequence_key: str, name: str) -> bool:
        """Create an automation from a suggestion."""
        return self.pattern_learner.create_automation(sequence_key, name)
    
    def toggle_learning(self, enabled: bool):
        """Enable or disable pattern learning."""
        self.is_learning = enabled
        logger.info(f"Pattern learning {'enabled' if enabled else 'disabled'}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get automation system statistics."""
        return {
            'total_actions_logged': len(self.pattern_learner.action_history),
            'patterns_identified': len(self.pattern_learner.patterns),
            'learning_enabled': self.is_learning,
            'suggestions_available': len(self.get_automation_suggestions())
        }

# Global instance
automation_system = AIActionAutomation()

def get_automation_system() -> AIActionAutomation:
    """Get the global automation system instance."""
    return automation_system

