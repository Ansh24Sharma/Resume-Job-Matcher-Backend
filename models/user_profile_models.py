from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    experience: List[str] = []
    skills: List[str] = []
    education: List[str] = []
    location: Optional[str] = None
    resume_filename: Optional[str] = None
    resume_file_path: Optional[str] = None
    upload_date: Optional[datetime] = None
    completion_percentage: int = 0
    created_at: datetime
    updated_at: datetime

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    experience: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    education: Optional[List[str]] = None
    location: Optional[str] = None

class UserProfileSummary(BaseModel):
    id: int
    user_id: int
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    skills_count: int = 0
    experience_count: int = 0
    profile_completed: bool = False
    resume_uploaded: bool = False
    last_updated: datetime