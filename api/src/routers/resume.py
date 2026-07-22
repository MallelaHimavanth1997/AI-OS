"""Resume router - handles resume upload, parsing, and retrieval."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from backend.logging import get_logger
from database.models import Resume
from database.repositories import SessionLocal, create_session_factory
from agents.resume_intelligence_agent.agent import ResumeIntelligenceAgent
from api.src.schemas import ResumeUploadRequest, ResumeResponse

router = APIRouter(prefix="/resume", tags=["resume"])
logger = get_logger(bind={"component": "resume_router"})


async def get_session():
    """Dependency for database session."""
    async_session_factory = create_session_factory()
    async with async_session_factory() as session:
        yield session


@router.post("/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    request: ResumeUploadRequest,
    session = Depends(get_session)
):
    """Upload and parse a resume.
    
    Args:
        request: ResumeUploadRequest with resume_text
        session: Database session
        
    Returns:
        ResumeResponse with parsed resume metadata and stored ID
        
    Raises:
        HTTPException 400: Invalid resume format
        HTTPException 500: Parsing error
    """
    try:
        logger.info("Parsing resume", extra={"file_name": request.file_name})
        
        # Create agent and parse resume
        agent = ResumeIntelligenceAgent()
        parsed = agent.parse_resume(request.resume_text)
        
        # Generate embedding
        agent.embed_resume(parsed)
        
        # Store in database
        resume_id = str(uuid4())
        resume_record = Resume(
            id=resume_id,
            full_name=parsed.full_name or "Unknown",
            headline=parsed.headline,
            summary=parsed.summary,
            raw_text=request.resume_text,
            extra_metadata={
                "file_name": request.file_name,
                "skills_count": len(parsed.skills),
                "experience_count": len(parsed.experience),
                "education_count": len(parsed.education),
            },
            created_at=datetime.utcnow(),
        )
        
        await session.add(resume_record)
        await session.commit()
        await session.refresh(resume_record)
        
        logger.info("Resume stored", extra={"resume_id": resume_id})
        
        return ResumeResponse(
            resume_id=resume_id,
            full_name=parsed.full_name or "Unknown",
            headline=parsed.headline,
            summary=parsed.summary,
            skills=parsed.skills,
            experience_count=len(parsed.experience),
            education_count=len(parsed.education),
            keyword_count=len(parsed.keywords),
            created_at=resume_record.created_at,
        )
        
    except ValueError as e:
        logger.error("Resume parsing error", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=f"Invalid resume: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error parsing resume", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Resume parsing failed")


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, session = Depends(get_session)):
    """Retrieve a stored resume by ID.
    
    Args:
        resume_id: UUID of resume
        session: Database session
        
    Returns:
        ResumeResponse with full resume data
        
    Raises:
        HTTPException 404: Resume not found
    """
    try:
        from database.repositories import ResumeRepository
        
        repo = ResumeRepository(session)
        resume_record = await repo.query_by_id(resume_id)
        
        if not resume_record:
            logger.warning("Resume not found", extra={"resume_id": resume_id})
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Re-parse from raw text to get full structure
        agent = ResumeIntelligenceAgent()
        parsed = agent.parse_resume(resume_record.raw_text)
        
        return ResumeResponse(
            resume_id=resume_record.id,
            full_name=parsed.full_name or "Unknown",
            headline=parsed.headline,
            summary=parsed.summary,
            skills=parsed.skills,
            experience_count=len(parsed.experience),
            education_count=len(parsed.education),
            keyword_count=len(parsed.keywords),
            created_at=resume_record.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving resume", extra={"resume_id": resume_id, "error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve resume")
