"""ATS-optimized resume generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .parser import ParsedResume


@dataclass(slots=True)
class ATSResumeDocument:
    """ATS-friendly resume output with traceable scoring."""

    text: str
    ats_score: float
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class ATSResumeBuilder:
    """Create ATS-friendly resume text without inventing new experience."""

    def build(self, resume: ParsedResume, *, target_text: str | None = None, target_keywords: list[str] | None = None) -> ATSResumeDocument:
        target_keywords = self._normalize_keywords(target_keywords or self._keywords_from_text(target_text or ""))
        resume_keywords = self._normalize_keywords(resume.keywords + resume.skills + resume.projects + resume.experience + resume.certifications + resume.education)

        matched_keywords = [keyword for keyword in target_keywords if keyword in resume_keywords or self._contains_keyword(resume.raw_text, keyword)]
        missing_keywords = [keyword for keyword in target_keywords if keyword not in matched_keywords]
        ats_score = self._score(len(matched_keywords), len(target_keywords))
        text = self._render_resume(resume, target_keywords)
        suggestions = self._build_suggestions(missing_keywords, resume)

        return ATSResumeDocument(
            text=text,
            ats_score=ats_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            suggestions=suggestions,
        )

    def _render_resume(self, resume: ParsedResume, keywords: list[str]) -> str:
        sections: list[str] = []
        sections.append(resume.full_name)
        if resume.headline:
            sections.append(resume.headline)
        if resume.summary:
            sections.extend(["SUMMARY", self._emphasize_keywords(resume.summary, keywords)])
        if resume.skills:
            sections.extend(["SKILLS", self._format_list(resume.skills, keywords)])
        if resume.experience:
            sections.extend(["EXPERIENCE", self._format_list(resume.experience, keywords)])
        if resume.projects:
            sections.extend(["PROJECTS", self._format_list(resume.projects, keywords)])
        if resume.certifications:
            sections.extend(["CERTIFICATIONS", self._format_list(resume.certifications, keywords)])
        if resume.education:
            sections.extend(["EDUCATION", self._format_list(resume.education, keywords)])
        return "\n".join(section for section in sections if section).strip()

    def _format_list(self, items: list[str], keywords: list[str]) -> str:
        return "\n".join(f"- {self._emphasize_keywords(item, keywords)}" for item in items)

    def _emphasize_keywords(self, text: str, keywords: list[str]) -> str:
        result = text
        for keyword in sorted(keywords, key=len, reverse=True):
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            result = pattern.sub(lambda match: match.group(0).upper(), result)
        return result

    def _build_suggestions(self, missing_keywords: list[str], resume: ParsedResume) -> list[str]:
        suggestions: list[str] = []
        if missing_keywords:
            suggestions.append(f"Consider adding these existing keywords where truthful: {', '.join(missing_keywords[:8])}.")
        if not resume.summary:
            suggestions.append("Add a concise professional summary based on the resume content.")
        if not resume.skills:
            suggestions.append("Include a dedicated skills section to improve ATS parsing.")
        return suggestions

    def _keywords_from_text(self, text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#\.-]{1,}", text.lower())
        stop_words = {"and", "the", "for", "with", "from", "that", "this", "you", "your", "our", "are", "will", "have"}
        return self._normalize_keywords([token for token in tokens if token not in stop_words])

    def _normalize_keywords(self, keywords: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for keyword in keywords:
            normalized = re.sub(r"\s+", " ", keyword.strip().lower())
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        return keyword.lower() in text.lower()

    def _score(self, matched_count: int, total_count: int) -> float:
        if total_count <= 0:
            return 0.0
        return round((matched_count / total_count) * 100.0, 2)