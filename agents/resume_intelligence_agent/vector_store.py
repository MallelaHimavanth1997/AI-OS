"""Qdrant-backed vector storage for resume embeddings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import import_module
from typing import Any
from uuid import uuid4

from .config import ResumeIntelligenceConfig
from .parser import ParsedResume

QdrantClient = Any


@dataclass(slots=True)
class ResumeVectorRecord:
    """Stored resume vector payload."""

    id: str
    score: float | None = None
    resume: ParsedResume | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SimilarResumeResult:
    """Similarity search result for a resume embedding."""

    record: ResumeVectorRecord
    similarity: float


class QdrantResumeVectorStore:
    """Persist and search resume embeddings in Qdrant."""

    def __init__(self, config: ResumeIntelligenceConfig, client: QdrantClient | None = None) -> None:
        self.config = config
        self.models = import_module("qdrant_client.http.models")
        self.client = client or self._create_client()
        self._ensure_collection()

    def upsert_resume(self, resume: ParsedResume, embedding: list[float], *, metadata: dict[str, Any] | None = None) -> ResumeVectorRecord:
        point_id = str(uuid4())
        payload = self._build_payload(resume, metadata)
        self.client.upsert(
            collection_name=self.config.vector_collection_name,
            points=[self.models.PointStruct(id=point_id, vector=embedding, payload=payload)],
        )
        return ResumeVectorRecord(id=point_id, payload=payload, resume=resume)

    def search_similar(self, embedding: list[float], *, limit: int = 5) -> list[SimilarResumeResult]:
        hits = self.client.search(
            collection_name=self.config.vector_collection_name,
            query_vector=embedding,
            limit=limit,
            with_payload=True,
        )
        results: list[SimilarResumeResult] = []
        for hit in hits:
            payload = dict(hit.payload or {})
            results.append(
                SimilarResumeResult(
                    record=ResumeVectorRecord(id=str(hit.id), score=float(hit.score), payload=payload),
                    similarity=float(hit.score),
                )
            )
        return results

    def _create_client(self) -> QdrantClient:
        qdrant_client_module = import_module("qdrant_client")
        if self.config.use_local_qdrant:
            location = self.config.qdrant_local_path or ":memory:"
            return qdrant_client_module.QdrantClient(location=location)
        return qdrant_client_module.QdrantClient(url=self.config.qdrant_url, api_key=self.config.qdrant_api_key)

    def _ensure_collection(self) -> None:
        try:
            self.client.get_collection(self.config.vector_collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.config.vector_collection_name,
                vectors_config=self.models.VectorParams(
                    size=self.config.vector_dimensions,
                    distance=self.models.Distance.COSINE,
                ),
            )

    def _build_payload(self, resume: ParsedResume, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "full_name": resume.full_name,
            "headline": resume.headline,
            "summary": resume.summary,
            "skills": resume.skills,
            "projects": resume.projects,
            "experience": resume.experience,
            "certifications": resume.certifications,
            "education": resume.education,
            "keywords": resume.keywords,
            "source_path": resume.source_path,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            payload.update(metadata)
        return payload