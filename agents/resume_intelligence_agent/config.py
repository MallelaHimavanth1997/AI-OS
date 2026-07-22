"""Configuration for the Resume Intelligence Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class ResumeIntelligenceConfig:
    """Runtime settings for resume parsing, embeddings, and ATS generation."""

    vector_collection_name: str = field(default_factory=lambda: os.getenv("RESUME_VECTOR_COLLECTION", "resume_embeddings"))
    vector_dimensions: int = field(default_factory=lambda: int(os.getenv("RESUME_VECTOR_DIMENSIONS", "256")))
    qdrant_url: str | None = field(default_factory=lambda: os.getenv("QDRANT_URL"))
    qdrant_api_key: str | None = field(default_factory=lambda: os.getenv("QDRANT_API_KEY"))
    qdrant_local_path: str | None = field(default_factory=lambda: os.getenv("QDRANT_LOCAL_PATH"))
    use_local_qdrant: bool = field(default_factory=lambda: os.getenv("RESUME_QDRANT_LOCAL", "true").lower() in {"1", "true", "yes", "on"})
    max_keywords: int = field(default_factory=lambda: int(os.getenv("RESUME_MAX_KEYWORDS", "30")))
    max_skills: int = field(default_factory=lambda: int(os.getenv("RESUME_MAX_SKILLS", "40")))
    max_projects: int = field(default_factory=lambda: int(os.getenv("RESUME_MAX_PROJECTS", "8")))
    max_experience: int = field(default_factory=lambda: int(os.getenv("RESUME_MAX_EXPERIENCE", "8")))
    storage_dir: Path = field(default_factory=lambda: Path(os.getenv("RESUME_STORAGE_DIR", "resumes/processed")).expanduser())
    enable_llm_enrichment: bool = field(default_factory=lambda: os.getenv("RESUME_ENABLE_LLM_ENRICHMENT", "false").lower() in {"1", "true", "yes", "on"})
    llm_model_name: str = field(default_factory=lambda: os.getenv("RESUME_LLM_MODEL", "qwen3"))

    def ensure_directories(self) -> None:
        """Create local runtime directories used by the agent."""

        self.storage_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_resume_config() -> ResumeIntelligenceConfig:
    """Return cached resume agent configuration."""

    config = ResumeIntelligenceConfig()
    config.ensure_directories()
    return config