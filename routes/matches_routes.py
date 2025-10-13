from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from service.matches_service import get_matches_for_recruiter, get_detailed_match_explanation
from models.matches_models import RecruiterMatchSummary, MatchExplanation, MatchExplanationRequest
from auth import get_current_user

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("/getMatches", response_model=List[RecruiterMatchSummary])
async def recruiter_matches(
    user: tuple = Depends(get_current_user)
):
    """
    Get all matches for a recruiter (status 'applied').
    """
    try:
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        recruiter_email = user_dict.get("email")
        role = user_dict.get("role")

        if role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can access matches"
            )

        matches = get_matches_for_recruiter(recruiter_email)
        return matches

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to fetch recruiter matches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recruiter matches"
        )

@router.post("/getDetailedMatches", response_model=Optional[MatchExplanation])
async def match_explanation(
    request: MatchExplanationRequest,
    user: tuple = Depends(get_current_user)
):
    """
    Get detailed explanation for a match.
    """
    try:
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        role = user_dict.get("role")

        if role != "recruiter":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recruiters can access match explanations"
            )

        explanation = get_detailed_match_explanation(
            request.resume_id, 
            request.job_id, 
            request.job_source
        )
        
        if not explanation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match explanation not found"
            )
        return explanation

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to fetch match explanation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match explanation"
        )