from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import pandas as pd
from io import BytesIO
import json            
from service.jobs_service import insert_job, get_all_jobs, get_jobs_by_creator, update_job
from service.posted_jobs_service import insert_posted_job, get_all_posted_jobs, get_posted_jobs_by_creator, update_posted_job
from pdf_loader import extract_text_from_uploaded_file
from entities import extract_entities
from preprocess import clean_text
from auth import get_current_user
from models.job_models import JobUploadResponse, JobPosting, JobListResponse, JobUpdateResponse, JobUpdateRequest
 
router = APIRouter(prefix="/job", tags=["Job"])
 
@router.post("/uploadJob", response_model=JobUploadResponse)
async def upload_job(job: UploadFile = File(...), user: tuple = Depends(get_current_user)):
    try:
        print(f"[INFO] Processing uploaded job: {job.filename}")
        
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        # Get creator email from user
        creator_email = user_dict.get("email")
        
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
    
@router.post("/bulkUploadJobs", response_model=dict)
async def bulk_upload_jobs(
    file: UploadFile = File(...),
    user: tuple = Depends(get_current_user)
):
    """
    Bulk upload jobs from Excel or CSV file (.xlsx, .xls, .csv)
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            return {
                "status": "error",
                "message": "Invalid file type. Please upload Excel (.xlsx, .xls) or CSV (.csv) file",
                "successful_uploads": 0,
                "failed_uploads": 0,
                "errors": []
            }
        
        print(f"[INFO] Processing bulk upload file: {file.filename}")
        
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }

        # Get creator email from user
        creator_email = user_dict.get("email")
        
        # Read file contents
        contents = await file.read()
        
        try:
            # Read file into DataFrame based on file type
            if file.filename.endswith('.csv'):
                # Read CSV file
                df = pd.read_csv(BytesIO(contents))
                print(f"[INFO] Reading CSV file")
            else:
                # Read Excel file
                df = pd.read_excel(BytesIO(contents))
                print(f"[INFO] Reading Excel file")
            
            print(f"[INFO] Found {len(df)} rows in file")
            
            # Required columns
            required_columns = ['title', 'company', 'location', 'job_type']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    "status": "error",
                    "message": f"Missing required columns: {', '.join(missing_columns)}",
                    "successful_uploads": 0,
                    "failed_uploads": 0,
                    "errors": [f"Required columns: {', '.join(required_columns)}"]
                }
            
            # Valid enum values
            valid_job_types = ['full-time', 'part-time', 'internship', 'remote']
            valid_status = ['active', 'closed']
            
            successful_uploads = 0
            failed_uploads = 0
            errors = []
            
            # Process each row
            for index, row in df.iterrows():
                row_num = index + 2  # +2 because file is 1-indexed and has header row
                
                try:
                    # Validate required fields
                    if pd.isna(row['title']) or not str(row['title']).strip():
                        errors.append(f"Row {row_num}: Title is required")
                        failed_uploads += 1
                        continue
                    
                    if pd.isna(row['company']) or not str(row['company']).strip():
                        errors.append(f"Row {row_num}: Company is required")
                        failed_uploads += 1
                        continue
                    
                    if pd.isna(row['location']) or not str(row['location']).strip():
                        errors.append(f"Row {row_num}: Location is required")
                        failed_uploads += 1
                        continue
                    
                    if pd.isna(row['job_type']) or not str(row['job_type']).strip():
                        errors.append(f"Row {row_num}: Job type is required")
                        failed_uploads += 1
                        continue
                    
                    # Validate job_type (case-insensitive)
                    job_type = str(row['job_type']).strip().lower()
                    if job_type not in valid_job_types:
                        errors.append(f"Row {row_num}: Invalid job_type '{job_type}'. Must be one of: {', '.join(valid_job_types)}")
                        failed_uploads += 1
                        continue
                    
                    # Prepare basic job data
                    title = str(row['title']).strip()
                    company = str(row['company']).strip()
                    location = str(row['location']).strip()
                    
                    # Description (optional)
                    description = ""
                    if 'description' in df.columns and not pd.isna(row['description']):
                        desc = str(row['description']).strip()
                        if desc:
                            description = f"<p>{desc}</p>"
                    
                    # Prepare entities dictionary
                    entities = {
                        "skills": [],
                        "education": [],
                        "experience": []
                    }
                    
                    # Skills (optional, comma-separated)
                    if 'skills' in df.columns and not pd.isna(row['skills']):
                        skills_text = str(row['skills']).strip()
                        if skills_text:
                            entities['skills'] = [s.strip() for s in skills_text.split(',') if s.strip()]
                    
                    # Education (optional, comma-separated)
                    if 'education' in df.columns and not pd.isna(row['education']):
                        education_text = str(row['education']).strip()
                        if education_text:
                            entities['education'] = [e.strip() for e in education_text.split(',') if e.strip()]
                    
                    # Experience (optional, comma-separated)
                    if 'experience' in df.columns and not pd.isna(row['experience']):
                        experience_text = str(row['experience']).strip()
                        if experience_text:
                            entities['experience'] = [e.strip() for e in experience_text.split(',') if e.strip()]
                    
                    # Salary (optional)
                    salary = None
                    if 'salary' in df.columns and not pd.isna(row['salary']):
                        salary_text = str(row['salary']).strip()
                        if salary_text:
                            salary = salary_text
                    
                    # Status validation (optional, not used in insert_posted_job but logged)
                    if 'status' in df.columns and not pd.isna(row['status']):
                        status = str(row['status']).strip().lower()
                        if status not in valid_status:
                            errors.append(f"Row {row_num}: Invalid status '{status}'. Valid values: {', '.join(valid_status)}")
                    
                    # Insert into database using insert_posted_job
                    job_id = insert_posted_job(
                        title=title,
                        description=description,
                        entities=entities,
                        company=company,
                        location=location,
                        job_type=job_type,
                        salary=salary,
                        creator_email=creator_email
                    )
                    
                    if job_id:
                        successful_uploads += 1
                        print(f"[INFO] Successfully uploaded job: {title} - Row {row_num} (ID: {job_id})")
                    else:
                        failed_uploads += 1
                        errors.append(f"Row {row_num}: Failed to insert job into database")
                
                except Exception as e:
                    failed_uploads += 1
                    errors.append(f"Row {row_num}: {str(e)}")
                    print(f"[ERROR] Row {row_num}: {str(e)}")
            
            # Prepare response
            status = "success" if successful_uploads > 0 else "error"
            message = f"Processed {len(df)} rows: {successful_uploads} successful, {failed_uploads} failed"
            
            return {
                "status": status,
                "message": message,
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "errors": errors[:10] if errors else []  # Limit to first 10 errors
            }
        
        except Exception as e:
            print(f"[ERROR] Error processing file: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing file: {str(e)}",
                "successful_uploads": 0,
                "failed_uploads": 0,
                "errors": [str(e)]
            }
    
    except Exception as e:
        print(f"[ERROR] Bulk upload error: {str(e)}")
        return {
            "status": "error",
            "message": f"Upload failed: {str(e)}",
            "successful_uploads": 0,
            "failed_uploads": 0,
            "errors": [str(e)]
        }
    
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
