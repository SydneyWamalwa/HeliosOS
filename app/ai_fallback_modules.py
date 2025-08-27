"""
Fallback AI Modules for HeliosOS

These modules provide basic AI functionality without requiring heavy ML dependencies
like transformers, torch, etc. They use simpler algorithms and rule-based approaches.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter, deque
import sqlite3
import threading
from pathlib import Path

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

@dataclass
class ProcessedContent:
    """Represents processed content with metadata."""
    original_text: str
    summary: str
    content_type: str
    language: str = "en"
    confidence: float = 0.0
    keywords: List[str] = None
    sentiment: str = "neutral"
    category: str = "general"
    processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

class FallbackIntentClassifier:
    """Simple rule-based intent classifier."""
    
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
            ]
        }
        
        self.app_mappings = {
            'firefox': ['firefox', 'browser', 'web browser'],
            'chrome': ['chrome', 'google chrome'],
            'terminal': ['terminal', 'console', 'command line', 'cmd'],
            'code': ['code', 'vscode', 'visual studio code', 'editor'],
            'calculator': ['calculator', 'calc'],
            'files': ['files', 'file manager', 'explorer']
        }
    
    def classify_intent(self, command: str) -> Tuple[str, Dict[str, Any]]:
        """Classify user intent from natural language command."""
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
                    
                    return intent, entities
        
        return 'general_query', {'query': command}
    
    def _resolve_application(self, app_input: str) -> str:
        """Resolve application name from user input."""
        app_input = app_input.lower()
        
        for app_name, aliases in self.app_mappings.items():
            if app_input in aliases:
                return app_name
        
        return app_input

class FallbackActionExecutor:
    """Simple action executor."""
    
    def __init__(self):
        self.action_handlers = {
            'open_application': self._open_application,
            'close_application': self._close_application,
            'search_web': self._search_web,
            'create_document': self._create_document,
            'system_command': self._system_command,
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
    
    def _general_query(self, entities: Dict[str, Any]) -> str:
        """Handle general queries."""
        query = entities.get('query', '')
        logger.info(f"Processing general query: {query}")
        return f"I understand you're asking about: {query}. Let me help you with that."

class FallbackTextSummarizer:
    """Simple text summarizer using extractive methods."""
    
    def summarize(self, text: str, method: str = "extractive", max_length: int = 150) -> str:
        """Summarize text using simple extractive method."""
        if not text or len(text.strip()) < 50:
            return text
        
        sentences = self._split_sentences(text)
        
        if len(sentences) <= 3:
            return text
        
        # Simple scoring based on sentence position and length
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Position score (first and last sentences are important)
            if i == 0 or i == len(sentences) - 1:
                score += 2
            elif i < len(sentences) * 0.3:  # Early sentences
                score += 1
            
            # Length score (medium length sentences preferred)
            words = len(sentence.split())
            if 10 <= words <= 30:
                score += 1
            
            # Keyword score (simple frequency-based)
            common_words = self._get_common_words(text)
            for word in common_words[:5]:
                if word.lower() in sentence.lower():
                    score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and select top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        # Select sentences until max_length is reached
        summary_sentences = []
        current_length = 0
        
        for score, sentence in scored_sentences:
            if current_length + len(sentence) <= max_length * 5:  # Rough estimate
                summary_sentences.append(sentence)
                current_length += len(sentence)
            
            if len(summary_sentences) >= 3:
                break
        
        # Sort selected sentences by original order
        original_order = []
        for sentence in summary_sentences:
            original_order.append((sentences.index(sentence), sentence))
        
        original_order.sort(key=lambda x: x[0])
        
        return " ".join([sentence for _, sentence in original_order])
    
    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting."""
        # Basic sentence splitting on periods, exclamation marks, and question marks
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_common_words(self, text: str) -> List[str]:
        """Get most common words in text."""
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        word_counts = Counter(filtered_words)
        return [word for word, count in word_counts.most_common(10)]

class FallbackContentAnalyzer:
    """Simple content analyzer."""
    
    def __init__(self):
        self.content_types = {
            'email': ['from:', 'to:', 'subject:', 'dear'],
            'code': ['function', 'class', 'import', 'def', 'var', 'const'],
            'article': ['article', 'blog', 'post', 'news'],
            'document': ['document', 'report', 'paper', 'manual']
        }
    
    def analyze_content(self, text: str, content_type: str = "auto") -> ProcessedContent:
        """Analyze content and extract insights."""
        start_time = time.time()
        
        if content_type == "auto":
            content_type = self._detect_content_type(text)
        
        # Simple summarization
        summarizer = FallbackTextSummarizer()
        summary = summarizer.summarize(text)
        
        # Extract keywords
        keywords = self._extract_keywords(text)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(text)
        
        # Categorize content
        category = self._categorize_content(text)
        
        processing_time = time.time() - start_time
        
        return ProcessedContent(
            original_text=text,
            summary=summary,
            content_type=content_type,
            keywords=keywords,
            sentiment=sentiment,
            category=category,
            processing_time=processing_time,
            confidence=0.7
        )
    
    def _detect_content_type(self, text: str) -> str:
        """Detect content type."""
        text_lower = text.lower()
        
        for content_type, indicators in self.content_types.items():
            if any(indicator in text_lower for indicator in indicators):
                return content_type
        
        return "general"
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome', 'love', 'like', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'sad', 'angry', 'frustrated', 'disappointed']
        
        text_lower = text.lower()
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"
    
    def _categorize_content(self, text: str) -> str:
        """Categorize content."""
        categories = {
            'business': ['business', 'company', 'corporate', 'enterprise'],
            'technology': ['technology', 'software', 'computer', 'digital'],
            'education': ['education', 'learning', 'school', 'university'],
            'health': ['health', 'medical', 'doctor', 'hospital']
        }
        
        text_lower = text.lower()
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"

# Fallback automation system
class FallbackAutomationSystem:
    """Fallback automation system using simple pattern matching."""
    
    def __init__(self):
        self.intent_classifier = FallbackIntentClassifier()
        self.action_executor = FallbackActionExecutor()
        self.action_history = deque(maxlen=100)
        self.is_learning = True
    
    def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a natural language command."""
        intent, entities = self.intent_classifier.classify_intent(command)
        result = self.action_executor.execute_action(intent, entities)
        
        if self.is_learning and result['success']:
            action = UserAction(
                timestamp=datetime.now(),
                action_type=intent,
                application=entities.get('application'),
                parameters=entities,
                context=context
            )
            self.action_history.append(action)
        
        return result
    
    def get_automation_suggestions(self) -> List[Dict[str, Any]]:
        """Get automation suggestions."""
        # Simple frequency-based suggestions
        if len(self.action_history) < 5:
            return []
        
        action_counts = Counter()
        for action in self.action_history:
            key = f"{action.action_type}:{action.application or 'none'}"
            action_counts[key] += 1
        
        suggestions = []
        for key, count in action_counts.most_common(3):
            if count >= 3:
                action_type, app = key.split(':', 1)
                suggestions.append({
                    'name': f"Frequent {action_type} for {app}",
                    'frequency': count,
                    'confidence': min(count / len(self.action_history), 1.0),
                    'key': key
                })
        
        return suggestions
    
    def create_automation(self, sequence_key: str, name: str) -> bool:
        """Create automation (placeholder)."""
        logger.info(f"Created automation: {name} for {sequence_key}")
        return True
    
    def toggle_learning(self, enabled: bool):
        """Toggle learning."""
        self.is_learning = enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats."""
        return {
            'total_actions_logged': len(self.action_history),
            'patterns_identified': len(self.get_automation_suggestions()),
            'learning_enabled': self.is_learning,
            'suggestions_available': len(self.get_automation_suggestions())
        }

# Fallback content processor
class FallbackContentProcessor:
    """Fallback content processor."""
    
    def __init__(self):
        self.summarizer = FallbackTextSummarizer()
        self.content_analyzer = FallbackContentAnalyzer()
    
    def summarize_text(self, text: str, method: str = "extractive") -> str:
        """Summarize text."""
        return self.summarizer.summarize(text, method=method)
    
    def analyze_content(self, text: str, content_type: str = "auto") -> ProcessedContent:
        """Analyze content."""
        return self.content_analyzer.analyze_content(text, content_type)
    
    def process_email(self, email_content: str, sender: str = "", subject: str = "") -> Dict[str, Any]:
        """Process email (simplified)."""
        analysis = self.analyze_content(email_content, "email")
        
        return {
            'sender': sender,
            'subject': subject,
            'summary': analysis.summary,
            'priority': 'normal',
            'category': analysis.category,
            'action_required': 'please' in email_content.lower() or 'action' in email_content.lower()
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing stats."""
        return {
            'total_content_processed': 0,
            'average_processing_time': 0,
            'total_emails_processed': 0,
            'emails_requiring_action': 0,
            'urgent_emails': 0
        }

# Fallback innovative features
class FallbackInnovativeFeatures:
    """Fallback innovative features."""
    
    def __init__(self):
        self.current_context = {
            'active_applications': [],
            'time_of_day': self._get_time_of_day(),
            'productivity_level': 0.5
        }
        self.features_enabled = {
            'proactive_suggestions': True,
            'smart_notifications': True,
            'adaptive_ui': True,
            'voice_commands': True,
            'context_learning': True
        }
    
    def _get_time_of_day(self) -> str:
        """Get time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def update_user_context(self, **kwargs):
        """Update user context."""
        self.current_context.update(kwargs)
    
    def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """Get proactive suggestions."""
        suggestions = []
        
        if self.current_context.get('time_of_day') == 'morning':
            suggestions.append({
                'action_type': 'daily_planning',
                'description': 'Start your day by reviewing your calendar',
                'confidence': 0.8,
                'priority': 'normal'
            })
        
        return suggestions
    
    def get_smart_notifications(self) -> List[Dict[str, Any]]:
        """Get smart notifications."""
        return []  # No notifications for fallback
    
    def get_ui_adaptations(self) -> Dict[str, Any]:
        """Get UI adaptations."""
        time_of_day = self.current_context.get('time_of_day', 'day')
        
        return {
            'theme': {'mode': 'dark' if time_of_day in ['evening', 'night'] else 'light'},
            'layout': {'sidebar': 'expanded'},
            'widgets': {'clock': True, 'weather': True}
        }
    
    def process_voice_command(self, audio_text: str) -> Dict[str, Any]:
        """Process voice command."""
        if 'helios' in audio_text.lower():
            return {
                'status': 'understood',
                'action': 'general_query',
                'confidence': 0.6
            }
        return {'status': 'no_wake_word'}
    
    def create_notification(self, title: str, message: str, **kwargs) -> bool:
        """Create notification."""
        logger.info(f"Notification: {title} - {message}")
        return True
    
    def get_productivity_insights(self) -> Dict[str, Any]:
        """Get productivity insights."""
        return {
            'status': 'analyzed',
            'most_productive_time': 'morning',
            'recommendations': ['Focus on important tasks in the morning']
        }
    
    def toggle_feature(self, feature_name: str, enabled: bool):
        """Toggle feature."""
        if feature_name in self.features_enabled:
            self.features_enabled[feature_name] = enabled
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get feature status."""
        return self.features_enabled.copy()
    
    def get_system_insights(self) -> Dict[str, Any]:
        """Get system insights."""
        return {
            'current_context': self.current_context,
            'active_features': self.features_enabled,
            'suggestions_count': len(self.get_proactive_suggestions()),
            'notifications_count': 0
        }

# Global fallback instances
fallback_automation_system = FallbackAutomationSystem()
fallback_content_processor = FallbackContentProcessor()
fallback_innovative_features = FallbackInnovativeFeatures()

def get_automation_system():
    """Get automation system (fallback version)."""
    return fallback_automation_system

def get_content_processor():
    """Get content processor (fallback version)."""
    return fallback_content_processor

def get_innovative_features():
    """Get innovative features (fallback version)."""
    return fallback_innovative_features

