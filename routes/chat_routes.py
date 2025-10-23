from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from models.chat_models import ChatRequest, ChatResponse
from auth import get_current_user
from service.chatbot_service import generate_chat_reply
import json

router = APIRouter(prefix="/chat", tags=["Chat"])

def format_context_safely(context: dict) -> str:
    """
    Format context in a structured way that encourages proper AI formatting
    """
    if not context:
        return ""
    
    context_parts = []
    
    # User info
    if "user_info" in context:
        user_info = context["user_info"]
        context_parts.append(f"USER PROFILE:")
        context_parts.append(f"- Name: {user_info.get('name', 'Unknown')}")
    
    # Resume/Skills
    if "resume" in context:
        resume = context["resume"]
        context_parts.append(f"\nUSER SKILLS & EXPERIENCE:")
        
        if resume.get("skills"):
            skills = resume["skills"]
            if isinstance(skills, list):
                context_parts.append(f"- Skills: {', '.join(skills[:15])}")
            elif isinstance(skills, str):
                context_parts.append(f"- Skills: {skills[:200]}")
        
        if resume.get("current_position"):
            context_parts.append(f"- Current Role: {resume['current_position']}")
        
        if resume.get("total_experience"):
            context_parts.append(f"- Total Experience: {resume['total_experience']}")
    
    # Jobs - Clean format for AI to parse
    if "available_jobs" in context:
        jobs = context["available_jobs"]
        total_count = context.get("total_jobs_count", len(jobs) if isinstance(jobs, list) else 0)
        
        if isinstance(jobs, list) and len(jobs) > 0:
            context_parts.append(f"\nAVAILABLE JOB OPENINGS ({total_count} positions):")
            context_parts.append("\nWhen listing these jobs to the user, format each one clearly with headers and bullet points.\n")
            
            for idx, job in enumerate(jobs, 1):
                if isinstance(job, dict):
                    # Provide structured data for AI to format
                    context_parts.append(f"\nJob #{idx}:")
                    context_parts.append(f"  Title: {job.get('title', 'Unknown Position')}")
                    context_parts.append(f"  Company: {job.get('company', 'Not specified')}")
                    context_parts.append(f"  Location: {job.get('location', 'Not specified')}")
                    context_parts.append(f"  Skills: {job.get('skills', 'Not specified')}")
                    context_parts.append(f"  Experience: {job.get('experience', 'Not specified')}")
                    if job.get('salary') and str(job.get('salary')) != 'Not disclosed':
                        context_parts.append(f"  Salary: {job.get('salary')}")
                    if job.get('education'):
                        context_parts.append(f"  Education: {job.get('education')}")
                    if job.get('job_type'):
                        context_parts.append(f"  Type: {job.get('job_type')}")
        else:
            context_parts.append(f"\nNO JOBS CURRENTLY AVAILABLE")
    
    return "\n".join(context_parts)

@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, user: tuple = Depends(get_current_user)):
    """
    Context-aware chatbot for Resume-Job Matcher
    """
    try:
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "role": user[4]
        }
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid auth token"
        )

    # Build prompt with formatted context
    prompt = request.message
    
    # Check if user is asking for job listings
    list_keywords = ['list', 'show', 'display', 'all jobs', 'available jobs', 'job openings', 'what jobs']
    is_job_listing_query = any(keyword in prompt.lower() for keyword in list_keywords)
    
    if request.context:
        context_str = format_context_safely(request.context)
        if context_str:
            # Add formatting reminder for job listing queries
            if is_job_listing_query:
                prompt = f"""{prompt}

IMPORTANT: Format your response using proper markdown:
- Use ### for each job heading
- Use **bold** for job titles
- Use bullet points (-) for details
- Add blank lines between jobs

{context_str}"""
            else:
                prompt = f"{prompt}\n\n{context_str}"
    
    try:
        print(f"Sending to Gemini - User: {user_dict['username']}")
        print(f"Is job listing query: {is_job_listing_query}")
        
        reply, usage = generate_chat_reply(
            prompt=prompt,
            system_prompt=request.system_prompt,
            temperature=0.3 if is_job_listing_query else 0.7  # Lower temperature for more consistent formatting
        )
        
        if not reply:
            raise ValueError("AI returned empty response")
        
        print(f"Reply received, length: {len(reply)}")
        
        return ChatResponse(
            reply=reply,
            model="gemini-1.5-flash",
            usage=usage,
            context=request.context
        )
        
    except RuntimeError as e:
        error_msg = str(e)
        print(f"Runtime error: {error_msg}")
        
        if "safety" in error_msg.lower() or "finish_reason" in error_msg.lower():
            return ChatResponse(
                reply="I apologize, but I couldn't process that request. Could you please rephrase your question?",
                model="gemini-1.5-flash",
                usage=None,
                context=request.context
            )
        
        raise HTTPException(status_code=500, detail=f"Chat service error: {error_msg}")
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

