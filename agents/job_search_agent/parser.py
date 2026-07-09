"""Parse job descriptions into structured records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
import re


_SECTION_HEADERS = {
    "requirements": ("requirements", "qualifications", "what you bring", "must have"),
    "responsibilities": (
        "responsibilities",
        "what you will do",
        "duties",
        "role overview",
        "day to day",
    ),
    "benefits": ("benefits", "perks", "what we offer"),
}


@dataclass(slots=True)
class ParsedJob:
    """Structured representation of a job posting."""

    title: str
    company: str
    location: str
    description: str
    requirements: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    source_url: str | None = None
    source_job_id: str | None = None
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class JobDescriptionParser:
    """Normalize job descriptions from text or provider payloads.

    The parser is intentionally tolerant of incomplete data because external
    job feeds often vary in shape. It extracts what it can and preserves the
    original payload in metadata for traceability.
    """

    def parse(self, job_data: str | Mapping[str, Any]) -> ParsedJob:
        """Parse a raw job payload into a structured record."""

        if isinstance(job_data, str):
            payload: dict[str, Any] = {"description": job_data}
        else:
            payload = dict(job_data)

        title = self._normalize_text(
            payload.get("title") or payload.get("job_title") or self._infer_title(payload)
        )
        company = self._normalize_text(payload.get("company") or payload.get("employer") or "Unknown Company")
        location = self._normalize_text(payload.get("location") or payload.get("job_location") or "Remote/Unspecified")
        description = self._normalize_text(
            payload.get("description")
            or payload.get("job_description")
            or payload.get("summary")
            or ""
        )
        raw_text = self._extract_raw_text(payload)

        sections = self._extract_sections(raw_text or description)
        requirements = self._merge_items(
            self._extract_list(payload.get("requirements")),
            sections.get("requirements", []),
        )
        responsibilities = self._merge_items(
            self._extract_list(payload.get("responsibilities")),
            sections.get("responsibilities", []),
        )
        keywords = self._merge_items(
            self._extract_list(payload.get("keywords")),
            self._keywords_from_text(" ".join([title, company, location, description, raw_text])),
        )

        return ParsedJob(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            responsibilities=responsibilities,
            keywords=keywords,
            source_url=self._normalize_text(payload.get("source_url") or payload.get("url") or "") or None,
            source_job_id=self._normalize_text(payload.get("source_job_id") or payload.get("id") or "") or None,
            raw_text=raw_text or description,
            metadata=payload,
        )

    def _extract_raw_text(self, payload: Mapping[str, Any]) -> str:
        candidate_fields = (
            "raw_text",
            "full_text",
            "description_text",
            "description",
            "job_description",
        )
        for field_name in candidate_fields:
            value = payload.get(field_name)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return ""

    def _infer_title(self, payload: Mapping[str, Any]) -> str:
        text = self._extract_raw_text(payload)
        if not text:
            return "Untitled Role"

        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if len(first_line) <= 120:
            return first_line
        return "Untitled Role"

    def _extract_sections(self, text: str) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {"requirements": [], "responsibilities": [], "benefits": []}
        if not text:
            return sections

        current_section: str | None = None
        buffer: list[str] = []

        def flush_buffer() -> None:
            nonlocal buffer, current_section
            if current_section and buffer:
                sections[current_section].extend(buffer)
            buffer = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            matched_section = self._match_section_header(line)
            if matched_section:
                flush_buffer()
                current_section = matched_section
                continue

            bullet = self._clean_bullet(line)
            if bullet:
                buffer.append(bullet)
                continue

            if current_section:
                buffer.append(line)

        flush_buffer()
        return sections

    def _match_section_header(self, line: str) -> str | None:
        normalized = line.lower().rstrip(":")
        for section_name, aliases in _SECTION_HEADERS.items():
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return section_name
        return None

    def _clean_bullet(self, line: str) -> str | None:
        if re.match(r"^[-*•]\s+", line):
            return re.sub(r"^[-*•]\s+", "", line).strip()
        if re.match(r"^\d+[.)]\s+", line):
            return re.sub(r"^\d+[.)]\s+", "", line).strip()
        return None

    def _extract_list(self, value: Any) -> list[str]:
        if isinstance(value, str):
            pieces = [piece.strip() for piece in re.split(r"[,;/\n]", value) if piece.strip()]
            return pieces

        if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            return [self._normalize_text(str(item)) for item in value if str(item).strip()]

        return []

    def _keywords_from_text(self, text: str) -> list[str]:
        if not text:
            return []

        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", text.lower())
        stop_words = {
            "with",
            "from",
            "that",
            "this",
            "your",
            "they",
            "will",
            "have",
            "into",
            "for",
            "and",
            "the",
            "our",
            "you",
            "are",
            "role",
            "job",
            "team",
            "work",
            "experience",
            "skills",
            "ability",
            "using",
            "across",
        }
        unique_tokens = []
        seen: set[str] = set()
        for token in tokens:
            if token in stop_words or token in seen:
                continue
            seen.add(token)
            unique_tokens.append(token)
        return unique_tokens[:30]

    def _merge_items(self, *item_lists: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for items in item_lists:
            for item in items:
                normalized = self._normalize_text(item)
                if not normalized:
                    continue
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append(normalized)
        return merged

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        return re.sub(r"\s+", " ", text)