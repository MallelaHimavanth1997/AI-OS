"""SQLite storage for job postings and match results."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json
import sqlite3

from .matcher import MatchResult
from .parser import ParsedJob


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class JobRecord:
    """Persisted job posting."""

    id: int
    title: str
    company: str
    location: str
    description: str
    requirements: list[str]
    responsibilities: list[str]
    keywords: list[str]
    source_url: str | None
    source_job_id: str | None
    source_name: str
    created_at: str
    updated_at: str
    raw_payload: dict[str, Any]


@dataclass(slots=True)
class JobMatchRecord:
    """Persisted match analysis for a job posting."""

    id: int
    job_id: int
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    matched_keywords: list[str]
    score_breakdown: dict[str, float]
    created_at: str
    user_profile_id: str


class JobDatabase:
    """SQLite repository for job data and scoring results."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def upsert_job(self, parsed_job: ParsedJob, *, source_name: str) -> int:
        """Insert or update a job record and return its database id."""

        existing_id = self._find_existing_job_id(parsed_job)
        timestamp = _utc_now()
        payload = json.dumps(parsed_job.metadata, ensure_ascii=False, default=str)

        with self._connection() as connection:
            if existing_id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO jobs (
                        title,
                        company,
                        location,
                        description,
                        requirements,
                        responsibilities,
                        keywords,
                        source_url,
                        source_job_id,
                        source_name,
                        raw_payload,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        parsed_job.title,
                        parsed_job.company,
                        parsed_job.location,
                        parsed_job.description,
                        json.dumps(parsed_job.requirements, ensure_ascii=False, default=str),
                        json.dumps(parsed_job.responsibilities, ensure_ascii=False, default=str),
                        json.dumps(parsed_job.keywords, ensure_ascii=False, default=str),
                        parsed_job.source_url,
                        parsed_job.source_job_id,
                        source_name,
                        payload,
                        timestamp,
                        timestamp,
                    ),
                )
                connection.commit()
                return int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE jobs
                SET title = ?,
                    company = ?,
                    location = ?,
                    description = ?,
                    requirements = ?,
                    responsibilities = ?,
                    keywords = ?,
                    source_name = ?,
                    raw_payload = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    parsed_job.title,
                    parsed_job.company,
                    parsed_job.location,
                    parsed_job.description,
                    json.dumps(parsed_job.requirements, ensure_ascii=False, default=str),
                    json.dumps(parsed_job.responsibilities, ensure_ascii=False, default=str),
                    json.dumps(parsed_job.keywords, ensure_ascii=False, default=str),
                    source_name,
                    payload,
                    timestamp,
                    existing_id,
                ),
            )
            connection.commit()
            return existing_id

    def save_match(self, job_id: int, match_result: MatchResult, *, user_profile_id: str = "default") -> int:
        """Persist a match result for a job."""

        timestamp = _utc_now()
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO job_matches (
                    job_id,
                    match_percentage,
                    matched_skills,
                    missing_skills,
                    matched_keywords,
                    score_breakdown,
                    created_at,
                    user_profile_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    match_result.match_percentage,
                    json.dumps(match_result.matched_skills, ensure_ascii=False, default=str),
                    json.dumps(match_result.missing_skills, ensure_ascii=False, default=str),
                    json.dumps(match_result.matched_keywords, ensure_ascii=False, default=str),
                    json.dumps(match_result.score_breakdown, ensure_ascii=False, default=str),
                    timestamp,
                    user_profile_id,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def get_job(self, job_id: int) -> JobRecord | None:
        row = self._fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
        if row is None:
            return None
        return self._row_to_job_record(row)

    def list_jobs(self, *, limit: int = 50) -> list[JobRecord]:
        rows = self._fetch_all("SELECT * FROM jobs ORDER BY updated_at DESC LIMIT ?", (limit,))
        return [self._row_to_job_record(row) for row in rows]

    def list_job_matches(self, *, job_id: int | None = None, limit: int = 50) -> list[JobMatchRecord]:
        if job_id is None:
            rows = self._fetch_all("SELECT * FROM job_matches ORDER BY created_at DESC LIMIT ?", (limit,))
        else:
            rows = self._fetch_all(
                "SELECT * FROM job_matches WHERE job_id = ? ORDER BY created_at DESC LIMIT ?",
                (job_id, limit),
            )
        return [self._row_to_match_record(row) for row in rows]

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT NOT NULL,
                    requirements TEXT NOT NULL,
                    responsibilities TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    source_url TEXT,
                    source_job_id TEXT,
                    source_name TEXT NOT NULL,
                    raw_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(source_url, source_job_id, title, company)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    match_percentage REAL NOT NULL,
                    matched_skills TEXT NOT NULL,
                    missing_skills TEXT NOT NULL,
                    matched_keywords TEXT NOT NULL,
                    score_breakdown TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    user_profile_id TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                )
                """
            )
            connection.commit()

    def _find_existing_job_id(self, parsed_job: ParsedJob) -> int | None:
        where_clauses: list[str] = []
        parameters: list[Any] = []

        if parsed_job.source_url:
            where_clauses.append("source_url = ?")
            parameters.append(parsed_job.source_url)
        if parsed_job.source_job_id:
            where_clauses.append("source_job_id = ?")
            parameters.append(parsed_job.source_job_id)

        where_clauses.append("title = ?")
        parameters.append(parsed_job.title)
        where_clauses.append("company = ?")
        parameters.append(parsed_job.company)

        query = "SELECT id FROM jobs WHERE " + " AND ".join(where_clauses) + " LIMIT 1"
        row = self._fetch_one(query, tuple(parameters))
        return int(row["id"]) if row else None

    def _row_to_job_record(self, row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=int(row["id"]),
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            requirements=self._load_json_list(row["requirements"]),
            responsibilities=self._load_json_list(row["responsibilities"]),
            keywords=self._load_json_list(row["keywords"]),
            source_url=row["source_url"],
            source_job_id=row["source_job_id"],
            source_name=row["source_name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            raw_payload=self._load_json_dict(row["raw_payload"]),
        )

    def _row_to_match_record(self, row: sqlite3.Row) -> JobMatchRecord:
        return JobMatchRecord(
            id=int(row["id"]),
            job_id=int(row["job_id"]),
            match_percentage=float(row["match_percentage"]),
            matched_skills=self._load_json_list(row["matched_skills"]),
            missing_skills=self._load_json_list(row["missing_skills"]),
            matched_keywords=self._load_json_list(row["matched_keywords"]),
            score_breakdown=self._load_json_dict(row["score_breakdown"]),
            created_at=row["created_at"],
            user_profile_id=row["user_profile_id"],
        )

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def _fetch_one(self, query: str, parameters: Iterable[Any]) -> sqlite3.Row | None:
        with self._connection() as connection:
            cursor = connection.execute(query, tuple(parameters))
            return cursor.fetchone()

    def _fetch_all(self, query: str, parameters: Iterable[Any]) -> list[sqlite3.Row]:
        with self._connection() as connection:
            cursor = connection.execute(query, tuple(parameters))
            return list(cursor.fetchall())

    def _load_json_list(self, value: str) -> list[str]:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []

        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return []

    def _load_json_dict(self, value: str) -> dict[str, Any]:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}

        if isinstance(parsed, dict):
            return dict(parsed)
        return {}