import os
import google.generativeai as genai
from typing import Tuple, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("Gemini API key not configured (GEMINI_API_KEY).")

# Configure Gemini
genai.configure(api_key=GEMINI_KEY)

def generate_chat_reply(prompt: str, system_prompt: Optional[str] = None,
                        model: str = "gemini-2.5-flash", max_tokens: int = 2048,
                        temperature: float = 0.7) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Send prompt to Google Gemini and return (reply, usage_dict).
    """
    try:
        # Initialize model with safety settings
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        model_instance = genai.GenerativeModel(
            model,
            safety_settings=safety_settings
        )
        
        # Combine system prompt and user message
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Limit prompt length to avoid context overflow
        if len(full_prompt) > 8000:
            full_prompt = full_prompt[:8000] + "\n\n[Context truncated for length]"
        
        # Generate response
        response = model_instance.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
        )
        
        # Handle different response scenarios
        content = None
        
        # Check if response has text
        if hasattr(response, 'text') and response.text:
            content = response.text.strip()
        # Check if response has parts
        elif hasattr(response, 'parts') and response.parts:
            content = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
        # Check candidates
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    content = ''.join(
                        part.text for part in candidate.content.parts 
                        if hasattr(part, 'text')
                    )
                    if content:
                        break
        
        # If still no content, check finish reason
        if not content:
            finish_reason = "UNKNOWN"
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)
            
            if "SAFETY" in finish_reason or finish_reason == "2":
                content = "I apologize, but I couldn't generate a response due to safety filters. Could you please rephrase your question or ask something else?"
            else:
                raise ValueError(f"No content in response. Finish reason: {finish_reason}")
        
        # Create usage info (approximate)
        usage = {
            "prompt_tokens": len(full_prompt.split()),
            "completion_tokens": len(content.split()) if content else 0,
            "total_tokens": len(full_prompt.split()) + (len(content.split()) if content else 0)
        }
        
        return content, usage
        
    except Exception as e:
        error_msg = str(e)
        print(f"Gemini error details: {error_msg}")
        raise RuntimeError(f"Gemini request failed: {error_msg}")