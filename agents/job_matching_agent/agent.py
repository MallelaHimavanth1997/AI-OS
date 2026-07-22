"""Orchestration layer for the Job Matching Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from backend.logging import get_logger

from agents.job_search_agent import JobDescriptionParser, ParsedJob
from agents.resume_intelligence_agent import ParsedResume, ResumeParser

from .config import JobMatchingConfig, get_job_matching_config
from .matcher import MatchBreakdown, JobMatcher


@dataclass(slots=True)
class JobMatchAnalysis:
    """Combined result for a single ranked job."""

    job: ParsedJob
    match: MatchBreakdown
    priority_bucket: str


@dataclass(slots=True)
class MatchReport:
    """Ranked matching report for one resume against multiple jobs."""

    candidate_name: str
    total_jobs: int
    matched_jobs: list[JobMatchAnalysis] = field(default_factory=list)


class JobMatchingAgent:
    """Match resumes against jobs and produce ranked recommendations."""

    def __init__(
        self,
        *,
        config: JobMatchingConfig | None = None,
        matcher: JobMatcher | None = None,
        resume_parser: ResumeParser | None = None,
        job_parser: JobDescriptionParser | None = None,
    ) -> None:
        self.config = config or get_job_matching_config()
        self.matcher = matcher or JobMatcher(
            required_skill_weight=self.config.required_skill_weight,
            keyword_weight=self.config.keyword_weight,
            experience_weight=self.config.experience_weight,
        )
        self.resume_parser = resume_parser or ResumeParser()
        self.job_parser = job_parser or JobDescriptionParser()
        self.logger = get_logger(bind={"component": "job_matching_agent"})

    def match_resume_to_jobs(
        self,
        resume_input: str | Mapping[str, Any],
        jobs: Sequence[str | Mapping[str, Any]],
    ) -> MatchReport:
        """Parse a resume and rank a set of jobs against it."""

        resume = self.resume_parser.parse(resume_input)
        parsed_jobs = [self.job_parser.parse(job) for job in jobs]
        ranked = self.matcher.rank(resume, parsed_jobs)

        analyses = [self._build_analysis(job, match) for job, match in ranked[: self.config.max_recommendations]]
        report = MatchReport(
            candidate_name=resume.full_name,
            total_jobs=len(parsed_jobs),
            matched_jobs=analyses,
        )

        self.logger.info(
            "Jobs ranked against resume",
            candidate=resume.full_name,
            jobs=len(parsed_jobs),
            top_score=analyses[0].match.match_score if analyses else 0,
        )
        return report

    def match_parsed_resume_to_jobs(self, resume: ParsedResume, jobs: Sequence[ParsedJob]) -> MatchReport:
        """Rank already parsed jobs without reparsing resume input."""

        ranked = self.matcher.rank(resume, jobs)
        analyses = [self._build_analysis(job, match) for job, match in ranked[: self.config.max_recommendations]]
        return MatchReport(candidate_name=resume.full_name, total_jobs=len(jobs), matched_jobs=analyses)

    def compare_single_job(self, resume_input: str | Mapping[str, Any], job_input: str | Mapping[str, Any]) -> JobMatchAnalysis:
        """Compare one resume against one job and return a structured analysis."""

        resume = self.resume_parser.parse(resume_input)
        job = self.job_parser.parse(job_input)
        match = self.matcher.match(resume, job)
        return self._build_analysis(job, match)

    def compare_parsed_resume_and_job(self, resume: ParsedResume, job: ParsedJob) -> JobMatchAnalysis:
        """Compare already parsed resume and job objects without reparsing them."""

        match = self.matcher.match(resume, job)
        return self._build_analysis(job, match)

    def filter_opportunities(self, report: MatchReport, *, minimum_score: float | None = None) -> list[JobMatchAnalysis]:
        """Filter the ranked opportunities using configured score thresholds."""

        threshold = minimum_score if minimum_score is not None else self.config.minimum_match_score
        return [item for item in report.matched_jobs if item.match.match_score >= threshold]

    def _build_analysis(self, job: ParsedJob, match: MatchBreakdown) -> JobMatchAnalysis:
        if match.match_score >= 85:
            bucket = "high"
        elif match.match_score >= 70:
            bucket = "medium"
        else:
            bucket = "low"
        return JobMatchAnalysis(job=job, match=match, priority_bucket=bucket)