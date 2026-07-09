"""Orchestration layer for the Job Search Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .config import JobSearchConfig
from .database import JobDatabase, JobMatchRecord, JobRecord
from .matcher import MatchResult, SkillMatcher
from .parser import JobDescriptionParser, ParsedJob


class JobSearchProvider(Protocol):
    """Provider interface for fetching jobs from an external source."""

    def search_jobs(
        self,
        query: str,
        *,
        location: str | None = None,
        remote_only: bool | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        """Return raw job payloads for a query."""


class OpenAIJobEnhancer(Protocol):
    """Optional abstraction for future OpenAI-based enrichment."""

    def enhance_job_text(self, job: ParsedJob) -> ParsedJob:
        """Return an enriched or rewritten job object."""


@dataclass(slots=True)
class JobAnalysis:
    """Combined output of parsing, matching, and persistence."""

    job: JobRecord
    match: MatchResult | None = None
    match_record: JobMatchRecord | None = None
    parsed_job: ParsedJob | None = None


@dataclass(slots=True)
class SearchSummary:
    """A ranked set of job analyses for a given search."""

    query: str
    user_skills: list[str]
    results: list[JobAnalysis] = field(default_factory=list)


class JobSearchAgent:
    """Search, parse, score, and store jobs for later workflows.

    The class is designed to stay provider-agnostic. External job boards, ATS
    feeds, or a future OpenAI workflow can plug into the same orchestration
    path without changing the persistence or scoring code.
    """

    def __init__(
        self,
        *,
        config: JobSearchConfig | None = None,
        database: JobDatabase | None = None,
        parser: JobDescriptionParser | None = None,
        matcher: SkillMatcher | None = None,
        provider: JobSearchProvider | None = None,
        openai_enhancer: OpenAIJobEnhancer | None = None,
    ) -> None:
        self.config = config or JobSearchConfig.from_env()
        self.database = database or JobDatabase(self.config.database_path)
        self.parser = parser or JobDescriptionParser()
        self.matcher = matcher or SkillMatcher()
        self.provider = provider
        self.openai_enhancer = openai_enhancer if self.config.enable_openai_integration else None

    def search_jobs(
        self,
        query: str,
        *,
        location: str | None = None,
        remote_only: bool | None = None,
        user_skills: Sequence[str] | None = None,
    ) -> SearchSummary:
        """Fetch jobs from a provider, score them, and persist the results."""

        if self.provider is None:
            raise RuntimeError(
                "No job search provider is configured. Inject a provider that implements search_jobs()."
            )

        user_skills = list(user_skills or [])
        raw_jobs = self.provider.search_jobs(query, location=location, remote_only=remote_only)
        analyses: list[JobAnalysis] = []

        for raw_job in raw_jobs:
            analysis = self.ingest_job(raw_job, user_skills=user_skills)
            analyses.append(analysis)

        analyses.sort(key=self._analysis_sort_key, reverse=True)
        return SearchSummary(query=query, user_skills=user_skills, results=analyses[: self.config.max_results])

    def ingest_job(
        self,
        job_data: str | Mapping[str, Any],
        *,
        user_skills: Sequence[str] | None = None,
        source_name: str | None = None,
    ) -> JobAnalysis:
        """Parse, match, and persist one job payload."""

        parsed_job = self.parser.parse(job_data)
        if self.openai_enhancer is not None:
            parsed_job = self.openai_enhancer.enhance_job_text(parsed_job)

        effective_source_name = source_name or parsed_job.metadata.get("source_name") or self.config.source_name
        job_id = self.database.upsert_job(parsed_job, source_name=str(effective_source_name))

        match_result: MatchResult | None = None
        match_record: JobMatchRecord | None = None
        normalized_skills = list(user_skills or [])
        if normalized_skills:
            match_result = self.matcher.score(parsed_job, normalized_skills)
            self.database.save_match(job_id, match_result)
            match_records = self.database.list_job_matches(job_id=job_id, limit=1)
            match_record = match_records[0] if match_records else None

        job_record = self.database.get_job(job_id)
        if job_record is None:
            raise RuntimeError(f"Job {job_id} was saved but could not be reloaded from the database.")

        return JobAnalysis(
            job=job_record,
            match=match_result,
            match_record=match_record,
            parsed_job=parsed_job,
        )

    def rank_jobs(
        self,
        jobs: Sequence[str | Mapping[str, Any]],
        *,
        user_skills: Sequence[str],
        source_name: str | None = None,
    ) -> list[JobAnalysis]:
        """Rank pre-fetched jobs without performing an external search."""

        analyses = [self.ingest_job(job, user_skills=user_skills, source_name=source_name) for job in jobs]
        analyses.sort(key=self._analysis_sort_key, reverse=True)
        return analyses

    def _analysis_sort_key(self, analysis: JobAnalysis) -> float:
        if analysis.match is None:
            return 0.0
        return analysis.match.match_percentage