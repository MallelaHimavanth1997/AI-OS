"""Tests for the Resume Tailoring Agent."""

from pathlib import Path

from agents.resume_tailoring_agent import ResumeTailoringAgent, ResumeTailor
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

Certifications
- AWS Certified Developer

Education
- Bachelor of Science in Computer Science
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


def test_resume_tailor_generates_truthful_ats_document() -> None:
    resume = ResumeParser().parse(SAMPLE_RESUME)
    job = JobDescriptionParser().parse(SAMPLE_JOB)
    document = ResumeTailor().build(resume, job, __import__("agents.job_matching_agent", fromlist=["JobMatcher"]).JobMatcher().match(resume, job))

    assert document.candidate_name == "Jane Doe"
    assert document.source_job_title == "Senior Python Backend Engineer"
    assert document.ats_score > 0
    assert "Python" in document.text or "python" in document.text.lower()


def test_agent_exports_docx_and_pdf(tmp_path: Path) -> None:
    agent = ResumeTailoringAgent()
    summary = agent.tailor_resume(SAMPLE_RESUME, SAMPLE_JOB, output_dir=tmp_path)

    assert summary.artifact.docx_path.exists()
    assert summary.artifact.pdf_path.exists()
    assert summary.ats_score > 0
    assert summary.matched_keywords


def test_agent_can_generate_document_without_export() -> None:
    agent = ResumeTailoringAgent()
    document = agent.generate_document(SAMPLE_RESUME, SAMPLE_JOB)

    assert document.title.startswith("Tailored Resume")
    assert document.recommendations
    assert document.missing_keywords or document.matched_keywords