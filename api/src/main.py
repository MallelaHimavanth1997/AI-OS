"""ASGI entry point for the AI-OS API."""

from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))

from backend.app import create_app
from api.src.routers import resume, jobs, matching, applications


app = create_app()

# Include routers
app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(matching.router)
app.include_router(applications.router)


@app.get("/health")
async def health_check():
	"""Health check endpoint."""
	return {"status": "ok", "service": "ai-os-api"}