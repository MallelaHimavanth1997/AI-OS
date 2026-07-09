# Job Search Agent

The Job Search Agent is the first specialized module in AI-OS. It searches for jobs, parses descriptions into structured records, matches them against a user skill profile, calculates a match percentage, and stores everything in SQLite for downstream workflows.

## What It Does

- Searches jobs through an injected provider interface.
- Parses raw job data into a normalized internal model.
- Scores each job against the user’s skills.
- Persists both the job record and the match result.
- Leaves a clean hook for future OpenAI-based enrichment or rewriting.

## Files

- `config.py` holds runtime settings and environment-driven defaults.
- `parser.py` converts unstructured job descriptions into a structured `ParsedJob` model.
- `matcher.py` computes a transparent skill-to-job match percentage.
- `database.py` stores jobs and match scores in SQLite.
- `agent.py` orchestrates search, parse, match, and persistence.
- `architecture.md` documents the system flow and extension points.

## Usage

The agent is provider-agnostic. Inject a class that implements `search_jobs()` and call the orchestration layer:

```python
from agents.job_search_agent import JobSearchAgent

agent = JobSearchAgent(provider=my_provider)
summary = agent.search_jobs(
    "python backend engineer",
    location="Remote",
    user_skills=["Python", "FastAPI", "SQLite"],
)
```

If you only have raw jobs already, use `rank_jobs()` to parse and score them without a live provider.

## Environment Variables

- `AI_OS_JOB_SEARCH_DB`: SQLite database path.
- `AI_OS_JOB_SEARCH_MAX_RESULTS`: Maximum results returned by `search_jobs()`.
- `AI_OS_JOB_SEARCH_MIN_MATCH`: Minimum match threshold for later workflow filtering.
- `AI_OS_ENABLE_OPENAI`: Enables the future OpenAI enhancement hook.
- `AI_OS_OPENAI_MODEL`: Model name to use when that integration is wired in.
- `AI_OS_JOB_SOURCE_NAME`: Default source label stored with new jobs.
