"""Orchestration for the Resume Tailoring Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from backend.logging import get_logger

from agents.job_matching_agent import JobMatchingAgent
from agents.job_search_agent import JobDescriptionParser, ParsedJob
from agents.resume_intelligence_agent import ParsedResume, ResumeParser

from .config import ResumeTailoringConfig, get_resume_tailoring_config
from .tailor import ResumeTailor, TailoredResumeDocument


@dataclass(slots=True)
class TailoredResumeArtifact:
    """Generated tailored resume files and metadata."""

    document: TailoredResumeDocument
    docx_path: Path
    pdf_path: Path


@dataclass(slots=True)
class TailoredResumeSummary:
    """High-level response from the tailoring agent."""

    candidate_name: str
    target_job_title: str
    ats_score: float
    artifact: TailoredResumeArtifact
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class ResumeTailoringAgent:
    """Tailor resumes for a specific target job and export final documents."""

    def __init__(
        self,
        *,
        config: ResumeTailoringConfig | None = None,
        resume_parser: ResumeParser | None = None,
        job_parser: JobDescriptionParser | None = None,
        matcher: JobMatchingAgent | None = None,
        tailor: ResumeTailor | None = None,
    ) -> None:
        self.config = config or get_resume_tailoring_config()
        self.resume_parser = resume_parser or ResumeParser()
        self.job_parser = job_parser or JobDescriptionParser()
        self.matcher = matcher or JobMatchingAgent()
        self.tailor = tailor or ResumeTailor()
        self.logger = get_logger(bind={"component": "resume_tailoring_agent"})

    def tailor_resume(
        self,
        resume_input: str | Mapping[str, Any],
        job_input: str | Mapping[str, Any],
        *,
        output_dir: str | Path | None = None,
    ) -> TailoredResumeSummary:
        """Generate ATS-safe tailored resume files for a target job."""

        resume = self.resume_parser.parse(resume_input)
        job = self.job_parser.parse(job_input)
        match = self.matcher.compare_parsed_resume_and_job(resume, job).match
        document = self.tailor.build(resume, job, match)

        destination_dir = Path(output_dir) if output_dir else self.config.output_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        stem = self._slugify(f"{resume.full_name}-{job.title}")
        docx_path = self.tailor.export_docx(document, destination_dir / f"{stem}.docx")
        pdf_path = self.tailor.export_pdf(document, destination_dir / f"{stem}.pdf")

        artifact = TailoredResumeArtifact(document=document, docx_path=docx_path, pdf_path=pdf_path)
        summary = TailoredResumeSummary(
            candidate_name=resume.full_name,
            target_job_title=job.title,
            ats_score=document.ats_score,
            artifact=artifact,
            matched_keywords=document.matched_keywords,
            missing_keywords=document.missing_keywords,
            recommendations=document.recommendations,
        )

        self.logger.info(
            "Resume tailored",
            candidate=resume.full_name,
            target=job.title,
            ats_score=document.ats_score,
            docx=str(docx_path),
            pdf=str(pdf_path),
        )
        return summary

    def generate_document(self, resume_input: str | Mapping[str, Any], job_input: str | Mapping[str, Any]) -> TailoredResumeDocument:
        """Generate a tailored resume document without writing files."""

        resume = self.resume_parser.parse(resume_input)
        job = self.job_parser.parse(job_input)
        match = self.matcher.compare_parsed_resume_and_job(resume, job).match
        return self.tailor.build(resume, job, match)

    def export_document(self, document: TailoredResumeDocument, output_dir: str | Path | None = None) -> TailoredResumeArtifact:
        """Export a pre-generated tailored resume document to DOCX and PDF."""

        destination_dir = Path(output_dir) if output_dir else self.config.output_dir
        destination_dir.mkdir(parents=True, exist_ok=True)
        stem = self._slugify(f"{document.candidate_name or 'candidate'}-{document.source_job_title or 'target'}")
        docx_path = self.tailor.export_docx(document, destination_dir / f"{stem}.docx")
        pdf_path = self.tailor.export_pdf(document, destination_dir / f"{stem}.pdf")
        return TailoredResumeArtifact(document=document, docx_path=docx_path, pdf_path=pdf_path)

    def tailor_multiple(
        self,
        resume_input: str | Mapping[str, Any],
        jobs: Sequence[str | Mapping[str, Any]],
        *,
        output_dir: str | Path | None = None,
    ) -> list[TailoredResumeSummary]:
        """Generate tailored resumes for multiple jobs."""

        summaries: list[TailoredResumeSummary] = []
        for job_input in jobs:
            summaries.append(self.tailor_resume(resume_input, job_input, output_dir=output_dir))
        return summaries

    def _slugify(self, value: str) -> str:
        slug = value.lower()
        slug = slug.replace("/", "-")
        slug = "-".join(part for part in slug.split() if part)
        slug = "".join(character if character.isalnum() or character == "-" else "-" for character in slug)
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-") or "tailored-resume"