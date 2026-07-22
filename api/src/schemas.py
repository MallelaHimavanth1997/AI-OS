"""Request/Response schemas for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResumeUploadRequest(BaseModel):
    """Resume upload request."""
    resume_text: str = Field(..., description="Resume content as plain text")
    file_name: Optional[str] = Field(None, description="Original filename for metadata")


class ResumeResponse(BaseModel):
    """Resume parsed and stored response."""
    resume_id: str = Field(..., description="UUID of stored resume")
    full_name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience_count: int = 0
    education_count: int = 0
    keyword_count: int = 0
    created_at: datetime


class JobCreateRequest(BaseModel):
    """Job creation request."""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    required_skills: list[str] = Field(default_factory=list, description="Required skills")
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None


class JobResponse(BaseModel):
    """Job stored response."""
    job_id: str = Field(..., description="UUID of stored job")
    title: str
    company: str
    description_preview: str = Field(..., description="First 200 chars of description")
    required_skills_count: int
    created_at: datetime


class MatchBreakdownResponse(BaseModel):
    """Match score breakdown."""
    match_score: float = Field(..., ge=0, le=100)
    priority_score: float = Field(..., ge=0, le=100)
    skill_match_percentage: float
    keyword_match_percentage: float
    experience_match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    """Resume-to-job matching request."""
    resume_id: str = Field(..., description="UUID of resume")
    job_id: str = Field(..., description="UUID of job")


class MatchResponse(BaseModel):
    """Match analysis response."""
    match_id: str = Field(..., description="UUID of match record")
    resume_id: str
    job_id: str
    job_title: str
    match_breakdown: MatchBreakdownResponse
    is_good_fit: bool = Field(..., description="True if match_score >= 65")
    created_at: datetime


class ApplicationCreateRequest(BaseModel):
    """Tailored application creation request."""
    resume_id: str = Field(..., description="UUID of resume")
    job_id: str = Field(..., description="UUID of job")
    export_format: Optional[str] = Field(
        "docx", description="Export format: docx, pdf, or both"
    )


class ApplicationResponse(BaseModel):
    """Tailored application stored response."""
    application_id: str = Field(..., description="UUID of application")
    resume_id: str
    job_id: str
    job_title: str
    ats_score: float
    tailored_resume_path: str = Field(..., description="Path to tailored resume file")
    export_formats: list[str] = Field(..., description="['docx', 'pdf']")
    matched_keywords: list[str]
    missing_keywords: list[str]
    created_at: datetime


class ApplicationListResponse(BaseModel):
    """Paginated list of applications."""
    total: int
    items: list[ApplicationResponse]
    page: int
    page_size: int
