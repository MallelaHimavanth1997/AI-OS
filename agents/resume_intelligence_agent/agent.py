"""Orchestration for the Resume Intelligence Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from backend.logging import get_logger

from .ats import ATSResumeBuilder, ATSResumeDocument
from .config import ResumeIntelligenceConfig, get_resume_config
from .embeddings import HashingEmbeddingProvider, ResumeEmbeddingService
from .parser import ParsedResume, ResumeParser
from .vector_store import QdrantResumeVectorStore, ResumeVectorRecord, SimilarResumeResult


class ResumeEnhancer(Protocol):
    """Optional future hook for local LLM-powered resume refinement."""

    def enhance(self, resume: ParsedResume) -> ParsedResume:
        """Return a cleaned or enriched resume without inventing content."""


@dataclass(slots=True)
class ResumeAnalysis:
    """Combined result of parsing, embedding, and ATS generation."""

    resume: ParsedResume
    embedding: list[float]
    vector_record: ResumeVectorRecord | None = None
    ats_document: ATSResumeDocument | None = None
    similar_resumes: list[SimilarResumeResult] = field(default_factory=list)


class ResumeIntelligenceAgent:
    """Parse resumes, extract structured data, generate embeddings, and build ATS-ready output."""

    def __init__(
        self,
        *,
        config: ResumeIntelligenceConfig | None = None,
        parser: ResumeParser | None = None,
        embedding_service: ResumeEmbeddingService | None = None,
        vector_store: QdrantResumeVectorStore | None = None,
        ats_builder: ATSResumeBuilder | None = None,
        enhancer: ResumeEnhancer | None = None,
    ) -> None:
        self.config = config or get_resume_config()
        self.parser = parser or ResumeParser()
        self.embedding_service = embedding_service or ResumeEmbeddingService(HashingEmbeddingProvider(self.config.vector_dimensions))
        self.vector_store = vector_store or QdrantResumeVectorStore(self.config)
        self.ats_builder = ats_builder or ATSResumeBuilder()
        self.enhancer = enhancer
        self.logger = get_logger(bind={"component": "resume_intelligence_agent"})

    def ingest_resume(self, resume_input: str | Mapping[str, Any]) -> ResumeAnalysis:
        """Parse a resume, generate an embedding, and store it in the vector database."""

        resume = self.parser.parse(resume_input)
        if self.enhancer is not None and self.config.enable_llm_enrichment:
            resume = self.enhancer.enhance(resume)

        embedding = self.embedding_service.embed_resume(resume)
        vector_record = self.vector_store.upsert_resume(resume, embedding)
        similar_resumes = self.vector_store.search_similar(embedding, limit=5)

        self.logger.info(
            "Resume ingested",
            candidate=resume.full_name,
            skills=len(resume.skills),
            projects=len(resume.projects),
            experience=len(resume.experience),
        )

        return ResumeAnalysis(
            resume=resume,
            embedding=embedding,
            vector_record=vector_record,
            similar_resumes=similar_resumes,
        )

    def generate_ats_resume(self, resume_input: str | Mapping[str, Any], *, target_text: str | None = None, target_keywords: Sequence[str] | None = None) -> ATSResumeDocument:
        """Generate an ATS-optimized resume from the provided source content."""

        analysis = self.ingest_resume(resume_input)
        ats_document = self.ats_builder.build(
            analysis.resume,
            target_text=target_text,
            target_keywords=list(target_keywords or []),
        )
        analysis.ats_document = ats_document
        return ats_document

    def compare_against_target(self, resume_input: str | Mapping[str, Any], target_text: str) -> ATSResumeDocument:
        """Generate an ATS analysis against a target role or job description."""

        return self.generate_ats_resume(resume_input, target_text=target_text)

    def find_similar_resumes(self, resume_input: str | Mapping[str, Any], *, limit: int = 5) -> list[SimilarResumeResult]:
        """Search the vector store for similar resume embeddings."""

        resume = self.parser.parse(resume_input)
        embedding = self.embedding_service.embed_resume(resume)
        return self.vector_store.search_similar(embedding, limit=limit)