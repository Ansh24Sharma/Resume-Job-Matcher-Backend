from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = "You are a helpful assistant for a dashboard."
    context: Optional[Dict[str, Any]] = None 

class ChatResponse(BaseModel):
    reply: str
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None