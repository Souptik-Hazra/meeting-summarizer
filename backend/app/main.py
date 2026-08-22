from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.meeting import router as meeting_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for converting meeting audio into structured meeting intelligence.",
)

# Configure CORS
origins = []
if settings.FRONTEND_URL:
    for u in settings.FRONTEND_URL.split(","):
        cleaned = u.strip().rstrip("/")
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

for default_origin in ["http://localhost:5173", "https://meeting-summarizer-app.netlify.app"]:
    if default_origin not in origins:
        origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(meeting_router)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify API service status."""
    return {
        "status": "ok",
        "service": "meeting-summarizer-api",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
