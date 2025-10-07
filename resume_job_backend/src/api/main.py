from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request

from src.core.config import settings, OPENAPI_TAGS
from src.api.routes.health import router as health_router
from src.api.routes.resumes import router as resumes_router
from src.api.routes.jobs import router as jobs_router
from src.api.routes.matches import router as matches_router

# Initialize FastAPI app with project metadata and tags
app = FastAPI(
    title="Resume Match & Improve API",
    description=(
        "Backend API for parsing resumes and jobs, generating ATS improvement suggestions, "
        "and computing match scores. Includes optional Supabase JWT auth."
    ),
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
)

# CORS configuration: include frontend origin(s)
allow_origins = set(settings.cors_origins or [])
# Always ensure localhost frontend is allowed for development
allow_origins.add("http://localhost:3000")
# optional https localhost for some setups
allow_origins.add("https://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router, tags=["Health"])
app.include_router(resumes_router, prefix="/resumes", tags=["Resumes"])
app.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
app.include_router(matches_router, tags=["Matching"])

@app.get("/", summary="Health Check", tags=["Health"])
def root_health():
    """Simple health endpoint at root path used by uptime checks."""
    return {"status": "ok"}


@app.get("/docs/websocket", summary="WebSocket Usage", tags=["Docs"])
def websocket_docs():
    """Provide info for any future WebSocket endpoints (none currently)."""
    return {
        "message": "No WebSocket endpoints currently. Future real-time features will be documented here.",
        "note": "Refer to /openapi.json for full REST API schema.",
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all to return JSON errors rather than HTML stack traces."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )
