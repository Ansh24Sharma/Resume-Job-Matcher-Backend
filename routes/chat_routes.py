from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from models.chat_models import ChatRequest, ChatResponse
from auth import get_current_user
from service.chatbot_service import generate_chat_reply
import traceback

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, user: tuple = Depends(get_current_user)):
    """
    Authenticated chatbot endpoint.
    """
    try:
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        print(f"User {user_dict['username']} sent message")
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid auth token"
        )

    # Build prompt with optional context
    prompt = request.message
    if request.context:
        ctx_parts = [f"{k}: {v}" for k, v in request.context.items()]
        prompt = f"{prompt}\n\nContext:\n" + "\n".join(ctx_parts)

    try:
        print(f"Sending to OpenAI - Message: {prompt[:100]}...")
        
        reply, usage = generate_chat_reply(
            prompt=prompt,
            system_prompt=request.system_prompt
        )
        
        print(f"OpenAI replied: {reply[:100] if reply else 'None'}...")
        
        if not reply:
            raise ValueError("OpenAI returned empty response")
        
        return ChatResponse(
            reply=reply,
            model="gemini-2.5-flash",
            usage=usage,
            context=request.context
        )
        
    except RuntimeError as e:
        error_msg = str(e)
        print(f"Runtime error: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)
        
    except Exception as e:
        error_msg = f"Chat service error: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)