# Resume Tailoring Agent Architecture

## Goals

The agent must create a tailored resume only from verified candidate data. It can emphasize, reorder, and score existing content, but it must never create new job history or unverified claims.

## Flow

1. Parse resume input into structured data.
2. Parse the target job into structured data.
3. Compute the job match using the existing matching agent.
4. Build an ATS-safe tailored document.
5. Export the result to DOCX and PDF.

## Guarantees

- No invented experience.
- No fabricated employers or credentials.
- Only truthful reordering and keyword emphasis.
- Exported files are generated from the same tailored document object.

## Future Extensions

- Add version tracking for tailored outputs.
- Sync tailored resume artifacts to PostgreSQL.
- Generate cover letters from the same job fit analysis.
- Add explicit template support for different resume styles.