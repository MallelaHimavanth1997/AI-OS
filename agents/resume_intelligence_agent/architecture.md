# Resume Intelligence Agent Architecture

## Goals

The agent is designed to turn resume input into structured career data, deterministic embeddings, and ATS-safe output while keeping the implementation local-first and testable.

## Flow

1. `parser.py` loads text from raw input or a file and returns a normalized `ParsedResume`.
2. `extractor.py` identifies named sections, skills, projects, experience, certifications, education, and keywords.
3. `embeddings.py` converts the structured resume into a deterministic local vector.
4. `vector_store.py` persists the embedding in Qdrant and supports similarity search.
5. `ats.py` builds an ATS-friendly resume document based only on existing facts.
6. `agent.py` coordinates the workflow and returns the analysis object.

## Design Principles

- Never invent experience or skills.
- Keep parsing tolerant of incomplete formatting.
- Make every transformation explainable.
- Keep the vector store and embedding provider swappable.

## Future Extensions

- Replace the hashing embedder with a local LLM embedding service.
- Add PDF and DOCX export from the ATS document.
- Sync resume versions to PostgreSQL and vector memory.
- Add resume tailoring against job descriptions and application workflows.