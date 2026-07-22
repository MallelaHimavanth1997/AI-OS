"""Configuration for the Job Matching Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class JobMatchingConfig:
    """Runtime configuration for scoring and ranking jobs."""

    minimum_match_score: float = field(default_factory=lambda: float(os.getenv("JOB_MATCH_MIN_SCORE", "65")))
    minimum_priority_score: float = field(default_factory=lambda: float(os.getenv("JOB_MATCH_MIN_PRIORITY", "55")))
    required_skill_weight: float = field(default_factory=lambda: float(os.getenv("JOB_MATCH_REQUIRED_SKILL_WEIGHT", "0.55")))
    keyword_weight: float = field(default_factory=lambda: float(os.getenv("JOB_MATCH_KEYWORD_WEIGHT", "0.25")))
    experience_weight: float = field(default_factory=lambda: float(os.getenv("JOB_MATCH_EXPERIENCE_WEIGHT", "0.20")))
    max_recommendations: int = field(default_factory=lambda: int(os.getenv("JOB_MATCH_MAX_RECOMMENDATIONS", "10")))


@lru_cache(maxsize=1)
def get_job_matching_config() -> JobMatchingConfig:
    """Return cached configuration for dependency injection."""

    return JobMatchingConfig()