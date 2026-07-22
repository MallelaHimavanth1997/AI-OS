"""Applications router - handles tailored resume creation and retrieval."""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from backend.logging import get_logger
from database.models import Application, ApplicationStatus
from database.repositories import (
    create_session_factory,
    ResumeRepository,
    JobRepository,
    ApplicationRepository,
)
from agents.resume_intelligence_agent.agent import ResumeIntelligenceAgent
from agents.job_matching_agent.agent import JobMatchingAgent
from agents.resume_tailoring_agent.agent import ResumeTailoringAgent
from agents.resume_intelligence_agent.parser import ParsedJob
from api.src.schemas import ApplicationCreateRequest, ApplicationResponse, ApplicationListResponse

router = APIRouter(prefix="/applications", tags=["applications"])
logger = get_logger(bind={"component": "applications_router"})


async def get_session():
    """Dependency for database session."""
    async_session_factory = create_session_factory()
    async with async_session_factory() as session:
        yield session


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    request: ApplicationCreateRequest,
    session = Depends(get_session),
):
    """Create a tailored resume application for a job.
    
    Args:
        request: ApplicationCreateRequest with resume_id, job_id, and export format
        session: Database session
        
    Returns:
        ApplicationResponse with tailored resume metadata and file paths
        
    Raises:
        HTTPException 404: Resume or job not found
        HTTPException 500: Tailoring error
    """
    try:
        logger.info(
            "Creating tailored application",
            extra={
                "resume_id": request.resume_id,
                "job_id": request.job_id,
                "format": request.export_format,
            },
        )
        
        # Fetch resume and job
        resume_repo = ResumeRepository(session)
        job_repo = JobRepository(session)
        
        resume_record = await resume_repo.query_by_id(request.resume_id)
        job_record = await job_repo.query_by_id(request.job_id)
        
        if not resume_record:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not job_record:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Parse resume
        resume_agent = ResumeIntelligenceAgent()
        parsed_resume = resume_agent.parse_resume(resume_record.raw_text)
        
        # Parse job
        parsed_job = ParsedJob(
            title=job_record.title,
            company=job_record.company,
            description=job_record.description,
            required_skills=job_record.extra_metadata.get("required_skills", []),
            keywords=[job_record.title] + job_record.extra_metadata.get("required_skills", []),
        )
        
        # Match and tailor
        matcher = JobMatchingAgent()
        analysis = matcher.compare_parsed_resume_and_job(parsed_resume, parsed_job)
        match = analysis.match
        
        tailor_agent = ResumeTailoringAgent()
        tailored = tailor_agent.tailor_resume(parsed_resume, parsed_job, match)
        
        # Export in requested format(s)
        export_formats = []
        artifact_paths = {}
        
        if request.export_format in ("docx", "both"):
            docx_path = tailor_agent.tailor.export_docx(
                tailored, f"{parsed_resume.full_name or 'resume'}_{job_record.title}"
            )
            export_formats.append("docx")
            artifact_paths["docx"] = str(docx_path)
        
        if request.export_format in ("pdf", "both"):
            pdf_path = tailor_agent.tailor.export_pdf(
                tailored, f"{parsed_resume.full_name or 'resume'}_{job_record.title}"
            )
            export_formats.append("pdf")
            artifact_paths["pdf"] = str(pdf_path)
        
        # Store application in database
        app_id = str(uuid4())
        application_record = Application(
            id=app_id,
            user_id=None,  # Would be set by auth middleware in production
            resume_id=request.resume_id,
            job_id=request.job_id,
            status=ApplicationStatus.DRAFT,
            match_score=match.match_score,
            extra_metadata={
                "ats_score": tailored.ats_score,
                "matched_keywords": tailored.matched_keywords,
                "missing_keywords": tailored.missing_keywords,
                "recommendations": tailored.recommendations,
                "artifact_paths": artifact_paths,
                "export_formats": export_formats,
            },
            created_at=datetime.utcnow(),
        )
        
        await session.add(application_record)
        await session.commit()
        await session.refresh(application_record)
        
        logger.info(
            "Application created",
            extra={
                "app_id": app_id,
                "ats_score": tailored.ats_score,
                "formats": export_formats,
            },
        )
        
        # Determine primary tailored resume path
        tailored_resume_path = artifact_paths.get("docx") or artifact_paths.get("pdf", "")
        
        return ApplicationResponse(
            application_id=app_id,
            resume_id=request.resume_id,
            job_id=request.job_id,
            job_title=job_record.title,
            ats_score=tailored.ats_score,
            tailored_resume_path=tailored_resume_path,
            export_formats=export_formats,
            matched_keywords=tailored.matched_keywords,
            missing_keywords=tailored.missing_keywords,
            created_at=application_record.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating application",
            extra={"resume_id": request.resume_id, "job_id": request.job_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Application creation failed")


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    session = Depends(get_session),
):
    """Retrieve an application by ID.
    
    Args:
        application_id: UUID of application
        session: Database session
        
    Returns:
        ApplicationResponse with application details
        
    Raises:
        HTTPException 404: Application not found
    """
    try:
        app_repo = ApplicationRepository(session)
        app_record = await app_repo.query_by_id(application_id)
        
        if not app_record:
            raise HTTPException(status_code=404, detail="Application not found")
        
        job_repo = JobRepository(session)
        job_record = await job_repo.query_by_id(app_record.job_id)
        
        metadata = app_record.extra_metadata or {}
        
        return ApplicationResponse(
            application_id=app_record.id,
            resume_id=app_record.resume_id,
            job_id=app_record.job_id,
            job_title=job_record.title if job_record else "Unknown",
            ats_score=metadata.get("ats_score", 0.0),
            tailored_resume_path=list(metadata.get("artifact_paths", {}).values())[0]
            if metadata.get("artifact_paths")
            else "",
            export_formats=metadata.get("export_formats", []),
            matched_keywords=metadata.get("matched_keywords", []),
            missing_keywords=metadata.get("missing_keywords", []),
            created_at=app_record.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving application",
            extra={"application_id": application_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve application")


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session = Depends(get_session),
):
    """List all applications with pagination.
    
    Args:
        skip: Number of results to skip
        limit: Maximum results to return
        session: Database session
        
    Returns:
        ApplicationListResponse with paginated results
    """
    try:
        from sqlalchemy import select, func
        
        app_repo = ApplicationRepository(session)
        
        # Get total count
        count_result = await session.scalar(select(func.count(Application.id)))
        total = count_result or 0
        
        # Get paginated results
        query = select(Application).offset(skip).limit(limit).order_by(Application.created_at.desc())
        result = await session.execute(query)
        applications = result.scalars().all()
        
        job_repo = JobRepository(session)
        items = []
        
        for app in applications:
            job_record = await job_repo.query_by_id(app.job_id)
            metadata = app.extra_metadata or {}
            
            items.append(
                ApplicationResponse(
                    application_id=app.id,
                    resume_id=app.resume_id,
                    job_id=app.job_id,
                    job_title=job_record.title if job_record else "Unknown",
                    ats_score=metadata.get("ats_score", 0.0),
                    tailored_resume_path=list(metadata.get("artifact_paths", {}).values())[0]
                    if metadata.get("artifact_paths")
                    else "",
                    export_formats=metadata.get("export_formats", []),
                    matched_keywords=metadata.get("matched_keywords", []),
                    missing_keywords=metadata.get("missing_keywords", []),
                    created_at=app.created_at,
                )
            )
        
        return ApplicationListResponse(
            total=total,
            items=items,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit,
        )
        
    except Exception as e:
        logger.error("Error listing applications", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to list applications")
