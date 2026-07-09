"""Job Search Agent package."""

from .agent import JobAnalysis, JobSearchAgent, JobSearchProvider
from .config import JobSearchConfig
from .database import JobDatabase, JobRecord, JobMatchRecord
from .matcher import MatchResult, SkillMatcher
from .parser import ParsedJob, JobDescriptionParser

__all__ = [
    "JobAnalysis",
    "JobDatabase",
    "JobDescriptionParser",
    "JobMatchRecord",
    "JobRecord",
    "JobSearchAgent",
    "JobSearchConfig",
    "JobSearchProvider",
    "MatchResult",
    "ParsedJob",
    "SkillMatcher",
]