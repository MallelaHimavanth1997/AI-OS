###### \# AI-OS

###### 

###### \## Overview

###### 

###### AI-OS is an autonomous AI assistant framework designed to manage multiple specialized AI agents, automation workflows, memory systems, and productivity tools.

###### 

###### \## Project Goals

###### 

###### \- Build a multi-agent AI operating system

###### \- Automate job search and application workflows

###### \- Create intelligent task management agents

###### \- Maintain long-term AI memory

###### \- Integrate automation tools and APIs

###### 
# AI-OS

AI-OS is a local-first, open-source AI operating system for autonomous job search and personal executive assistance. The repository is being built incrementally around a clean, modular architecture so each agent, service, and integration can be developed and tested independently.

## What This System Does

- Understands resume content and career goals.
- Searches jobs continuously during configured working hours.
- Tailors resumes and cover letters when needed.
- Applies to jobs where automation is possible.
- Tracks recruiter activity, Gmail, notifications, and dashboards.
- Runs locally with privacy-first defaults and open-source infrastructure.

## Core Stack

- Python 3.12+
- FastAPI
- LangGraph and LangChain
- Ollama with open-source models
- PostgreSQL, Qdrant, and Redis
- Playwright for browser automation
- n8n for workflow automation
- Grafana for dashboards
- Docker and Nginx for deployment

## Repository Layout

- [backend](backend)
- [frontend](frontend)
- [agents](agents)
- [memory](memory)
- [workflows](workflows)
- [database](database)
- [dashboard](dashboard)
- [config](config)
- [docker](docker)
- [scripts](scripts)
- [logs](logs)
- [docs](docs)
- [tests](tests)
- [playwright](playwright)
- [resumes](resumes)
- [templates](templates)
- [emails](emails)
- [cover_letters](cover_letters)
- [notifications](notifications)
- [utils](utils)
- [api](api)
- [scheduler](scheduler)

## Authoritative Spec

The master project specification is documented in the conversation context and should be reflected in the architecture, module boundaries, and deployment strategy. The docs folder now contains the permanent project knowledge base for future implementation work.
###### \- FastAPI


