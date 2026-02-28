"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import ai, dicom, health, local_images
from app.services import pacs_client

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    logger.info("Starting MRI Viewer Backend")
    logger.info("Local images dir: %s", settings.images_dir)
    logger.info("PACS base URL: %s", settings.pacs_base_url)
    yield
    # Cleanup: close the shared HTTP client
    await pacs_client.close_client()
    logger.info("Shutdown complete")


app = FastAPI(
    title="MRI Viewer Backend",
    description="DICOMweb proxy and AI detection API for MRI viewing",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow configured frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(local_images.router, prefix="/api")
app.include_router(dicom.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
