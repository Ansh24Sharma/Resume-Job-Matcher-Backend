from pydantic import BaseModel
from typing import List, Optional

class ResumeUploadResponse(BaseModel):
    status: str
    resume: str
    entities: dict
    message: Optional[str] = None
    text_preview: Optional[str] = None
    profile_updated: bool = False

class ResumeListResponse(BaseModel):
    resumes: List[dict]

class ResumeDownloadRequest(BaseModel):
    user_id: Optional[int] = None
