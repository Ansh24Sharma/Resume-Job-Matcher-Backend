from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List

class RecruiterMatchSummary(BaseModel):
    match_id: int
    resume_id: int
    job_id: int
    job_source: str
    final_score: float
    title: str
    name: str
    updated_at: datetime

class MatchExplanation(BaseModel):
    resume_skills: List[str]
    resume_education: List[str]
    resume_experience: List[str]
    job_title: str
    job_skills: List[str]
    job_education: List[str]
    job_experience: List[str]
    scores: Dict[str, float]
    status: str
    updated_at: datetime

class MatchExplanationRequest(BaseModel):
    resume_id: int
    job_id: int
    job_source: str 