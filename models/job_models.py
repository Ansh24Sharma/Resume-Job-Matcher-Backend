from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum

class JobType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    internship = "internship"
    remote = "remote"

class JobStatus(str, Enum):
    active = "active"
    closed = "closed"

class JobUploadResponse(BaseModel):
    status: str
    job: str
    entities: dict
    message: Optional[str] = None
    text_preview: Optional[str] = None

class JobListResponse(BaseModel):
    jobs: List[dict]
    posted_jobs: List[dict]

class JobPosting(BaseModel):
    title: str
    company: str
    location: str
    job_type: JobType
    experience: List[str]
    salary: List[str]
    description: str
    education: List[str] 
    skills: List[str]
    status: JobStatus = JobStatus.active

class JobUpdateRequest(BaseModel):
    job_id: int
    job_source: str
    title: Optional[str] = None
    description: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[List[str]] = None
    experience: Optional[List[str]] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    salary: Optional[str] = None
    status: Optional[JobStatus] = None

class JobUpdateResponse(BaseModel):
    success: bool
    message: str
    job: Optional[dict] = None
