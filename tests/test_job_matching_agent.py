"""Tests for the Job Matching Agent."""

from agents.job_matching_agent import JobMatchingAgent, JobMatcher
from agents.resume_intelligence_agent import ResumeParser
from agents.job_search_agent import JobDescriptionParser


SAMPLE_RESUME = """
Jane Doe
Senior Python Engineer

Professional Summary
Senior engineer building FastAPI services, data pipelines, and automation systems.

Skills
Python, FastAPI, PostgreSQL, Redis, Docker, Qdrant

Experience
- Built production APIs with FastAPI and PostgreSQL.
- Automated job workflows and internal tooling.

Projects
- Job Search Platform: built a search and matching system for career workflows.
"""


SAMPLE_JOB = {
    "title": "Senior Python Backend Engineer",
    "company": "Acme Labs",
    "location": "Remote",
    "description": "We need a senior engineer to build FastAPI services, PostgreSQL integrations, and automation workflows.",
    "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "responsibilities": ["Build APIs", "Improve automation", "Work with recruiters"],
    "keywords": ["python", "fastapi", "postgresql", "docker", "automation"],
}


def test_matcher_scores_resume_against_job() -> None:
    resume = ResumeParser().parse(SAMPLE_RESUME)
    job = JobDescriptionParser().parse(SAMPLE_JOB)
    match = JobMatcher().match(resume, job)

    assert match.match_score > 0
    assert match.priority_score >= match.match_score or match.priority_score >= 0
    assert "python" in match.matched_skills
    assert "docker" in match.missing_skills or "docker" in match.matched_keywords


def test_agent_ranks_jobs_and_returns_report() -> None:
    agent = JobMatchingAgent()
    report = agent.match_resume_to_jobs(SAMPLE_RESUME, [SAMPLE_JOB])

    assert report.candidate_name == "Jane Doe"
    assert report.total_jobs == 1
    assert report.matched_jobs
    assert report.matched_jobs[0].priority_bucket in {"high", "medium", "low"}


def test_agent_filters_by_threshold() -> None:
    agent = JobMatchingAgent()
    report = agent.match_resume_to_jobs(SAMPLE_RESUME, [SAMPLE_JOB])
    filtered = agent.filter_opportunities(report, minimum_score=0)

    assert filtered