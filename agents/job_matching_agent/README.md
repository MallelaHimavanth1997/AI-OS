# Job Matching Agent

The Job Matching Agent compares a parsed resume to one or more parsed job descriptions, calculates a similarity score, computes priority, identifies missing skills, and returns ranked opportunities.

## What It Does

- Matches a resume against jobs using deterministic local scoring.
- Produces a total match score and a priority score.
- Identifies matched skills, missing skills, and keyword gaps.
- Returns ranked opportunities with actionable recommendations.

## Files

- `config.py` holds score thresholds and weights.
- `matcher.py` performs the actual similarity calculations.
- `agent.py` orchestrates resume parsing, job parsing, ranking, and reporting.
- `architecture.md` describes the design and scoring model.

## Usage

```python
from agents.job_matching_agent import JobMatchingAgent

agent = JobMatchingAgent()
report = agent.match_resume_to_jobs(resume_text, jobs)
```
