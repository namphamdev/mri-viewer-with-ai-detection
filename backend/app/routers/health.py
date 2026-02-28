"""Health check router."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Return basic health status."""
    return {"status": "ok", "service": "mri-viewer-backend"}
