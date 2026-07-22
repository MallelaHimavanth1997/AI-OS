# Database Foundation

AI-OS uses PostgreSQL as the system of record for users, jobs, applications, companies, recruiters, emails, notifications, resumes, cover letters, dashboard metrics, and audit history.

## What Lives Here

- `config.py` holds database connection settings.
- `engine.py` builds the async SQLAlchemy engine and session factory.
- `models.py` defines the PostgreSQL schema in ORM form.
- `repositories/` contains reusable async repository classes.
- `migrations/001_initial.sql` defines the initial production schema.

## Design Notes

- UUID primary keys are used across the schema for safe distributed generation.
- JSONB is used for flexible payloads, metadata, and extracted structures.
- Async SQLAlchemy is the default access pattern so the backend can scale with FastAPI.
- The migration is explicit SQL so it can run under Alembic, container init scripts, or a manual deploy step.
