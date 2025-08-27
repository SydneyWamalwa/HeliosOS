"""
AI Content Processing Module for HeliosOS

This module provides intelligent content processing capabilities including:
- Advanced text summarization (extractive and abstractive)
- Email processing and classification
- Document analysis and insights
- Content categorization and tagging
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.parser import Parser
import sqlite3
import threading
from pathlib import Path

from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM, pipeline, BartTokenizer, BartForConditionalGeneration
)
import torch
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    logger.warning("Failed to download NLTK data")

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

@dataclass
class EmailData:
    """Represents email data with metadata."""
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: datetime
    priority: str = "normal"
    category: str = "general"
    summary: str = ""
    action_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class TextSummarizer:
    """Advanced text summarization using multiple techniques."""
    
    def __init__(self):
        self.models_loaded = False
        self.bart_model = None
        self.bart_tokenizer = None
        self._load_models()
    
    def _load_models(self):
        """Load summarization models."""
        try:
            # Load BART model for abstractive summarization
            model_name = "facebook/bart-large-cnn"
            self.bart_tokenizer = BartTokenizer.from_pretrained(model_name)
            self.bart_model = BartForConditionalGeneration.from_pretrained(model_name)
            self.models_loaded = True
            logger.info("Summarization models loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load summarization models: {str(e)}")
            self.models_loaded = False
    
    def summarize(self, text: str, method: str = "hybrid", max_length: int = 150) -> str:
        """
        Summarize text using specified method.
        
        Args:
            text: Input text to summarize
            method: Summarization method ('extractive', 'abstractive', 'hybrid')
            max_length: Maximum length of summary
        
        Returns:
            Summarized text
        """
        if not text or len(text.strip()) < 50:
            return text
        
        start_time = time.time()
        
        try:
            if method == "extractive":
                summary = self._extractive_summarization(text, max_length)
            elif method == "abstractive":
                summary = self._abstractive_summarization(text, max_length)
            else:  # hybrid
                summary = self._hybrid_summarization(text, max_length)
            
            processing_time = time.time() - start_time
            logger.info(f"Summarization completed in {processing_time:.2f}s using {method} method")
            
            return summary
        
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return self._fallback_summary(text, max_length)
    
    def _extractive_summarization(self, text: str, max_length: int) -> str:
        """Extractive summarization using sentence ranking."""
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 3:
            return text
        
        # Create sentence embeddings using word overlap
        sentence_vectors = []
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            words = [word for word in words if word.isalnum()]
            sentence_vectors.append(words)
        
        # Calculate similarity matrix
        similarity_matrix = np.zeros((len(sentences), len(sentences)))
        
        for i in range(len(sentences)):
            for j in range(len(sentences)):
                if i != j:
                    similarity_matrix[i][j] = self._sentence_similarity(
                        sentence_vectors[i], sentence_vectors[j]
                    )
        
        # Use PageRank to rank sentences
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph)
        
        # Select top sentences
        ranked_sentences = sorted(
            ((scores[i], s) for i, s in enumerate(sentences)),
            reverse=True
        )
        
        # Select sentences until max_length is reached
        summary_sentences = []
        current_length = 0
        
        for score, sentence in ranked_sentences:
            if current_length + len(sentence) <= max_length * 5:  # Rough word estimate
                summary_sentences.append(sentence)
                current_length += len(sentence)
            
            if len(summary_sentences) >= 3:  # Limit to 3 sentences
                break
        
        return " ".join(summary_sentences)
    
    def _abstractive_summarization(self, text: str, max_length: int) -> str:
        """Abstractive summarization using BART model."""
        if not self.models_loaded:
            return self._fallback_summary(text, max_length)
        
        try:
            # Tokenize input
            inputs = self.bart_tokenizer.encode(
                text, 
                return_tensors="pt", 
                max_length=1024, 
                truncation=True
            )
            
            # Generate summary
            with torch.no_grad():
                summary_ids = self.bart_model.generate(
                    inputs,
                    max_length=max_length,
                    min_length=30,
                    length_penalty=2.0,
                    num_beams=4,
                    early_stopping=True
                )
            
            summary = self.bart_tokenizer.decode(
                summary_ids[0], 
                skip_special_tokens=True
            )
            
            return summary
        
        except Exception as e:
            logger.error(f"Abstractive summarization failed: {str(e)}")
            return self._extractive_summarization(text, max_length)
    
    def _hybrid_summarization(self, text: str, max_length: int) -> str:
        """Hybrid summarization combining extractive and abstractive methods."""
        # First, use extractive to get key sentences
        extractive_summary = self._extractive_summarization(text, max_length * 2)
        
        # Then, use abstractive to refine the summary
        if len(extractive_summary) > max_length:
            return self._abstractive_summarization(extractive_summary, max_length)
        
        return extractive_summary
    
    def _sentence_similarity(self, sent1: List[str], sent2: List[str]) -> float:
        """Calculate similarity between two sentences."""
        if not sent1 or not sent2:
            return 0.0
        
        # Get stopwords
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = set()
        
        # Remove stopwords
        sent1 = [word for word in sent1 if word not in stop_words]
        sent2 = [word for word in sent2 if word not in stop_words]
        
        # Create vocabulary
        all_words = list(set(sent1 + sent2))
        
        # Create vectors
        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)
        
        for word in sent1:
            if word in all_words:
                vector1[all_words.index(word)] += 1
        
        for word in sent2:
            if word in all_words:
                vector2[all_words.index(word)] += 1
        
        # Calculate cosine similarity
        return 1 - cosine_distance(vector1, vector2)
    
    def _fallback_summary(self, text: str, max_length: int) -> str:
        """Fallback summary method."""
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 2:
            return text
        
        # Take first and last sentences, plus middle one if exists
        summary_sentences = [sentences[0]]
        
        if len(sentences) > 2:
            middle_idx = len(sentences) // 2
            summary_sentences.append(sentences[middle_idx])
        
        if len(sentences) > 1:
            summary_sentences.append(sentences[-1])
        
        summary = " ".join(summary_sentences)
        
        # Truncate if too long
        if len(summary) > max_length * 5:
            summary = summary[:max_length * 5] + "..."
        
        return summary

class EmailProcessor:
    """Advanced email processing and classification."""
    
    def __init__(self):
        self.summarizer = TextSummarizer()
        self.email_patterns = {
            'meeting': [
                r'meeting', r'conference', r'call', r'zoom', r'teams',
                r'appointment', r'schedule', r'calendar'
            ],
            'urgent': [
                r'urgent', r'asap', r'immediately', r'emergency',
                r'critical', r'important', r'deadline'
            ],
            'action_required': [
                r'please', r'action required', r'need', r'request',
                r'confirm', r'approve', r'review', r'sign'
            ],
            'newsletter': [
                r'newsletter', r'unsubscribe', r'weekly', r'monthly',
                r'digest', r'update', r'news'
            ],
            'promotional': [
                r'sale', r'discount', r'offer', r'deal', r'promotion',
                r'limited time', r'special', r'save'
            ]
        }
    
    def process_email(self, email_content: str, sender: str = "", 
                     subject: str = "") -> EmailData:
        """
        Process email content and extract insights.
        
        Args:
            email_content: Email body text
            sender: Email sender
            subject: Email subject
        
        Returns:
            EmailData object with processed information
        """
        # Parse email if it's in raw format
        if email_content.startswith("From:") or email_content.startswith("Subject:"):
            parsed_email = self._parse_raw_email(email_content)
            sender = parsed_email.get('sender', sender)
            subject = parsed_email.get('subject', subject)
            email_content = parsed_email.get('body', email_content)
        
        # Generate summary
        summary = self.summarizer.summarize(email_content, method="hybrid", max_length=100)
        
        # Classify email
        category = self._classify_email(email_content, subject)
        priority = self._determine_priority(email_content, subject)
        action_required = self._check_action_required(email_content, subject)
        
        return EmailData(
            sender=sender,
            recipient="",  # Would be filled by the calling system
            subject=subject,
            body=email_content,
            timestamp=datetime.now(),
            priority=priority,
            category=category,
            summary=summary,
            action_required=action_required
        )
    
    def _parse_raw_email(self, raw_email: str) -> Dict[str, str]:
        """Parse raw email format."""
        parser = Parser()
        
        try:
            msg = parser.parsestr(raw_email)
            
            return {
                'sender': msg.get('From', ''),
                'subject': msg.get('Subject', ''),
                'body': self._extract_email_body(msg)
            }
        except Exception as e:
            logger.error(f"Failed to parse raw email: {str(e)}")
            return {'sender': '', 'subject': '', 'body': raw_email}
    
    def _extract_email_body(self, msg) -> str:
        """Extract email body from parsed message."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return ""
    
    def _classify_email(self, content: str, subject: str) -> str:
        """Classify email into categories."""
        text = (content + " " + subject).lower()
        
        category_scores = {}
        
        for category, patterns in self.email_patterns.items():
            score = 0
            for pattern in patterns:
                score += len(re.findall(pattern, text, re.IGNORECASE))
            category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return "general"
    
    def _determine_priority(self, content: str, subject: str) -> str:
        """Determine email priority."""
        text = (content + " " + subject).lower()
        
        urgent_indicators = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'deadline', 'time sensitive', 'high priority'
        ]
        
        high_priority_indicators = [
            'important', 'please review', 'action required',
            'needs approval', 'meeting request'
        ]
        
        urgent_score = sum(1 for indicator in urgent_indicators if indicator in text)
        high_score = sum(1 for indicator in high_priority_indicators if indicator in text)
        
        if urgent_score > 0:
            return "urgent"
        elif high_score > 0:
            return "high"
        else:
            return "normal"
    
    def _check_action_required(self, content: str, subject: str) -> bool:
        """Check if email requires action from user."""
        text = (content + " " + subject).lower()
        
        action_indicators = [
            'please', 'action required', 'need', 'request',
            'confirm', 'approve', 'review', 'sign', 'respond',
            'reply', 'feedback', 'decision', 'choose'
        ]
        
        return any(indicator in text for indicator in action_indicators)
    
    def batch_process_emails(self, emails: List[Dict[str, str]]) -> List[EmailData]:
        """Process multiple emails in batch."""
        processed_emails = []
        
        for email in emails:
            try:
                processed = self.process_email(
                    email.get('content', ''),
                    email.get('sender', ''),
                    email.get('subject', '')
                )
                processed_emails.append(processed)
            except Exception as e:
                logger.error(f"Failed to process email: {str(e)}")
        
        return processed_emails

class ContentAnalyzer:
    """Advanced content analysis and insights."""
    
    def __init__(self):
        self.summarizer = TextSummarizer()
        self.content_types = {
            'article': ['article', 'blog', 'post', 'news'],
            'document': ['document', 'report', 'paper', 'manual'],
            'email': ['from:', 'to:', 'subject:', 'dear'],
            'code': ['function', 'class', 'import', 'def', 'var'],
            'legal': ['agreement', 'contract', 'terms', 'conditions'],
            'academic': ['abstract', 'introduction', 'methodology', 'conclusion']
        }
    
    def analyze_content(self, text: str, content_type: str = "auto") -> ProcessedContent:
        """
        Analyze content and extract insights.
        
        Args:
            text: Input text to analyze
            content_type: Type of content or "auto" for automatic detection
        
        Returns:
            ProcessedContent object with analysis results
        """
        start_time = time.time()
        
        # Auto-detect content type if needed
        if content_type == "auto":
            content_type = self._detect_content_type(text)
        
        # Generate summary
        summary = self.summarizer.summarize(text, method="hybrid")
        
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
            confidence=0.8  # Placeholder confidence score
        )
    
    def _detect_content_type(self, text: str) -> str:
        """Automatically detect content type."""
        text_lower = text.lower()
        
        type_scores = {}
        for content_type, indicators in self.content_types.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            type_scores[content_type] = score
        
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] > 0:
                return best_type
        
        return "general"
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        try:
            words = word_tokenize(text.lower())
            
            # Remove stopwords and non-alphabetic words
            try:
                stop_words = set(stopwords.words('english'))
            except:
                stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'])
            
            words = [word for word in words if word.isalpha() and word not in stop_words]
            
            # Count word frequency
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and return top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            return [word for word, freq in sorted_words[:max_keywords]]
        
        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text."""
        # Simple sentiment analysis based on word patterns
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful',
            'fantastic', 'awesome', 'love', 'like', 'happy'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'hate',
            'dislike', 'sad', 'angry', 'frustrated', 'disappointed'
        ]
        
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
        """Categorize content into general categories."""
        categories = {
            'business': ['business', 'company', 'corporate', 'enterprise', 'commercial'],
            'technology': ['technology', 'software', 'computer', 'digital', 'tech'],
            'education': ['education', 'learning', 'school', 'university', 'academic'],
            'health': ['health', 'medical', 'doctor', 'hospital', 'medicine'],
            'finance': ['finance', 'money', 'bank', 'investment', 'financial'],
            'entertainment': ['entertainment', 'movie', 'music', 'game', 'fun']
        }
        
        text_lower = text.lower()
        
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return "general"

class AIContentProcessor:
    """Main class for AI-powered content processing."""
    
    def __init__(self, db_path: str = "content_processing.db"):
        self.summarizer = TextSummarizer()
        self.email_processor = EmailProcessor()
        self.content_analyzer = ContentAnalyzer()
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the content processing database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS processed_content (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_hash TEXT UNIQUE,
                        original_text TEXT,
                        summary TEXT,
                        content_type TEXT,
                        keywords TEXT,
                        sentiment TEXT,
                        category TEXT,
                        processing_time REAL,
                        created_at TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS processed_emails (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT,
                        subject TEXT,
                        summary TEXT,
                        priority TEXT,
                        category TEXT,
                        action_required BOOLEAN,
                        created_at TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize content processing database: {str(e)}")
    
    def summarize_text(self, text: str, method: str = "hybrid") -> str:
        """Summarize text using specified method."""
        return self.summarizer.summarize(text, method=method)
    
    def process_email(self, email_content: str, sender: str = "", 
                     subject: str = "") -> EmailData:
        """Process email and return structured data."""
        processed = self.email_processor.process_email(email_content, sender, subject)
        
        # Store in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO processed_emails 
                    (sender, subject, summary, priority, category, action_required, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    processed.sender,
                    processed.subject,
                    processed.summary,
                    processed.priority,
                    processed.category,
                    processed.action_required,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store processed email: {str(e)}")
        
        return processed
    
    def analyze_content(self, text: str, content_type: str = "auto") -> ProcessedContent:
        """Analyze content and return insights."""
        processed = self.content_analyzer.analyze_content(text, content_type)
        
        # Store in database
        try:
            content_hash = str(hash(text))
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO processed_content 
                    (content_hash, original_text, summary, content_type, keywords, 
                     sentiment, category, processing_time, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    content_hash,
                    text[:1000],  # Limit stored text size
                    processed.summary,
                    processed.content_type,
                    json.dumps(processed.keywords),
                    processed.sentiment,
                    processed.category,
                    processed.processing_time,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store processed content: {str(e)}")
        
        return processed
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get content processing statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Content stats
                content_cursor = conn.execute('''
                    SELECT COUNT(*), AVG(processing_time) 
                    FROM processed_content
                ''')
                content_count, avg_processing_time = content_cursor.fetchone()
                
                # Email stats
                email_cursor = conn.execute('''
                    SELECT COUNT(*), 
                           SUM(CASE WHEN action_required = 1 THEN 1 ELSE 0 END),
                           SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END)
                    FROM processed_emails
                ''')
                email_count, action_required_count, urgent_count = email_cursor.fetchone()
                
                return {
                    'total_content_processed': content_count or 0,
                    'average_processing_time': avg_processing_time or 0,
                    'total_emails_processed': email_count or 0,
                    'emails_requiring_action': action_required_count or 0,
                    'urgent_emails': urgent_count or 0
                }
        except Exception as e:
            logger.error(f"Failed to get processing stats: {str(e)}")
            return {}

# Global instance
content_processor = AIContentProcessor()

def get_content_processor() -> AIContentProcessor:
    """Get the global content processor instance."""
    return content_processor

