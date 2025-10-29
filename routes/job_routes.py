from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from service.jobs_service import insert_job, get_all_jobs, get_jobs_by_creator, update_job
from service.posted_jobs_service import insert_posted_job, get_all_posted_jobs, get_posted_jobs_by_creator, update_posted_job
from pdf_loader import extract_text_from_uploaded_file
from entities import extract_entities
from preprocess import clean_text
from auth import get_current_user
from models.job_models import JobUploadResponse, JobPosting, JobListResponse, JobUpdateResponse, JobUpdateRequest
 
router = APIRouter(prefix="/job", tags=["Job"])
 
@router.post("/uploadJob", response_model=JobUploadResponse)
async def upload_job(job: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        print(f"[INFO] Processing uploaded job: {job.filename}")
        
        # Get creator email from user
        creator_email = user.get("email")
        
        # Extract text using the improved function
        raw_text = extract_text_from_uploaded_file(job.file)
        
        if not raw_text or len(raw_text.strip()) < 50:
            return {
                "status": "error", 
                "job": job.filename, 
                "message": "Could not extract sufficient text from PDF",
                "entities": {"skills": [], "education": [], "experience": []}
            }
        
        print(f"[INFO] Extracted {len(raw_text)} characters from {job.filename}")
        
        # Extract entities
        entities = extract_entities(raw_text)
        print(f"[INFO] Entities extracted: {entities}")
        
        # Store the raw text (not cleaned) to preserve formatting for preview
        # job_source will be automatically set to 'jobs' in insert_job
        job_id = insert_job(
            title=job.filename, 
            description=raw_text, 
            entities=entities,
            creator_email=creator_email
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "job": job.filename, 
            "entities": entities,
            "text_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to process {job.filename}: {str(e)}")
        return {
            "status": "error",
            "job": job.filename,
            "message": str(e),
            "entities": {"skills": [], "education": [], "experience": []}
        }


@router.post("/postJob", response_model=JobUploadResponse)
def post_job(job: JobPosting, user: tuple = Depends(get_current_user)):
    """
    Post a new job with job type and salary information.
    This creates an entry in the posted_jobs table with all the new fields.
    For posted jobs, we use the provided entities directly instead of extracting them.
    job_source will be automatically set to 'posted_jobs'
    """
    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }

    # Get creator email from user
    creator_email = user_dict.get("email")

    try:        
        # For posted jobs, create entities dict from provided fields directly
        entities = {
            "skills": job.skills if job.skills else [],
            "education": job.education if job.education else [],
            "experience": job.experience if job.experience else []
        }

        # Insert job into posted_jobs table with new fields
        # job_source will be automatically set to 'posted_jobs' in insert_posted_job
        job_id = insert_posted_job(
            title=job.title,
            description=job.description,
            entities=entities,
            company=job.company,
            location=job.location,
            job_type=job.job_type.value, 
            salary=job.salary,
            creator_email=creator_email
        )

        if job_id is None:
            raise HTTPException(status_code=500, detail="Failed to insert job into database")

        return JobUploadResponse(
            status="success",
            job_id=job_id,
            job=job.title,
            entities=entities,
            job_type=job.job_type,
            salary=job.salary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting job: {e}")
 
@router.get("/getAllJobs", response_model=JobListResponse)
def list_jobs():
    """
    Fetch all jobs for recruiter dashboard.
    """
    jobs = get_all_jobs()
    posted_jobs = get_all_posted_jobs()
    return JobListResponse(
        jobs=jobs,
        posted_jobs=posted_jobs
        )

@router.get("/getJobsByCreator", response_model=JobListResponse)
def list_jobs(user: tuple = Depends(get_current_user)):
    """
    Fetch all jobs and posted jobs created by the logged-in recruiter.
    """
    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }
    creator_email = user_dict.get("email")
    if not creator_email:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized Access"
        )
    jobs = get_jobs_by_creator(creator_email)
    posted_jobs = get_posted_jobs_by_creator(creator_email)
    return JobListResponse(
        jobs=jobs,
        posted_jobs=posted_jobs
    )

@router.put("/updateJob", response_model=JobUpdateResponse)
def update_job_endpoint(
    job_data: JobUpdateRequest,
    user: tuple = Depends(get_current_user)
):
    """
    Update a job (either from jobs or posted_jobs table).
    Can update any field including status.
    """
    user_dict = {
        "user_id": user[0],
        "username": user[1],
        "email": user[2],
        "hashed_password": user[3],
        "role": user[4]
    }
    
    creator_email = user_dict.get("email")
    if not creator_email:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized Access"
        )
    
    try:
        job_id = job_data.job_id
        job_source = job_data.job_source

        try:
            job_dict = job_data.model_dump()
        except AttributeError:
            job_dict = job_data.dict()
        
        # Filter out None values and exclude job_id/job_source from update data
        update_data = {
            k: v for k, v in job_dict.items()
            if v is not None and k not in ['job_id', 'job_source']
        }
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No valid fields provided for update"
            )
        
        if job_source == "jobs":
            updated_job = update_job(job_id, creator_email, update_data)
            job_type_name = "Job"
        elif job_source == "posted_jobs":
            updated_job = update_posted_job(job_id, creator_email, update_data)
            job_type_name = "Posted job"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid job_source. Must be 'jobs' or 'posted_jobs'"
            )
        
        if not updated_job:
            raise HTTPException(
                status_code=404,
                detail=f"{job_type_name} not found or you don't have permission to update it"
            )
        
        return JobUpdateResponse(
            success=True,
            message=f"{job_type_name} updated successfully",
            job=updated_job
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating job: {str(e)}"
        )
