"""FastAPI main application entry point for RE-THREAD."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.analyze import router as analyze_router
from backend.app.api.recommend import router as recommend_router
from backend.app.api.outcome import router as outcome_router
from backend.app.config import settings
from backend.app.db import engine, get_db, Base
from backend.app.ml.loader import model_registry
from backend.app.models_db import Facility
from backend.app.schemas import HealthResponse
from backend.app.seed.seed_data import seed_all

logger = logging.getLogger("rethread.main")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: runs on startup and shutdown."""
    logger.info("Starting up RE-THREAD API...")

    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)

    # Check if DB has data; if empty, seed default realistic Pune data
    from backend.app.db import SessionLocal
    db = SessionLocal()
    try:
        facility_count = db.query(Facility).count()
        if facility_count == 0:
            logger.info("Database appears unseeded. Seeding default dataset...")
            seed_all()
    finally:
        db.close()

    # Load ML models once at backend startup (Rule #5)
    model_registry.load_all_models()

    yield

    logger.info("Shutting down RE-THREAD API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Circular Fashion Decision Platform",
    lifespan=lifespan,
)

import time

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header_and_logging(request, call_next):
    """Structured request logging and execution latency tracking."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    logger.info(
        f"[{request.method}] {request.url.path} -> {response.status_code} "
        f"({duration_ms:.2f}ms)"
    )
    return response


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health check endpoint",
)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Verifies that API and database connection are operational."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    return HealthResponse(
        status="ok",
        app=settings.PROJECT_NAME,
        version=settings.VERSION,
        database=db_status,
    )


# Register API Routers (both root level per docs and /api/v1 prefix)
app.include_router(analyze_router, tags=["Vision & Tag Analysis"])
app.include_router(recommend_router, tags=["Decision Engine & Recommendation"])
app.include_router(outcome_router, tags=["Lifecycle Loop & Outcome"])

app.include_router(analyze_router, prefix=settings.API_V1_STR, tags=["Vision & Tag Analysis (v1)"])
app.include_router(recommend_router, prefix=settings.API_V1_STR, tags=["Decision Engine & Recommendation (v1)"])
app.include_router(outcome_router, prefix=settings.API_V1_STR, tags=["Lifecycle Loop & Outcome (v1)"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
