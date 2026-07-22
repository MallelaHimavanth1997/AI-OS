"""Resume parsing and normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import json
import os

from .extractor import ResumeExtractor, SectionExtraction


@dataclass(slots=True)
class ParsedResume:
    """Structured representation of a resume."""

    full_name: str
    headline: str
    summary: str
    skills: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    raw_text: str = ""
    source_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, list[str]] = field(default_factory=dict)


class ResumeParser:
    """Parse resume files or raw text into a stable internal representation."""

    def __init__(self, extractor: ResumeExtractor | None = None) -> None:
        self.extractor = extractor or ResumeExtractor()

    def parse(self, resume_input: str | Path | Mapping[str, Any]) -> ParsedResume:
        raw_text, metadata, source_path = self._load_input(resume_input)
        sections = self.extractor.extract_sections(raw_text)

        full_name = self.extractor.extract_name(raw_text, metadata)
        headline = self.extractor.extract_headline(raw_text)
        summary = self.extractor.extract_summary(raw_text, sections)
        skills = self.extractor.extract_skills(raw_text, sections)
        projects = self.extractor.extract_projects(raw_text, sections)
        experience = self.extractor.extract_experience(raw_text, sections)
        certifications = self.extractor.extract_certifications(raw_text, sections)
        education = self.extractor.extract_education(raw_text, sections)
        keywords = self.extractor.extract_keywords(raw_text, max_keywords=metadata.get("max_keywords", 30))

        return ParsedResume(
            full_name=full_name,
            headline=headline,
            summary=summary,
            skills=skills,
            projects=projects,
            experience=experience,
            certifications=certifications,
            education=education,
            keywords=keywords,
            raw_text=raw_text,
            source_path=source_path,
            metadata=metadata,
            sections=sections.sections,
        )

    def _load_input(self, resume_input: str | Path | Mapping[str, Any]) -> tuple[str, dict[str, Any], str | None]:
        if isinstance(resume_input, Mapping):
            metadata = dict(resume_input)
            raw_text = str(
                metadata.get("raw_text")
                or metadata.get("text")
                or metadata.get("content")
                or metadata.get("resume_text")
                or metadata.get("description")
                or ""
            )
            source_path = str(metadata.get("source_path") or metadata.get("file_path") or "") or None
            if not raw_text and source_path:
                raw_text = self._read_file(Path(source_path))
            return self._normalize_text(raw_text), metadata, source_path

        path_candidate = Path(resume_input)
        if path_candidate.exists() and path_candidate.is_file():
            return self._normalize_text(self._read_file(path_candidate)), {"source_path": str(path_candidate)}, str(path_candidate)

        text = str(resume_input)
        return self._normalize_text(text), {"source_path": None}, None

    def _read_file(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8")
        if suffix == ".docx":
            return self._read_docx(path)
        if suffix == ".pdf":
            return self._read_pdf(path)
        raise ValueError(f"Unsupported resume file type: {suffix}")

    def _read_docx(self, path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:  # pragma: no cover - import check
            raise RuntimeError("python-docx is required to parse DOCX resumes.") from exc

        document = Document(str(path))
        lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(lines)

    def _read_pdf(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - import check
            raise RuntimeError("pypdf is required to parse PDF resumes.") from exc

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(page.strip() for page in pages if page.strip())

    def _normalize_text(self, text: str) -> str:
        return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))