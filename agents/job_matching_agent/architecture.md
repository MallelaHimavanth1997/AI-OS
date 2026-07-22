# Job Matching Agent Architecture

## Goals

The agent is intentionally deterministic and explainable. It compares parsed resume data to parsed job data, then returns transparent score components and recommendations.

## Flow

1. `ResumeParser` converts the resume input into structured data.
2. `JobDescriptionParser` converts each job into a structured record.
3. `JobMatcher` computes score components from skills, keywords, and experience signals.
4. `JobMatchingAgent` ranks jobs and wraps the results in a report.

## Scoring Model

- Required skill overlap is weighted most heavily.
- Job keyword alignment contributes secondary signal.
- Experience alignment adds seniority and role-fit context.
- Priority score adds practical routing heuristics such as urgent or remote listings.

## Future Extensions

- Persist ranked matches in PostgreSQL for dashboarding.
- Add job source metadata and per-job explanations.
- Integrate OpenAI or local LLM assistance for narrative match summaries.