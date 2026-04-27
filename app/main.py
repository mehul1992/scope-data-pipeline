from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import companies, health, snapshots, uploads
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Scope Data Pipeline API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router, tags=["health"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(snapshots.router, prefix="/snapshots", tags=["snapshots"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
