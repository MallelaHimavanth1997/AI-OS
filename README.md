# AI-OS

AI-OS is an open-source autonomous AI Operating System that unifies two domains:
- **AI Job Search Assistant** for opportunity discovery and application workflows
- **AI Personal Executive Assistant** for planning, execution support, and automation

This repository currently provides a **production-grade project foundation** for long-term development.

## Project Vision
Build a modular, local-first, enterprise-ready AI platform with clear boundaries between orchestration, domain logic, integrations, and infrastructure.

## Architecture
AI-OS follows:
- **Clean Architecture** for separation of concerns
- **SOLID principles** for maintainability and extensibility
- **Domain-focused modular design** for independent evolution of components

Planned core layers:
1. Interface Layer (API, workflows, UI integrations)
2. Application Layer (agents, services, orchestration)
3. Domain Layer (business rules, models, contracts)
4. Infrastructure Layer (PostgreSQL, Qdrant, Redis, browser automation, observability)

## Technology Stack
- Python 3.12
- FastAPI
- LangGraph + LangChain
- Ollama (Qwen3 default model)
- PostgreSQL
- Qdrant
- Redis
- Playwright
- n8n
- Docker
- Grafana
- Loguru
- Pytest

## Installation (Foundation Stage)
1. Clone the repository.
2. Copy environment template:
   ```bash
   cp .env.example .env
   ```
3. Review folder READMEs and docs to begin implementation.

## Roadmap
- Phase 1: Foundation and architecture scaffolding (current)
- Phase 2: Core backend and agent orchestration
- Phase 3: Integrations, automation workflows, and UI/dashboard
- Phase 4: Security hardening, scalability, and production operations

## Folder Structure
```text
AI-OS/
├── backend/
├── browser/
├── dashboard/
├── docker/
├── docs/
├── emails/
├── frontend/
├── logs/
├── resumes/
├── scripts/
├── templates/
├── workflows/
└── .github/workflows/
```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution standards and workflow.

## License
This project is licensed under the [MIT License](LICENSE).
