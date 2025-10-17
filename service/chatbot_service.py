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
                        model: str = "gemini-2.5-flash", max_tokens: int = 512,
                        temperature: float = 0.2) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Send prompt to Google Gemini and return (reply, usage_dict).
    """
    try:
        # Initialize model with the correct name
        model_instance = genai.GenerativeModel(model)
        
        # Combine system prompt and user message
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Generate response
        response = model_instance.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
        )
        
        content = response.text.strip() if response.text else None
        
        # Create usage info
        usage = {
            "prompt_tokens": len(full_prompt.split()),
            "completion_tokens": len(content.split()) if content else 0,
            "total_tokens": len(full_prompt.split()) + (len(content.split()) if content else 0)
        }
        
        return content, usage
        
    except Exception as e:
        raise RuntimeError(f"Gemini request failed: {str(e)}")