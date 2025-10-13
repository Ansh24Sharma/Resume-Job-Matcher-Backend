from pydantic import BaseModel
from typing import List, Dict
from enum import Enum

class SaveJobStatus(str, Enum):
    saved = "saved"
    not_saved = "not_saved"
    applied =  "applied"

class RecommendationsRequest(BaseModel):
    top_n: int = 5

class RecommendationResponse(BaseModel):
    resume_id: int
    recommendations: List[Dict]

class ApplyJobRequest(BaseModel):
    match_id: int

class SaveJobRequest(BaseModel):
    match_id: int

class SaveJobResponse(BaseModel):
    match_id: int
    save_status: SaveJobStatus

class SavedJobsRequest(BaseModel):
    resume_id: int