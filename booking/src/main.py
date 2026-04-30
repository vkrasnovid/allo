"""FastAPI application for the booking service."""

import logging
import os

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Алло — Booking Service",
    description="CRM & Booking API for voice AI secretary",
    version="0.1.0",
)


@app.on_event("startup")
async def startup():
    try:
        from src.database import engine
        from src.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"Database startup skipped (will retry on first request): {e}")


@app.on_event("shutdown")
async def shutdown():
    try:
        from src.database import engine
        await engine.dispose()
        logger.info("Database engine disposed")
    except Exception:
        pass


# Import routes after app creation to avoid circular imports
from src.api.routes import router  # noqa: E402
app.include_router(router)
