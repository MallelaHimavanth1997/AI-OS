"""Similarity scoring for resumes and jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Sequence

from agents.job_search_agent import ParsedJob
from agents.resume_intelligence_agent import ParsedResume


@dataclass(slots=True)
class MatchBreakdown:
    """Detailed score components for a single job match."""

    match_score: float
    priority_score: float
    skill_score: float
    keyword_score: float
    experience_score: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    job_signals: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class JobMatcher:
    """Compute deterministic resume-to-job similarity scores."""

    def __init__(self, *, required_skill_weight: float = 0.55, keyword_weight: float = 0.25, experience_weight: float = 0.20) -> None:
        total = required_skill_weight + keyword_weight + experience_weight
        if total <= 0:
            raise ValueError("Weights must sum to a positive value.")
        self.required_skill_weight = required_skill_weight / total
        self.keyword_weight = keyword_weight / total
        self.experience_weight = experience_weight / total

    def match(self, resume: ParsedResume, job: ParsedJob) -> MatchBreakdown:
        """Compare a parsed resume with a parsed job posting."""

        resume_skills = self._normalize_list(resume.skills + resume.keywords + resume.certifications)
        resume_text = self._combined_resume_text(resume)
        job_required = self._normalize_list(job.requirements)
        job_keywords = self._normalize_list(job.keywords + self._extract_keywords(job.description) + self._extract_keywords(job.raw_text))

        matched_skills = [skill for skill in job_required if self._contains_any(resume_skills, skill) or self._contains_text(resume_text, skill)]
        missing_skills = [skill for skill in job_required if skill not in matched_skills]
        matched_keywords = [keyword for keyword in job_keywords if self._contains_any(resume_skills, keyword) or self._contains_text(resume_text, keyword)]

        skill_score = self._ratio(len(matched_skills), len(job_required))
        keyword_score = self._ratio(len(matched_keywords), len(job_keywords))
        experience_score = self._experience_alignment(resume, job)

        weighted_score = (
            skill_score * self.required_skill_weight
            + keyword_score * self.keyword_weight
            + experience_score * self.experience_weight
        )
        match_score = round(min(weighted_score * 100.0, 100.0), 2)
        priority_score = self._priority_score(match_score, job, resume)

        recommendations = self._build_recommendations(missing_skills, matched_keywords, resume, job)
        job_signals = self._build_job_signals(job)

        return MatchBreakdown(
            match_score=match_score,
            priority_score=priority_score,
            skill_score=round(skill_score * 100.0, 2),
            keyword_score=round(keyword_score * 100.0, 2),
            experience_score=round(experience_score * 100.0, 2),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_keywords=matched_keywords,
            job_signals=job_signals,
            recommendations=recommendations,
        )

    def rank(self, resume: ParsedResume, jobs: Sequence[ParsedJob]) -> list[tuple[ParsedJob, MatchBreakdown]]:
        """Rank multiple jobs from best to worst fit."""

        scored = [(job, self.match(resume, job)) for job in jobs]
        return sorted(scored, key=lambda item: (item[1].priority_score, item[1].match_score), reverse=True)

    def _priority_score(self, match_score: float, job: ParsedJob, resume: ParsedResume) -> float:
        seniority_bonus = 0.0
        if self._contains_text(job.title, "senior") or self._contains_text(job.title, "lead"):
            seniority_bonus += 5.0 if len(resume.experience) >= 3 else -5.0
        if self._contains_text(job.description, "remote"):
            seniority_bonus += 2.5
        if self._contains_text(job.description, "urgent") or self._contains_text(job.description, "immediate"):
            seniority_bonus += 2.5
        return round(max(min(match_score + seniority_bonus, 100.0), 0.0), 2)

    def _experience_alignment(self, resume: ParsedResume, job: ParsedJob) -> float:
        resume_experience_text = self._combined_resume_text(resume)
        signals = self._extract_keywords(job.description + " " + job.raw_text + " " + " ".join(job.responsibilities))
        if not signals:
            return 0.0

        matched = sum(1 for signal in signals if self._contains_text(resume_experience_text, signal))
        return self._ratio(matched, len(signals))

    def _build_recommendations(self, missing_skills: list[str], matched_keywords: list[str], resume: ParsedResume, job: ParsedJob) -> list[str]:
        recommendations: list[str] = []
        if missing_skills:
            recommendations.append(f"Add or emphasize these existing skills if truthful: {', '.join(missing_skills[:8])}.")
        if len(matched_keywords) < max(1, len(job.keywords) // 2) and job.keywords:
            recommendations.append("Align summary and bullet points with more job-specific keywords.")
        if not resume.summary:
            recommendations.append("Add a concise professional summary aligned to the target role.")
        if not resume.projects:
            recommendations.append("Include measurable project examples to improve fit for technical roles.")
        return recommendations

    def _build_job_signals(self, job: ParsedJob) -> list[str]:
        signals = [job.title, job.company, job.location]
        signals.extend(job.keywords[:10])
        return self._normalize_list(signals)

    def _extract_keywords(self, text: str) -> list[str]:
        raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#\.-]{1,}", text.lower())
        stop_words = {"and", "the", "for", "with", "from", "that", "this", "you", "your", "our", "are", "will", "have", "into", "over", "role", "job", "team", "work"}
        return self._normalize_list([token for token in raw_tokens if token not in stop_words])

    def _combined_resume_text(self, resume: ParsedResume) -> str:
        parts = [
            resume.full_name,
            resume.headline,
            resume.summary,
            " ".join(resume.skills),
            " ".join(resume.projects),
            " ".join(resume.experience),
            " ".join(resume.certifications),
            " ".join(resume.education),
            " ".join(resume.keywords),
            resume.raw_text,
        ]
        return self._normalize_text(" ".join(part for part in parts if part))

    def _normalize_list(self, values: Sequence[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = self._normalize_text(value)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _contains_any(self, haystack: Sequence[str], needle: str) -> bool:
        needle_norm = self._normalize_text(needle)
        return any(needle_norm in value or value in needle_norm for value in haystack)

    def _contains_text(self, text: str, needle: str) -> bool:
        normalized_text = self._normalize_text(text)
        normalized_needle = self._normalize_text(needle)
        return bool(normalized_text and normalized_needle and normalized_needle in normalized_text)

    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())