from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
from service.resumes_service import insert_resume
from service.user_profiles_service import update_profile_from_resume
from pdf_loader import extract_text_from_uploaded_file
from entities import extract_entities
from auth import get_current_user
from models.resume_models import ResumeUploadResponse, ResumeDownloadRequest
import MySQLdb as sql
from config import DB_CONFIG

conn = sql.connect(**DB_CONFIG)
cursor = conn.cursor() 

router = APIRouter(prefix="/resume", tags=["Resume"])

# Create uploads directory if it doesn't exist
UPLOAD_DIRECTORY = "uploads/resumes"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@router.post("/uploadResume", response_model=ResumeUploadResponse)
async def upload_resume(resume: UploadFile = File(...), user: tuple = Depends(get_current_user)):
    try:
        print(f"[INFO] Processing uploaded resume: {resume.filename}")
        
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        
        user_id = user_dict.get("user_id")
        username = user_dict.get("username")
        
        # Validate file type
        if not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Create safe filename with standardized pattern: userid_username.pdf
        safe_filename = f"{user_id}_{username}.pdf"
        file_path = os.path.join(UPLOAD_DIRECTORY, safe_filename)
        
        # Check if user already has a resume and delete it (overwrite)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[INFO] Removed existing resume for user {user_id}")
            except Exception as e:
                print(f"[WARNING] Could not remove existing resume: {str(e)}")
        
        # Save file to disk
        try:
            contents = await resume.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Reset file pointer for text extraction
            await resume.seek(0)
        except Exception as e:
            print(f"[ERROR] Failed to save file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save resume file"
            )
        
        # Extract text using the improved function
        raw_text = extract_text_from_uploaded_file(resume.file)
        
        if not raw_text or len(raw_text.strip()) < 50:
            # Clean up saved file if text extraction failed
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return {
                "status": "error", 
                "resume": resume.filename, 
                "message": "Could not extract sufficient text from PDF",
                "entities": {"skills": [], "education": [], "experience": []},
                "profile_updated": False
            }
        
        print(f"[INFO] Extracted {len(raw_text)} characters from {resume.filename}")
        
        # Extract entities
        entities = extract_entities(raw_text)
        print(f"[INFO] Entities extracted: {entities}")
        
        # Check if resume already exists in database for this user
        try:
            # Delete existing resume record if exists
            delete_existing_resume_query = """
                DELETE FROM resumes WHERE user_id = %s
            """
            cursor.execute(delete_existing_resume_query, (user_id,))
            conn.commit()
            print(f"[INFO] Removed existing resume record for user {user_id}")
        except Exception as e:
            print(f"[WARNING] Error checking/deleting existing resume: {str(e)}")
            conn.rollback()
        
        # Store the raw text (not cleaned) to preserve formatting for preview
        try:
            insert_resume(name=safe_filename, description=raw_text, entities=entities, user_id=user_id)
            
            # Update user profile with resume data
            profile_updated = update_profile_from_resume(
                user_id, 
                safe_filename, 
                file_path, 
                entities
            )
            
            if not profile_updated:
                print(f"[WARNING] Failed to update profile for user {user_id}")
            
        except Exception as e:
            # Clean up saved file if database operations failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
        
        return {
            "status": "success", 
            "resume": resume.filename, 
            "entities": entities,
            "text_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
            "profile_updated": profile_updated,
            "message": "Resume uploaded and profile updated successfully (previous resume overwritten if existed)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to process {resume.filename}: {str(e)}")
        
        # Clean up any saved files in case of error
        safe_filename = f"{user_id}_{username}.pdf"
        file_path = os.path.join(UPLOAD_DIRECTORY, safe_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process resume: {str(e)}"
        )

@router.post("/download")
async def download_resume(request: ResumeDownloadRequest, user: tuple = Depends(get_current_user)):
    """
    Download resume file. 
    - Regular users can download their own resume (don't need to provide user_id)
    - Admin/Recruiter can download any user's resume by providing user_id
    """
    try:
        user_dict = {
            "user_id": user[0],
            "username": user[1],
            "email": user[2],
            "hashed_password": user[3],
            "role": user[4]
        }
        
        current_user_id = user_dict.get("user_id")
        current_user_role = user_dict.get("role")
        
        # Determine which user's resume to download
        target_user_id = request.user_id
        
        # If no user_id provided, use current user's ID
        if target_user_id is None:
            target_user_id = current_user_id
        
        # Check permissions: only admin/recruiter can download other users' resumes
        if target_user_id != current_user_id and current_user_role not in ["admin", "recruiter"]:
            raise HTTPException(
                status_code=403,
                detail="You can only download your own resume"
            )
        
        # Get the target user's username from database
        try:
            query = "SELECT name FROM user_profiles WHERE user_id = %s"
            cursor.execute(query, (target_user_id,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            target_username = result[0]
        except Exception as e:
            print(f"[ERROR] Failed to fetch user: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve user information"
            )
        
        # Construct filename using standardized pattern
        filename = f"{target_user_id}_{target_username}.pdf"
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Resume file not found for user {target_username}"
            )
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=f"{target_username}_resume.pdf",
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to download resume: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download resume"
        )