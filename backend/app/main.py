import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.api.routes import router as api_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables upon startup."""
    logger.info("Initializing database connection and schema...")
    try:
        await init_db()
        logger.info("Database schema synchronized successfully.")
    except Exception as exc:
        logger.error(f"Database initialization warning ({str(exc)}). Retrying on first query.")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Stateful Multi-Agent AI Orchestration System powered by LangGraph, Celery, Redis, PostgreSQL, and FastAPI.",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "create_task": "POST /api/tasks",
            "list_tasks": "GET /api/tasks",
            "get_task": "GET /api/tasks/{task_id}",
            "get_events": "GET /api/tasks/{task_id}/events",
            "websocket_stream": "WS /api/ws/{task_id}",
        }
    }
