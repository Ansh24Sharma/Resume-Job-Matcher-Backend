from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum
from datetime import datetime

class CandidateStatus(str, Enum):
    available = "available"
    interview_scheduled = "interview_scheduled"
    under_review = "under_review"
    hired = "hired"
    rejected = "rejected"

class JobSource(str, Enum):
    jobs = "jobs"
    posted_jobs = "posted_jobs"

class CandidateResponse(BaseModel):
    candidate_id: int
    match_id: int
    user_id: int
    profile_id: int
    job_id: int
    job_source: str
    status: str
    contacted_at: Optional[datetime] = None
    interview_scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    final_score: float
    bert_score: float
    skill_score: float
    education_score: float
    experience_score: float
    name: str
    email: str
    location: Optional[str] = None
    skills: List[str]
    experience: List[str]
    resume_filename: Optional[str] = None
    upload_date: Optional[datetime] = None
    job_title: str
    company: str

class CandidateDetailResponse(CandidateResponse):
    resume_file_path: Optional[str] = None
    job_description: Optional[str] = None

class CandidateStatusUpdate(BaseModel):
    candidate_id: int
    status: CandidateStatus

class InterviewScheduleRequest(BaseModel):
    candidate_id: int
    interview_date: datetime
    interview_time: str
    interview_type: str
    meeting_link: Optional[str] = None
    additional_notes: Optional[str] = None

class CandidateStatisticsResponse(BaseModel):
    total_candidates: int
    available: int
    interview_scheduled: int
    under_review: int
    hired: int
    rejected: int
    average_match_score: float
    recent_candidates: int

class CandidateListResponse(BaseModel):
    candidates: List[CandidateResponse]