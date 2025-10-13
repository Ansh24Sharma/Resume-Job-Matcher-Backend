from fastapi import APIRouter, Depends
from auth import get_current_user
from service.recommendation_service import run_matcher, get_top_recommendations, get_user_active_resume_id
from service.candidates_service import create_candidate_from_match
from fastapi import HTTPException, status
from models.recommendation_models import ApplyJobRequest, SaveJobRequest, SaveJobResponse, SaveJobStatus, SavedJobsRequest
from service.recommendation_service import fetch_saved_jobs
from service.recommendation_service import update_job_save_status, update_job_status_to_applied
from models.recommendation_models import RecommendationsRequest, RecommendationResponse
 
router = APIRouter(prefix="/recommendation", tags=["Recommendation"])
 
@router.post("/getRecommendations", response_model=RecommendationResponse)
async def recommendations(
    request: RecommendationsRequest, 
    user: tuple = Depends(get_current_user)  
):
    user_id = user[0]
    resume_id = get_user_active_resume_id(user_id)  
    
    if not resume_id:
        raise HTTPException(status_code=404, detail="Active resume not found for user")
    
    run_matcher()
    recs = get_top_recommendations(resume_id, request.top_n)
    return RecommendationResponse(
        resume_id=resume_id,
        recommendations=recs
    )

@router.post("/applyJob")
async def apply_job(request: ApplyJobRequest, user: tuple = Depends(get_current_user)):
    """Apply for a job by creating a candidate entry from the match"""

    print("Current user object:", user)
    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }

    email = user_dict.get("email")
        
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized Access"
        )

    success = create_candidate_from_match(request.match_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to apply for job"
        )

    update_result = update_job_status_to_applied(request.match_id)
    if not update_result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job status: {update_result.get('message')}"
        )

    return {
        "message": "Successfully applied to job",
        "match_id": request.match_id
    }

@router.post("/saveJob", response_model=SaveJobResponse)
async def save_job(
    request: SaveJobRequest,
    user: tuple = Depends(get_current_user)
):
    """
    Save a job recommendation by updating the save_status from 'not_saved' to 'saved'
    """

    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }

    email = user_dict.get("email")
        
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized Access"
        )
    
    try:
        result = update_job_save_status(
            match_id=request.match_id,
            save_status=SaveJobStatus.saved,
        )
        
        if result.get('success'):
            return SaveJobResponse(
                match_id=request.match_id,
                save_status=SaveJobStatus.saved
            )
        else:
            raise HTTPException(
                status_code=404,
                detail=result.get('message', "Match not found or could not be updated")
            )

    
    except Exception as e:
        print(f"Error saving job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save job: {str(e)}"
        )
    
@router.post("/getSavedJobs", response_model=RecommendationResponse)
async def get_saved_jobs(
    user: tuple = Depends(get_current_user)
):
    """
    Get all saved job recommendations for a resume.
    """
    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }

    user_id = user_dict.get("user_id")
    resume_id = get_user_active_resume_id(user_id) 

    results = fetch_saved_jobs(resume_id)
    return RecommendationResponse(
        resume_id=resume_id,
        recommendations=results
    )
