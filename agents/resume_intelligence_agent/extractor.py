"""Resume text extraction helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


_SECTION_ALIASES = {
    "summary": ("summary", "professional summary", "profile", "about me"),
    "skills": ("skills", "technical skills", "core skills", "competencies", "expertise"),
    "experience": ("experience", "work experience", "professional experience", "employment history", "career history"),
    "projects": ("projects", "project experience", "selected projects", "key projects"),
    "certifications": ("certifications", "certificates", "licenses", "credentials"),
    "education": ("education", "academic background", "qualifications"),
}

_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "have",
    "has",
    "will",
    "your",
    "you",
    "our",
    "are",
    "was",
    "were",
    "been",
    "into",
    "over",
    "more",
    "than",
    "less",
    "using",
    "used",
    "built",
    "managed",
    "lead",
    "led",
    "work",
    "team",
    "teams",
    "role",
    "roles",
    "responsible",
    "responsibilities",
    "skills",
    "experience",
    "resume",
    "cv",
    "project",
    "projects",
}


@dataclass(slots=True)
class SectionExtraction:
    """Structured section output for a resume document."""

    sections: dict[str, list[str]] = field(default_factory=dict)

    def section(self, name: str) -> list[str]:
        return self.sections.get(name, [])


class ResumeExtractor:
    """Extract structured information from resume text."""

    def extract_sections(self, text: str) -> SectionExtraction:
        sections: dict[str, list[str]] = {name: [] for name in _SECTION_ALIASES}
        current_section: str | None = None
        buffer: list[str] = []

        def flush() -> None:
            nonlocal buffer, current_section
            if current_section and buffer:
                sections[current_section].extend(buffer)
            buffer = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            matched_section = self._match_section(line)
            if matched_section:
                flush()
                current_section = matched_section
                continue

            bullet = self._clean_bullet(line)
            if bullet:
                buffer.append(bullet)
                continue

            if current_section:
                buffer.append(line)

        flush()
        return SectionExtraction(sections=sections)

    def extract_name(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        metadata = metadata or {}
        explicit_name = str(metadata.get("full_name") or metadata.get("name") or "").strip()
        if explicit_name:
            return explicit_name

        for line in text.splitlines():
            candidate = line.strip()
            if candidate and len(candidate.split()) <= 5 and not self._match_section(candidate):
                if re.match(r"^[A-Z][A-Za-z'\-\.]+(?:\s+[A-Z][A-Za-z'\-\.]+){1,4}$", candidate):
                    return candidate
        return "Unnamed Candidate"

    def extract_headline(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            return ""
        first = lines[0]
        second = lines[1]
        if self._match_section(first):
            return second
        if len(first.split()) <= 5 and len(second.split()) <= 12:
            return second
        return first

    def extract_skills(self, text: str, sections: SectionExtraction | None = None) -> list[str]:
        candidates: list[str] = []
        if sections:
            for line in sections.section("skills"):
                candidates.extend(self._split_list_line(line))
        for token in self._keyword_candidates(text):
            if token not in candidates:
                candidates.append(token)
        return self._dedupe(candidates)

    def extract_projects(self, text: str, sections: SectionExtraction | None = None) -> list[str]:
        project_lines = list(sections.section("projects") if sections else [])
        if project_lines:
            return self._dedupe(project_lines)

        fallback = [line.strip() for line in text.splitlines() if self._looks_like_project(line)]
        return self._dedupe(fallback)

    def extract_experience(self, text: str, sections: SectionExtraction | None = None) -> list[str]:
        return self._dedupe(self._section_or_fallback("experience", text, sections, minimum_length=20))

    def extract_certifications(self, text: str, sections: SectionExtraction | None = None) -> list[str]:
        return self._dedupe(self._section_or_fallback("certifications", text, sections, minimum_length=8))

    def extract_education(self, text: str, sections: SectionExtraction | None = None) -> list[str]:
        return self._dedupe(self._section_or_fallback("education", text, sections, minimum_length=8))

    def extract_keywords(self, text: str, *, max_keywords: int = 30) -> list[str]:
        keyword_counts: dict[str, int] = {}
        for token in self._keyword_candidates(text):
            keyword_counts[token] = keyword_counts.get(token, 0) + 1

        ranked = sorted(keyword_counts.items(), key=lambda item: (-item[1], item[0]))
        return [keyword for keyword, _ in ranked[:max_keywords]]

    def extract_summary(self, text: str, sections: SectionExtraction | None = None) -> str:
        summary_candidates = sections.section("summary") if sections else []
        if summary_candidates:
            return " ".join(summary_candidates).strip()

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines[:2]).strip() if lines else ""

    def _match_section(self, line: str) -> str | None:
        normalized = line.lower().rstrip(":")
        for name, aliases in _SECTION_ALIASES.items():
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return name
        return None

    def _clean_bullet(self, line: str) -> str | None:
        if re.match(r"^[-*•]\s+", line):
            return re.sub(r"^[-*•]\s+", "", line).strip()
        if re.match(r"^\d+[.)]\s+", line):
            return re.sub(r"^\d+[.)]\s+", "", line).strip()
        return None

    def _looks_like_project(self, line: str) -> bool:
        candidate = line.strip().lower()
        return bool(candidate) and ("project" in candidate or "built" in candidate or "developed" in candidate or "led" in candidate)

    def _section_or_fallback(
        self,
        section_name: str,
        text: str,
        sections: SectionExtraction | None,
        *,
        minimum_length: int,
    ) -> list[str]:
        if sections:
            section_items = [item for item in sections.section(section_name) if len(item.strip()) >= minimum_length]
            if section_items:
                return section_items
        fallback = [line.strip() for line in text.splitlines() if len(line.strip()) >= minimum_length and self._contains_section_hint(line, section_name)]
        return fallback

    def _contains_section_hint(self, line: str, section_name: str) -> bool:
        lowered = line.lower()
        if section_name == "experience":
            return any(keyword in lowered for keyword in ("engineer", "developer", "manager", "analyst", "consultant", "architect", "lead"))
        if section_name == "certifications":
            return any(keyword in lowered for keyword in ("certified", "certificate", "aws", "azure", "gcp", "pmp", "scrum"))
        if section_name == "education":
            return any(keyword in lowered for keyword in ("bachelor", "master", "phd", "university", "college", "degree"))
        return False

    def _keyword_candidates(self, text: str) -> list[str]:
        raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#\.-]{1,}", text.lower())
        candidates = [token for token in raw_tokens if token not in _STOP_WORDS and len(token) > 1]
        return self._dedupe(candidates)

    def _dedupe(self, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = self._normalize(value)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(value.strip())
        return result

    def _split_list_line(self, line: str) -> list[str]:
        pieces = [piece.strip() for piece in re.split(r"[,;/|]\s*", line) if piece.strip()]
        if len(pieces) > 1:
            return pieces
        cleaned = line.strip()
        return [cleaned] if cleaned else []

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())