"""Configuration for the Job Search Agent.

The configuration is intentionally environment-driven so the agent can run in
local development, CI, or a future production deployment without code changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


def _default_database_path() -> Path:
    configured_path = os.getenv("AI_OS_JOB_SEARCH_DB")
    if configured_path:
        return Path(configured_path).expanduser()

    return Path.home() / ".ai_os" / "job_search.sqlite3"


@dataclass(slots=True)
class JobSearchConfig:
    """Runtime settings for job discovery, scoring, and storage."""

    database_path: Path = field(default_factory=_default_database_path)
    max_results: int = 10
    minimum_match_percentage: float = 60.0
    openai_model: str = "gpt-4.1-mini"
    enable_openai_integration: bool = False
    source_name: str = "manual"

    @classmethod
    def from_env(cls) -> "JobSearchConfig":
        """Build a configuration object from environment variables."""

        max_results = int(os.getenv("AI_OS_JOB_SEARCH_MAX_RESULTS", "10"))
        minimum_match_percentage = float(
            os.getenv("AI_OS_JOB_SEARCH_MIN_MATCH", "60")
        )
        enable_openai_integration = os.getenv("AI_OS_ENABLE_OPENAI", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        return cls(
            database_path=_default_database_path(),
            max_results=max_results,
            minimum_match_percentage=minimum_match_percentage,
            openai_model=os.getenv("AI_OS_OPENAI_MODEL", "gpt-4.1-mini"),
            enable_openai_integration=enable_openai_integration,
            source_name=os.getenv("AI_OS_JOB_SOURCE_NAME", "manual"),
        )