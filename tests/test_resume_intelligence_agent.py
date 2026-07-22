"""Tests for the Resume Intelligence Agent."""

from agents.resume_intelligence_agent import HashingEmbeddingProvider, QdrantResumeVectorStore, ResumeIntelligenceAgent, ResumeIntelligenceConfig, ResumeParser, ResumeEmbeddingService, ATSResumeBuilder


SAMPLE_RESUME = """
Jane Doe
Senior Python Engineer

Professional Summary
Senior engineer building FastAPI services, data pipelines, and automation systems.

Skills
Python, FastAPI, PostgreSQL, Redis, Docker, Qdrant

Experience
- Built production APIs with FastAPI and PostgreSQL.
- Automated job workflows and internal tooling.

Projects
- Job Search Platform: built a search and matching system for career workflows.

Certifications
- AWS Certified Developer

Education
- Bachelor of Science in Computer Science
"""


def test_resume_parser_extracts_structured_content() -> None:
    parser = ResumeParser()
    resume = parser.parse(SAMPLE_RESUME)

    assert resume.full_name == "Jane Doe"
    assert "Python" in resume.skills
    assert "FastAPI" in resume.summary or "FastAPI" in resume.keywords
    assert resume.projects
    assert resume.certifications
    assert resume.education


def test_hashing_embeddings_are_deterministic() -> None:
    provider = HashingEmbeddingProvider(dimensions=64)
    service = ResumeEmbeddingService(provider)
    parser = ResumeParser()
    resume = parser.parse(SAMPLE_RESUME)

    embedding_one = service.embed_resume(resume)
    embedding_two = service.embed_resume(resume)

    assert embedding_one == embedding_two
    assert len(embedding_one) == 64


def test_ats_builder_scores_keyword_coverage() -> None:
    parser = ResumeParser()
    ats_builder = ATSResumeBuilder()
    resume = parser.parse(SAMPLE_RESUME)

    document = ats_builder.build(resume, target_text="Python FastAPI PostgreSQL Docker Qdrant")

    assert document.ats_score > 0
    assert "python" in document.matched_keywords
    assert "SUMMARY" in document.text


def test_resume_agent_ingests_and_searches_with_local_qdrant() -> None:
    config = ResumeIntelligenceConfig(use_local_qdrant=True, qdrant_local_path=":memory:", vector_dimensions=64)
    agent = ResumeIntelligenceAgent(
        config=config,
        parser=ResumeParser(),
        embedding_service=ResumeEmbeddingService(HashingEmbeddingProvider(64)),
        vector_store=QdrantResumeVectorStore(config),
        ats_builder=ATSResumeBuilder(),
    )

    analysis = agent.ingest_resume(SAMPLE_RESUME)
    ats_document = agent.generate_ats_resume(SAMPLE_RESUME, target_text="Python FastAPI PostgreSQL Docker")
    similar = agent.find_similar_resumes(SAMPLE_RESUME, limit=3)

    assert analysis.resume.full_name == "Jane Doe"
    assert analysis.vector_record is not None
    assert ats_document.ats_score > 0
    assert similar