"""Jobs router - handles job posting creation and retrieval."""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from uuid import uuid4

from backend.logging import get_logger
from database.models import Job
from database.repositories import create_session_factory
from api.src.schemas import JobCreateRequest, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = get_logger(bind={"component": "jobs_router"})


async def get_session():
    """Dependency for database session."""
    async_session_factory = create_session_factory()
    async with async_session_factory() as session:
        yield session


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(request: JobCreateRequest, session = Depends(get_session)):
    """Create a new job posting.
    
    Args:
        request: JobCreateRequest with job details
        session: Database session
        
    Returns:
        JobResponse with stored job ID
        
    Raises:
        HTTPException 400: Invalid job data
        HTTPException 500: Database error
    """
    try:
        logger.info("Creating job", extra={"title": request.title, "company": request.company})
        
        job_id = str(uuid4())
        job_record = Job(
            id=job_id,
            title=request.title,
            company=request.company,
            description=request.description,
            location=request.location,
            salary_range=request.salary_range,
            job_url=request.job_url,
            extra_metadata={
                "required_skills": request.required_skills,
                "created_via": "api",
            },
            created_at=datetime.utcnow(),
        )
        
        await session.add(job_record)
        await session.commit()
        await session.refresh(job_record)
        
        logger.info("Job created", extra={"job_id": job_id})
        
        description_preview = (
            request.description[:200] + "..."
            if len(request.description) > 200
            else request.description
        )
        
        return JobResponse(
            job_id=job_id,
            title=request.title,
            company=request.company,
            description_preview=description_preview,
            required_skills_count=len(request.required_skills),
            created_at=job_record.created_at,
        )
        
    except Exception as e:
        logger.error("Error creating job", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, session = Depends(get_session)):
    """Retrieve a job posting by ID.
    
    Args:
        job_id: UUID of job
        session: Database session
        
    Returns:
        JobResponse with job details
        
    Raises:
        HTTPException 404: Job not found
    """
    try:
        from database.repositories import JobRepository
        
        repo = JobRepository(session)
        job_record = await repo.query_by_id(job_id)
        
        if not job_record:
            logger.warning("Job not found", extra={"job_id": job_id})
            raise HTTPException(status_code=404, detail="Job not found")
        
        description_preview = (
            job_record.description[:200] + "..."
            if len(job_record.description) > 200
            else job_record.description
        )
        
        skills_count = len(job_record.extra_metadata.get("required_skills", []))
        
        return JobResponse(
            job_id=job_record.id,
            title=job_record.title,
            company=job_record.company,
            description_preview=description_preview,
            required_skills_count=skills_count,
            created_at=job_record.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving job", extra={"job_id": job_id, "error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to retrieve job")


@router.get("", response_model=dict)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session = Depends(get_session),
):
    """List all jobs with pagination.
    
    Args:
        skip: Number of results to skip
        limit: Maximum results to return
        session: Database session
        
    Returns:
        Dict with total count and list of JobResponse items
    """
    try:
        from database.repositories import JobRepository
        from sqlalchemy import select, func
        
        repo = JobRepository(session)
        
        # Get total count
        count_result = await session.scalar(select(func.count(Job.id)))
        total = count_result or 0
        
        # Get paginated results
        query = select(Job).offset(skip).limit(limit)
        result = await session.execute(query)
        jobs = result.scalars().all()
        
        items = []
        for job in jobs:
            description_preview = (
                job.description[:200] + "..."
                if len(job.description) > 200
                else job.description
            )
            skills_count = len(job.extra_metadata.get("required_skills", []))
            items.append(
                JobResponse(
                    job_id=job.id,
                    title=job.title,
                    company=job.company,
                    description_preview=description_preview,
                    required_skills_count=skills_count,
                    created_at=job.created_at,
                )
            )
        
        return {
            "total": total,
            "items": items,
            "skip": skip,
            "limit": limit,
        }
        
    except Exception as e:
        logger.error("Error listing jobs", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to list jobs")
