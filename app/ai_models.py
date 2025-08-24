# app/ai_models.py
import os
import requests
from typing import List, Dict, Any, Optional

HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", None)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
HF_BASE = "https://api-inference.huggingface.co/models/"

class AIModelManager:
    """Manages AI model interactions with different providers"""
    
    @staticmethod
    def get_summary(text: str) -> Dict[str, Any]:
        """Generate a summary of the provided text"""
        if not text.strip():
            return {"summary": ""}
            
        # Try OpenAI first if configured
        if OPENAI_API_KEY:
            try:
                return AIModelManager._get_openai_summary(text)
            except Exception as e:
                print(f"OpenAI summary failed: {str(e)}")
                # Fall back to HuggingFace
        
        # Try HuggingFace if configured
        if HUGGINGFACE_API_KEY:
            try:
                return AIModelManager._get_huggingface_summary(text)
            except Exception as e:
                print(f"HuggingFace summary failed: {str(e)}")
                # Fall back to mock
        
        # Mock fallback
        short = text if len(text) <= 200 else text[:197] + "..."
        return {"summary": f"[MOCK SUMMARY] {short}"}
    
    @staticmethod
    def get_chat_response(messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate a chat response based on conversation history"""
        if not messages:
            return {"reply": "How can I help you today?"}
            
        last_msg = messages[-1]["content"] if messages and "content" in messages[-1] else ""
        
        # Try OpenAI first if configured
        if OPENAI_API_KEY:
            try:
                return AIModelManager._get_openai_chat_response(messages)
            except Exception as e:
                print(f"OpenAI chat failed: {str(e)}")
                # Fall back to HuggingFace
        
        # Try HuggingFace if configured
        if HUGGINGFACE_API_KEY:
            try:
                return AIModelManager._get_huggingface_chat_response(last_msg)
            except Exception as e:
                print(f"HuggingFace chat failed: {str(e)}")
                # Fall back to rule-based
        
        # Rule-based fallback responses
        return AIModelManager._get_rule_based_response(last_msg)
    
    @staticmethod
    def _get_openai_summary(text: str) -> Dict[str, Any]:
        """Get summary using OpenAI API"""
        import openai
        openai.api_key = OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text concisely."},
                {"role": "user", "content": f"Please summarize the following text in a concise way:\n\n{text}"}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        return {"summary": response.choices[0].message.content.strip()}
    
    @staticmethod
    def _get_huggingface_summary(text: str) -> Dict[str, Any]:
        """Get summary using HuggingFace API"""
        model = "facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {"inputs": text}
        
        resp = requests.post(HF_BASE + model, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        out = resp.json()
        
        if isinstance(out, list) and len(out) > 0 and "summary_text" in out[0]:
            return {"summary": out[0]["summary_text"]}
        return {"summary": str(out)}
    
    @staticmethod
    def _get_openai_chat_response(messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get chat response using OpenAI API"""
        import openai
        openai.api_key = OPENAI_API_KEY
        
        # Add system message if not present
        if not messages or messages[0].get("role") != "system":
            system_msg = {
                "role": "system", 
                "content": "You are Leo, an extremely helpful, friendly, and concise AI assistant embedded in the Aurora OS. "
                           "You help users operate the streamed desktop, summarize text, run small diagnostics, and explain results clearly. "
                           "Be polite, include short actionable steps when relevant, and ask clarifying questions only if essential."
            }
            messages = [system_msg] + messages
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        return {"reply": response.choices[0].message.content.strip()}
    
    @staticmethod
    def _get_huggingface_chat_response(last_msg: str) -> Dict[str, Any]:
        """Get chat response using HuggingFace API"""
        persona_preamble = (
            "You are Leo, an extremely helpful, friendly, and concise AI assistant embedded in the Aurora OS. "
            "You help users operate the streamed desktop, summarize text, run small diagnostics, and explain results clearly. "
            "Be polite, include short actionable steps when relevant, and ask clarifying questions only if essential."
        )
        prompt = persona_preamble + "\n\nUser: " + last_msg + "\nLeo:"
        
        # Use a more capable model if available
        model = "google/flan-t5-xl"  # Alternative: "gpt2"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {"inputs": prompt, "options": {"wait_for_model": True}}
        
        resp = requests.post(HF_BASE + model, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        out = resp.json()
        
        if isinstance(out, dict) and "generated_text" in out:
            reply = out["generated_text"]
        elif isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict) and "generated_text" in out[0]:
            reply = out[0]["generated_text"]
        else:
            reply = str(out)
            
        # Trim echo of the prompt if present
        if reply.startswith(prompt):
            reply = reply[len(prompt):].strip()
            
        return {"reply": reply}
    
    @staticmethod
    def _get_rule_based_response(last_msg: str) -> Dict[str, Any]:
        """Fallback rule-based responses when no AI services are available"""
        txt = last_msg.lower().strip()
        
        if txt.startswith("summarize") or txt.startswith("summarise"):
            body = last_msg.split(":", 1)[-1].strip() if ":" in last_msg else last_msg
            if len(body) > 200:
                body = body[:197] + "..."
            return {"reply": f"[MOCK SUMMARY] {body}"}
            
        if "open terminal" in txt or "open the terminal" in txt:
            return {"reply": "To interact with the OS, click 'Open Terminal' in the Applications menu or use the command panel on the right."}
            
        if "help" in txt or txt.startswith("how do i"):
            return {"reply": "I am Leo, your AI assistant. I can help you navigate the Aurora OS, run applications, summarize text, and answer questions. Try asking me how to perform specific tasks or use the command panel to run system commands."}
            
        if "screenshot" in txt or "describe" in txt:
            return {"reply": "I can't directly access the screen contents. If you need help with something visual, please describe what you're seeing or trying to accomplish."}
            
        # Default friendly reply
        safe = last_msg if len(last_msg) < 400 else last_msg[:400] + "..."
        return {"reply": f"I received: \"{safe}\" — how would you like me to help? I can assist with using applications, finding files, or explaining how to accomplish tasks in Aurora OS."}