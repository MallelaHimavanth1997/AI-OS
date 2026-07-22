# Resume Intelligence Agent

The Resume Intelligence Agent parses resume content, extracts skills and structured sections, generates deterministic embeddings, stores them in Qdrant, and produces ATS-optimized resume output without inventing experience.

## What It Does

- Parses plain text, PDF, DOCX, or structured resume input.
- Extracts skills, projects, experience, certifications, education, and ATS keywords.
- Generates local deterministic embeddings for each resume.
- Stores embeddings in Qdrant for similarity search and long-term memory.
- Builds ATS-friendly resume text and keyword coverage analysis.

## Files

- `config.py` holds runtime settings.
- `extractor.py` handles section parsing and keyword extraction.
- `parser.py` normalizes raw resume inputs.
- `embeddings.py` provides deterministic local embeddings.
- `vector_store.py` stores and queries resume vectors in Qdrant.
- `ats.py` generates ATS-optimized output.
- `agent.py` orchestrates the full pipeline.
- `architecture.md` explains the design and extension points.

## Usage

```python
from agents.resume_intelligence_agent import ResumeIntelligenceAgent

agent = ResumeIntelligenceAgent()
analysis = agent.ingest_resume("path/to/resume.txt")
ats_document = agent.generate_ats_resume("path/to/resume.txt", target_text="Python backend engineer")
```

## Environment Variables

- `RESUME_VECTOR_COLLECTION`: Qdrant collection name.
- `RESUME_VECTOR_DIMENSIONS`: Embedding dimension count.
- `QDRANT_URL`: External Qdrant URL.
- `QDRANT_API_KEY`: Optional Qdrant API key.
- `RESUME_QDRANT_LOCAL`: Enables local Qdrant mode for development.
- `RESUME_STORAGE_DIR`: Local directory for processed resume artifacts.
- `RESUME_ENABLE_LLM_ENRICHMENT`: Enables future local LLM enhancement.
