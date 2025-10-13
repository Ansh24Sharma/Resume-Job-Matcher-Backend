from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from service.candidates_service import (
    get_candidates_by_recruiter,
    get_candidate_by_id,
    update_candidate_status,
    get_candidate_statistics
)
from models.candidates_models import (
    CandidateResponse,
    CandidateDetailResponse,
    CandidateStatusUpdate,
    InterviewScheduleRequest,
    CandidateStatisticsResponse,
    CandidateListResponse,
)
from auth import get_current_user
from email_invitation import send_interview_invitation_email

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("/my-candidates", response_model=CandidateListResponse)
async def get_my_candidates(
    user: tuple = Depends(get_current_user)
):
    """Get all candidates for the current recruiter without filters"""

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
                detail="Only recruiters can access candidate management"
            )

        # Fetch all candidates for recruiter without any filters
        candidates = get_candidates_by_recruiter(creator_email=recruiter_email)

        return CandidateListResponse(
            candidates=candidates
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to fetch candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates"
        )


@router.get("/statistics", response_model=CandidateStatisticsResponse)
async def get_recruiter_statistics(user: tuple = Depends(get_current_user)):
    """Get candidate statistics for the recruiter dashboard"""
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
                detail="Only recruiters can access statistics"
            )
        
        statistics = get_candidate_statistics(recruiter_email)
        return CandidateStatisticsResponse(**statistics)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to fetch statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.get("/candidate_details/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate_details(
    candidate_id: int,
    user: tuple = Depends(get_current_user)
):
    """Get detailed information about a specific candidate"""
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
                detail="Only recruiters can access candidate details"
            )
        
        candidate = get_candidate_by_id(candidate_id)
        
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        return CandidateDetailResponse(**candidate)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to fetch candidate details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidate details"
        )

@router.patch("/updateStatus")
async def update_status(
    status_update: CandidateStatusUpdate,
    user: tuple = Depends(get_current_user)
):
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
            detail="Only recruiters can update candidate status"
        )

    candidate_id = status_update.candidate_id
    candidate_status = status_update.status

    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    success = update_candidate_status(candidate_id, candidate_status.value)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update candidate status"
        )

    return {
        "message": "Candidate status updated successfully",
        "candidate_id": candidate_id,
        "new_status": candidate_status.value
    }

@router.post("/schedule-interview")
async def schedule_interview(
    interview_request: InterviewScheduleRequest,
    user: tuple = Depends(get_current_user)
):
    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }

    recruiter_email = user_dict.get("email")
    recruiter_username = user_dict.get("username")
    role = user_dict.get("role")

    if role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recruiters can schedule interviews"
        )

    candidate_id = interview_request.candidate_id

    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )

    success = update_candidate_status(candidate_id, "interview_scheduled")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update candidate status"
        )

    email_sent = send_interview_invitation_email(
        candidate_email=candidate["email"],
        candidate_name=candidate["name"],
        recruiter_email=recruiter_email,
        recruiter_name=recruiter_username,
        company=candidate["company"],
        job_title=candidate["job_title"],
        interview_date=interview_request.interview_date.strftime("%B %d, %Y"),
        interview_time=interview_request.interview_time,
        interview_type=interview_request.interview_type,
        meeting_link=interview_request.meeting_link,
        additional_notes=interview_request.additional_notes
    )

    return {
        "message": "Interview scheduled successfully",
        "candidate_id": candidate_id,
        "email_sent": email_sent,
        "candidate_email": candidate["email"],
        "interview_date": interview_request.interview_date,
        "interview_time": interview_request.interview_time
    }
