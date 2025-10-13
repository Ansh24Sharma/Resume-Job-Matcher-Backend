from fastapi import APIRouter, Depends
from auth import get_current_user
from service.resumes_service import get_all_resumes
from service.jobs_service import get_all_jobs
from service.matches_service import get_match_scores
 
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
 
@router.get("/recruiter")
async def recruiter_dashboard(user: dict = Depends(get_current_user)):
    resumes = get_all_resumes()
    jobs = get_all_jobs()
    scores = get_match_scores()
    return {"resumes": resumes, "jobs": jobs, "scores": scores}
 
@router.get("/stats")
async def stats(user: dict = Depends(get_current_user)):
    return {
        "total_resumes": len(get_all_resumes()),
        "total_jobs": len(get_all_jobs()),
        # "top_skills": ["Python", "SQL", "React"],  
    }
 