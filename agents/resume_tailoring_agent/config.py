"""Configuration for the Resume Tailoring Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class ResumeTailoringConfig:
    """Runtime settings for tailoring and exporting resumes."""

    output_dir: Path = field(default_factory=lambda: Path(os.getenv("RESUME_TAILOR_OUTPUT_DIR", "resumes/tailored")).expanduser())
    max_summary_keywords: int = field(default_factory=lambda: int(os.getenv("RESUME_TAILOR_MAX_SUMMARY_KEYWORDS", "5")))
    max_skill_bullets: int = field(default_factory=lambda: int(os.getenv("RESUME_TAILOR_MAX_SKILL_BULLETS", "12")))
    max_experience_bullets: int = field(default_factory=lambda: int(os.getenv("RESUME_TAILOR_MAX_EXPERIENCE_BULLETS", "10")))
    max_project_bullets: int = field(default_factory=lambda: int(os.getenv("RESUME_TAILOR_MAX_PROJECT_BULLETS", "8")))
    min_ats_score: float = field(default_factory=lambda: float(os.getenv("RESUME_TAILOR_MIN_ATS_SCORE", "65")))
    author_name: str = field(default_factory=lambda: os.getenv("RESUME_AUTHOR_NAME", "AI-OS"))

    def ensure_directories(self) -> None:
        """Create local output directories used by the agent."""

        self.output_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_resume_tailoring_config() -> ResumeTailoringConfig:
    """Return cached tailoring configuration."""

    config = ResumeTailoringConfig()
    config.ensure_directories()
    return config