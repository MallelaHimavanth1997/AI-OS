# Backend Foundation

The backend package contains the shared FastAPI application factory, environment-driven settings, logging configuration, JWT security helpers, and request dependencies used by AI-OS services and agents.

## Modules

- `config.py` centralizes runtime configuration.
- `logging.py` configures Loguru for console and file output.
- `security.py` handles password hashing and JWT creation/validation.
- `schemas.py` defines shared API request and response models.
- `dependencies.py` provides reusable FastAPI dependencies.
- `app.py` creates the FastAPI application instance.

## Next Expansion Points

- PostgreSQL repositories and migration support.
- User persistence and RBAC.
- Agent and workflow routers.
- Background task orchestration.
