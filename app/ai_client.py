import time
import logging
from typing import Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from flask import current_app, has_app_context, g

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass

class HuggingFaceClient:
    """Production-ready HuggingFace API client."""

    def __init__(self, api_key: Optional[str] = None):
        # Only access current_app if we're in an app context
        if has_app_context():
            self.api_key = api_key or current_app.config.get('HUGGINGFACE_API_KEY', '')
        else:
            self.api_key = api_key or ''

        self.base_url = "https://api-inference.huggingface.co/models/"
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, AIServiceError))
    )
    def _make_request(self, model: str, payload: dict, timeout: int = 30) -> dict:
        """Make API request with retry logic."""
        if not self.api_key:
            raise AIServiceError("HuggingFace API key not configured")

        url = f"{self.base_url}{model}"

        try:
            response = self.session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()

            result = response.json()

            # Handle model loading status
            if isinstance(result, dict) and 'error' in result:
                error_msg = result['error']
                if 'loading' in error_msg.lower():
                    logger.warning(f"Model {model} is loading, retrying...")
                    raise AIServiceError("Model is loading")
                elif 'authorization' in error_msg.lower() or 'token' in error_msg.lower():
                    raise AIServiceError(f"Authentication error: {error_msg}")
                else:
                    raise AIServiceError(f"API Error: {error_msg}")

            return result

        except requests.RequestException as e:
            logger.error(f"Request failed for model {model}: {str(e)}")
            raise AIServiceError(f"Request failed: {str(e)}")

    def summarize_text(self, text: str, model: Optional[str] = None) -> str:
        """Summarize text using HuggingFace model."""
        if not text.strip():
            return ""

        # Get model from config if available and in app context
        if has_app_context():
            model = model or current_app.config.get('SUMMARY_MODEL', 'facebook/bart-large-cnn')
        else:
            model = model or 'facebook/bart-large-cnn'

        # If no API key is configured, use fallback immediately
        if not self.api_key:
            logger.warning("HuggingFace API key not configured, using fallback summary")
            return self._fallback_summary(text)

        start_time = time.time()

        try:
            payload = {
                "inputs": text,
                "parameters": {
                    "max_length": min(150, len(text.split()) // 2),
                    "min_length": 30,
                    "do_sample": False
                }
            }

            result = self._make_request(model, payload)
            response_time = time.time() - start_time

            # Extract summary text
            summary = ""
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and 'summary_text' in result[0]:
                    summary = result[0]['summary_text']
            elif isinstance(result, dict) and 'summary_text' in result:
                summary = result['summary_text']

            # Log interaction (safely)
            self._safe_log_interaction('summarize', text, summary, model, response_time, True)

            return summary or str(result)

        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            self._safe_log_interaction('summarize', text, None, model, time.time() - start_time, False, str(e))
            return self._fallback_summary(text)

    def generate_chat_response(self, messages: list, model: Optional[str] = None) -> str:
        """Generate chat response using HuggingFace model."""
        # Get model from config if available and in app context
        if has_app_context():
            model = model or current_app.config.get('CHAT_MODEL', 'microsoft/DialoGPT-medium')
        else:
            model = model or 'microsoft/DialoGPT-medium'

        # If no API key is configured, use fallback immediately
        if not self.api_key:
            logger.warning("HuggingFace API key not configured, using fallback chat response")
            return self._fallback_chat_response(messages)

        start_time = time.time()

        # Format conversation
        conversation = self._format_conversation(messages)

        try:
            payload = {
                "inputs": conversation,
                "parameters": {
                    "max_length": 512,
                    "temperature": 0.7,
                    "do_sample": True,
                    "pad_token_id": 50256
                }
            }

            result = self._make_request(model, payload)
            response_time = time.time() - start_time

            # Extract generated text
            response = ""
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and 'generated_text' in result[0]:
                    response = result[0]['generated_text']
            elif isinstance(result, dict) and 'generated_text' in result:
                response = result['generated_text']

            # Clean up response
            if response:
                response = self._clean_chat_response(response, conversation)

            # Log interaction (safely)
            self._safe_log_interaction('chat', conversation, response, model, response_time, True)

            return response or "I'm having trouble generating a response right now."

        except Exception as e:
            logger.error(f"Chat generation failed: {str(e)}")
            self._safe_log_interaction('chat', conversation, None, model, time.time() - start_time, False, str(e))
            return self._fallback_chat_response(messages)

    def _format_conversation(self, messages: list) -> str:
        """Format conversation for the model."""
        persona = (
            "You are Leo, a helpful AI assistant for HeliosOS. "
            "You provide concise, accurate responses and help users with system tasks. "
            "Be friendly but professional.\n\n"
        )

        conversation = persona
        for msg in messages[-5:]:  # Keep last 5 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '').strip()
            if content:
                if role == 'user':
                    conversation += f"User: {content}\n"
                else:
                    conversation += f"Leo: {content}\n"

        conversation += "Leo:"
        return conversation

    def _clean_chat_response(self, response: str, prompt: str) -> str:
        """Clean up the chat response."""
        if response.startswith(prompt):
            response = response[len(prompt):].strip()

        # Remove common artifacts
        response = response.replace('<|endoftext|>', '').strip()

        # Split on newlines and take first meaningful response
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            response = lines[0]

        return response[:500]  # Limit response length

    def _fallback_summary(self, text: str) -> str:
        """Fallback summary when API fails."""
        words = text.split()
        if len(words) <= 50:
            return f"[Brief content]: {text[:200]}..."

        # Simple extractive summary
        sentences = text.split('.')[:3]
        summary = '. '.join(s.strip() for s in sentences if s.strip())
        return f"[Auto Summary]: {summary[:300]}..."

    def _fallback_chat_response(self, messages: list) -> str:
        """Fallback chat response when API fails."""
        if not messages:
            return "Hello! I'm Leo, your HeliosOS assistant. How can I help you today?"

        last_msg = messages[-1].get('content', '').lower()

        if any(word in last_msg for word in ['help', 'how', 'what']):
            return ("I'm here to help! You can ask me to summarize text, "
                   "run system commands, or get information about HeliosOS.")
        elif 'summarize' in last_msg:
            return "To summarize text, just paste it and I'll create a brief summary for you."
        elif any(word in last_msg for word in ['command', 'terminal', 'run']):
            return ("You can run safe commands like 'ls', 'pwd', 'whoami', 'df -h', "
                   "and others using the Run Command panel.")
        else:
            return "I understand. How else can I assist you with HeliosOS?"

    def _safe_log_interaction(self, interaction_type: str, input_text: str,
                            output_text: Optional[str], model: str,
                            response_time: float, success: bool,
                            error_message: Optional[str] = None):
        """Safely log AI interaction to database."""
        try:
            # Only attempt database logging if we're in a Flask app context
            if not has_app_context():
                logger.debug("No Flask app context available, skipping database logging")
                return

            # Test database connection first
            try:
                from app import db
                # Use text() for SQLAlchemy 2.0 compatibility
                from sqlalchemy import text
                db.session.execute(text("SELECT 1"))
            except Exception as db_error:
                logger.warning(f"Database not available, skipping logging: {str(db_error)}")
                return

            # Import here to avoid circular imports
            from app.models import AIInteraction

            user_id = None
            if hasattr(g, 'current_user') and g.current_user:
                user_id = g.current_user.id

            interaction = AIInteraction(
                user_id=user_id,
                interaction_type=interaction_type,
                input_text=input_text[:1000],  # Limit input size
                output_text=output_text[:2000] if output_text else None,
                model_used=model,
                response_time=response_time,
                success=success,
                error_message=error_message
            )

            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"Successfully logged {interaction_type} interaction")

        except Exception as e:
            logger.warning(f"Failed to log AI interaction: {str(e)}")
            # Don't re-raise the exception to avoid breaking the main functionality


class AIService:
    """Main AI service interface."""

    def __init__(self):
        self.hf_client = HuggingFaceClient()

    def summarize(self, text: str) -> str:
        """Summarize text using the best available model."""
        return self.hf_client.summarize_text(text)

    def chat(self, messages: list) -> str:
        """Generate chat response using the best available model."""
        return self.hf_client.generate_chat_response(messages)

    def health_check(self) -> dict:
        """Check AI service health."""
        try:
            # Use a shorter test text to avoid rate limits
            test_summary = self.hf_client.summarize_text("This is a short test for health check.")

            return {
                'status': 'healthy',
                'services': {
                    'huggingface': 'available' if self.hf_client.api_key else 'no_key'
                },
                'test_result': bool(test_summary and not test_summary.startswith('[Auto Summary]'))
            }
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return {
                'status': 'degraded',
                'error': str(e),
                'services': {
                    'huggingface': 'error'
                }
            }

# Factory function
def get_ai_service() -> AIService:
    """Get AI service instance."""
    return AIService()