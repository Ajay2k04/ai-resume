from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request/Response Models
class ContactInfo(BaseModel):
    email: str
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    website: Optional[str] = ""

class Experience(BaseModel):
    title: str
    company: str
    duration: Optional[str] = None
    description: str

class ResumeData(BaseModel):
    name: str
    contact_info: ContactInfo
    skills: List[str]
    experience: List[Experience]
    education: List[str]
    summary: str
    projects: List[str]

class JobSearchRequest(BaseModel):
    job_titles: List[str]
    location: str
    remote_only: bool = False
    posted_within_days: int = 7
    num_results: int = 20

class JobResponse(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: str
    description: str
    job_url: Optional[str] = None
    company_url: Optional[str] = None
    source: Optional[str] = None
    posted_date: Optional[datetime] = None

class JobSearchResponse(BaseModel):
    jobs: List[JobResponse]
    total_count: int
    search_params: JobSearchRequest

class JobSelectionRequest(BaseModel):
    candidate_id: int
    job_id: int

class AIGenerationRequest(BaseModel):
    resume_data: ResumeData
    job_description: str
    job_title: str
    company_name: str
    contentType: str  # resume or cover_letter

class AIGenerationResponse(BaseModel):
    content: str
    status: str
    message: str

class ExportRequest(BaseModel):
    content: str
    filename: str
    format: str  # docx, pdf

class CandidateCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[str] = []
    summary: str = ""
    projects: List[str] = []

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[str] = []
    summary: str = ""
    projects: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
