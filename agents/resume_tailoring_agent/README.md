# Resume Tailoring Agent

The Resume Tailoring Agent turns a parsed resume and a target job into a truthful ATS-safe tailored resume, then exports it as both DOCX and PDF.

## What It Does

- Tailors a resume against a single target job.
- Reorders and emphasizes existing content without inventing experience.
- Calculates an ATS score from keyword coverage and match quality.
- Exports the final document to DOCX and PDF.
- Supports batch tailoring for multiple target jobs.

## Files

- `config.py` holds output paths and tuning settings.
- `tailor.py` performs the actual document transformation and export.
- `agent.py` orchestrates parsing, matching, tailoring, and file generation.
- `architecture.md` documents the design and guarantees.

## Usage

```python
from agents.resume_tailoring_agent import ResumeTailoringAgent

agent = ResumeTailoringAgent()
summary = agent.tailor_resume(resume_text, job_text)
```
