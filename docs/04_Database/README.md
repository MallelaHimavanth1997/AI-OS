# Database Architecture

AI-OS stores operational data in PostgreSQL and uses JSONB for flexible machine-generated payloads.

## Core Tables

- `users`
- `jobs`
- `applications`
- `companies`
- `recruiters`
- `emails`
- `notifications`
- `resumes`
- `cover_letters`
- `dashboard`
- `history`

## Access Pattern

The codebase uses async SQLAlchemy with repository classes per aggregate. The schema is intentionally normalized where it matters and flexible where AI-generated or workflow-generated content must evolve over time.

## Implementation Rules

- Use UUIDs for primary keys.
- Keep timestamps in UTC.
- Store structured AI output in JSONB.
- Prefer repository methods over ad hoc SQL in application code.
