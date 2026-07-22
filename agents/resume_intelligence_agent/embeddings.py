"""Embedding services for resume intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import re
from typing import Protocol, Sequence

from .parser import ParsedResume


class EmbeddingProvider(Protocol):
    """Provider interface for embedding text into a vector space."""

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding for the supplied text."""


@dataclass(slots=True)
class HashingEmbeddingProvider:
    """Deterministic local embedding provider that needs no external model."""

    dimensions: int = 256

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[A-Za-z0-9+#\.-]{2,}", text.lower())
        if not tokens:
            return vector

        for token in tokens:
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            weight = 1.0 + (digest[4] / 255.0)
            vector[index] += weight

        return self._normalize(vector)

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 8) for value in vector]


@dataclass(slots=True)
class ResumeEmbeddingService:
    """Create embeddings from structured resume content."""

    provider: EmbeddingProvider

    def embed_resume(self, resume: ParsedResume) -> list[float]:
        return self.provider.embed_text(self.build_embedding_text(resume))

    def build_embedding_text(self, resume: ParsedResume) -> str:
        parts: list[str] = [
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
        return "\n".join(part for part in parts if part).strip()

    def embed_many(self, resumes: Sequence[ParsedResume]) -> list[list[float]]:
        return [self.embed_resume(resume) for resume in resumes]