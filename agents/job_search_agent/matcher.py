"""Score job postings against user skill profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence
import re

from .parser import ParsedJob


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+#. ]+", " ", value.lower())).strip()


@dataclass(slots=True)
class MatchResult:
    """Result of matching a user profile to a job posting."""

    match_percentage: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)


class SkillMatcher:
    """Compute a transparent match score between a user profile and a job."""

    def score(self, parsed_job: ParsedJob, user_skills: Sequence[str]) -> MatchResult:
        """Return a percentage score and supporting evidence for the match."""

        normalized_skills = [self._normalize_skill(skill) for skill in user_skills if self._normalize_skill(skill)]
        unique_user_skills = list(dict.fromkeys(normalized_skills))

        job_text = self._job_text(parsed_job)
        matched_skills = [skill for skill in unique_user_skills if self._skill_present(skill, job_text)]
        missing_skills = [skill for skill in unique_user_skills if skill not in matched_skills]

        matched_requirements = [
            requirement
            for requirement in parsed_job.requirements
            if self._skill_present(self._normalize_skill(requirement), " ".join(unique_user_skills))
            or self._skill_present(self._normalize_skill(requirement), job_text)
        ]
        matched_keywords = [keyword for keyword in parsed_job.keywords if self._skill_present(keyword, job_text)]

        skill_score = self._ratio(len(matched_skills), len(unique_user_skills))
        requirement_score = self._ratio(len(matched_requirements), len(parsed_job.requirements))
        keyword_score = self._ratio(len(matched_keywords), len(parsed_job.keywords))

        weighted_score = (skill_score * 0.6) + (requirement_score * 0.25) + (keyword_score * 0.15)
        match_percentage = round(min(weighted_score * 100.0, 100.0), 2)

        return MatchResult(
            match_percentage=match_percentage,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            score_breakdown={
                "skill_score": round(skill_score * 100.0, 2),
                "requirement_score": round(requirement_score * 100.0, 2),
                "keyword_score": round(keyword_score * 100.0, 2),
            },
        )

    def _job_text(self, parsed_job: ParsedJob) -> str:
        components = [
            parsed_job.title,
            parsed_job.company,
            parsed_job.location,
            parsed_job.description,
            " ".join(parsed_job.requirements),
            " ".join(parsed_job.responsibilities),
            " ".join(parsed_job.keywords),
            parsed_job.raw_text,
        ]
        return _normalize(" ".join(component for component in components if component))

    def _skill_present(self, skill: str, text: str) -> bool:
        if not skill or not text:
            return False
        normalized_skill = self._normalize_skill(skill)
        if not normalized_skill:
            return False
        return normalized_skill in text

    def _normalize_skill(self, value: str) -> str:
        return _normalize(value)

    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator