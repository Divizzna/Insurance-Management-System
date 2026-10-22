from fastapi import HTTPException
from sqlalchemy import text
from backend.db import engine
from fastapi import FastAPI
from backend.config import settings
from backend.routers.customer import router as customer_router
from backend.routers.policy import router as policy_router

app = FastAPI(
    title=settings.app_name,
    description=(
        "Educational Insurance Management System "
        "with Generative AI and multi-agent workflows."
    ),
    version="0.1.0",
)
app.include_router(customer_router)
app.include_router(policy_router)



@app.get("/")
def home():
    return {
        "message": "Welcome to InsureFlow AI",
        "project": settings.app_name,
        "environment": settings.app_env,
        "status": "running",
    }


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
        "ai_configured": bool(
            settings.openai_base_url
            and settings.openai_api_key
            and settings.openai_model
        ),
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
