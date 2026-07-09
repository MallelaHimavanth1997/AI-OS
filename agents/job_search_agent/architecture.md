# Job Search Agent Architecture

## Goals

The module is designed to be provider-agnostic, persistence-backed, and ready for a future OpenAI integration without making the current code depend on external APIs.

## Flow

1. `agent.py` asks a provider for raw jobs or receives pre-fetched job payloads.
2. `parser.py` normalizes the payload into a `ParsedJob` structure.
3. `matcher.py` compares the parsed job against the user’s skill profile and calculates a match percentage.
4. `database.py` stores the job and the resulting match record in SQLite.
5. `agent.py` returns a ranked summary that can feed notifications, dashboards, or workflows.

## Responsibilities

### `config.py`

Owns runtime defaults and environment-driven settings. This keeps database paths, thresholds, and future OpenAI options out of business logic.

### `parser.py`

Turns inconsistent job descriptions into a stable internal model. It preserves the original payload for traceability and later enrichment.

### `matcher.py`

Scores jobs using a transparent formula based on user skill overlap, requirement overlap, and keyword overlap. The goal is explainability, not black-box ranking.

### `database.py`

Encapsulates SQLite schema creation and persistence. Jobs and match results are stored separately so the system can re-score jobs later as user profiles change.

### `agent.py`

Coordinates the full workflow and exposes the public API. It also contains a narrow `OpenAIJobEnhancer` protocol so a future LLM layer can refine descriptions or search queries without changing the rest of the module.

## Future OpenAI Integration

The current implementation keeps the OpenAI hook optional and isolated. A future implementation can:

- rewrite noisy job descriptions into structured sections,
- extract missing metadata from raw postings,
- refine search queries from user goals,
- generate personalized application notes or summaries.

That work should plug into the `OpenAIJobEnhancer` protocol or a separate query-refinement provider without affecting storage or scoring.