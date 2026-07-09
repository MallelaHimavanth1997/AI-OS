from fastapi import FastAPI

app = FastAPI(
    title="AI-OS API",
    description="Multi-agent AI operating system backend",
    version="1.0.0"
)

@app.get("/")
def health_check():
    return {
        "status": "AI-OS running",
        "version": "1.0.0"
    }