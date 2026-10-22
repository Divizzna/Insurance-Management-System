import os
import sys
from pathlib import Path

# Add project root directory to sys.path so 'from backend...' imports resolve when run directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from backend.db import engine
from backend.config import settings
from backend.routers.customer import router as customer_router
from backend.routers.policy import router as policy_router
from backend.routers.payment import router as payment_router
from backend.routers.claim import router as claim_router
from backend.routers.claim_review import router as claim_review_router
from backend.routers.ai_chat import router as ai_chat_router

app = FastAPI(
    title=settings.app_name,
    description=(
        "Enterprise Insurance Management System "
        "with Generative AI and multi-agent claim adjudication."
    ),
    version="0.2.0",
)

# Enable CORS for local testing and cross-origin clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(customer_router)
app.include_router(policy_router)
app.include_router(payment_router)
app.include_router(claim_router)
app.include_router(claim_review_router)
app.include_router(ai_chat_router)

# Mount frontend static assets
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def home(request: Request):
    """
    Serves the interactive frontend web dashboard if accessed in a browser,
    or the API system status if requested via curl/JSON.
    """
    accept = request.headers.get("accept", "")
    index_file = FRONTEND_DIR / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(index_file)

    return {
        "message": "Welcome to InsureFlow AI",
        "project": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
        "web_dashboard": "/app",
        "docs": "/docs",
    }


@app.get("/app")
def serve_app():
    """Direct route to access the frontend web dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend app not found")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "insurance-management-api",
    }


@app.get(f"{settings.api_v1_prefix}/info")
def project_info():
    return {
        "project": settings.app_name,
        "environment": settings.app_env,
        "database": settings.mysql_database,
        "ai_configured": bool(settings.openai_api_key and settings.openai_api_key.strip()),
        "model": settings.openai_model,
    }


@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": settings.mysql_database,
            "connection": "successful",
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable",
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=True)
