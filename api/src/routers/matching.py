"""Matching router - handles resume-to-job matching and ranking."""

import logging
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from uuid import uuid4

from backend.logging import get_logger
from database.models import ApplicationStatus
from database.repositories import create_session_factory, ResumeRepository, JobRepository
from agents.resume_intelligence_agent.agent import ResumeIntelligenceAgent
from agents.job_matching_agent.agent import JobMatchingAgent
from api.src.schemas import MatchRequest, MatchResponse, MatchBreakdownResponse

router = APIRouter(prefix="/match", tags=["matching"])
logger = get_logger(bind={"component": "match_router"})


async def get_session():
    """Dependency for database session."""
    async_session_factory = create_session_factory()
    async with async_session_factory() as session:
        yield session


@router.post("", response_model=MatchResponse, status_code=200)
async def match_resume_to_job(
    request: MatchRequest,
    session = Depends(get_session),
):
    """Match a resume to a job and compute fit score.
    
    Args:
        request: MatchRequest with resume_id and job_id
        session: Database session
        
    Returns:
        MatchResponse with match score breakdown
        
    Raises:
        HTTPException 404: Resume or job not found
        HTTPException 500: Matching error
    """
    try:
        logger.info(
            "Matching resume to job",
            extra={"resume_id": request.resume_id, "job_id": request.job_id},
        )
        
        # Fetch resume and job from database
        resume_repo = ResumeRepository(session)
        job_repo = JobRepository(session)
        
        resume_record = await resume_repo.query_by_id(request.resume_id)
        job_record = await job_repo.query_by_id(request.job_id)
        
        if not resume_record:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not job_record:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Parse resume and job
        resume_agent = ResumeIntelligenceAgent()
        parsed_resume = resume_agent.parse_resume(resume_record.raw_text)
        
        # Parse job description
        parsed_job = resume_agent.parser.parse(job_record.description)
        from agents.resume_intelligence_agent.parser import ParsedJob
        parsed_job_obj = ParsedJob(
            title=job_record.title,
            company=job_record.company,
            description=job_record.description,
            required_skills=job_record.extra_metadata.get("required_skills", []),
            keywords=[job_record.title] + job_record.extra_metadata.get("required_skills", []),
        )
        
        # Match resume to job
        matcher = JobMatchingAgent()
        analysis = matcher.compare_parsed_resume_and_job(parsed_resume, parsed_job_obj)
        match = analysis.match
        
        match_id = str(uuid4())
        
        logger.info(
            "Match computed",
            extra={
                "match_id": match_id,
                "score": match.match_score,
                "priority": match.priority_score,
            },
        )
        
        breakdown = MatchBreakdownResponse(
            match_score=match.match_score,
            priority_score=match.priority_score,
            skill_match_percentage=match.skill_match_percentage,
            keyword_match_percentage=match.keyword_match_percentage,
            experience_match_percentage=match.experience_match_percentage,
            matched_skills=list(match.matched_skills),
            missing_skills=list(match.missing_skills),
            recommendations=match.recommendations,
        )
        
        return MatchResponse(
            match_id=match_id,
            resume_id=request.resume_id,
            job_id=request.job_id,
            job_title=job_record.title,
            match_breakdown=breakdown,
            is_good_fit=match.match_score >= 65,
            created_at=datetime.utcnow(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error matching resume to job",
            extra={"resume_id": request.resume_id, "job_id": request.job_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Matching failed")


@router.post("/rank", response_model=dict)
async def rank_resume_against_jobs(
    resume_id: str,
    job_ids: list[str],
    session = Depends(get_session),
):
    """Rank multiple jobs for a single resume.
    
    Args:
        resume_id: UUID of resume
        job_ids: List of job UUIDs to rank
        session: Database session
        
    Returns:
        Dict with ranked jobs sorted by match score descending
    """
    try:
        logger.info(
            "Ranking jobs for resume",
            extra={"resume_id": resume_id, "job_count": len(job_ids)},
        )
        
        resume_repo = ResumeRepository(session)
        job_repo = JobRepository(session)
        
        resume_record = await resume_repo.query_by_id(resume_id)
        if not resume_record:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Parse resume once
        resume_agent = ResumeIntelligenceAgent()
        parsed_resume = resume_agent.parse_resume(resume_record.raw_text)
        matcher = JobMatchingAgent()
        
        # Fetch and match all jobs
        results = []
        for job_id in job_ids:
            job_record = await job_repo.query_by_id(job_id)
            if not job_record:
                continue
            
            from agents.resume_intelligence_agent.parser import ParsedJob
            parsed_job = ParsedJob(
                title=job_record.title,
                company=job_record.company,
                description=job_record.description,
                required_skills=job_record.extra_metadata.get("required_skills", []),
                keywords=[job_record.title] + job_record.extra_metadata.get("required_skills", []),
            )
            
            analysis = matcher.compare_parsed_resume_and_job(parsed_resume, parsed_job)
            match = analysis.match
            
            results.append({
                "job_id": job_id,
                "title": job_record.title,
                "company": job_record.company,
                "match_score": match.match_score,
                "priority_score": match.priority_score,
                "is_good_fit": match.match_score >= 65,
                "matched_skills": list(match.matched_skills),
                "missing_skills": list(match.missing_skills),
            })
        
        # Sort by priority_score (desc), then match_score (desc)
        results.sort(key=lambda x: (x["priority_score"], x["match_score"]), reverse=True)
        
        logger.info("Jobs ranked", extra={"resume_id": resume_id, "count": len(results)})
        
        return {
            "resume_id": resume_id,
            "ranked_jobs": results,
            "total": len(results),
            "good_fits": sum(1 for r in results if r["is_good_fit"]),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error ranking jobs",
            extra={"resume_id": resume_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Ranking failed")
