from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.routers import appointments, outbound, patients, vapi_webhook

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("startup", app=settings.app_name, env=settings.environment)
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Voice AI Agent backend for dental appointment management",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except Exception:
    pass

# Sentry
if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.1)

app.include_router(appointments.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
app.include_router(outbound.router, prefix="/api/v1")
app.include_router(vapi_webhook.router)


@app.get("/health")
def health_check():
    return JSONResponse({"status": "healthy", "service": settings.app_name})


# Static demo page — mounted last so API routes take priority
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
