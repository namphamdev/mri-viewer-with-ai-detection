"""Local image server — serves MRI JPG files from disk."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])

IMAGES_DIR = Path(settings.images_dir)


def _list_image_files() -> list[str]:
    """Return sorted list of .jpg filenames in the images directory."""
    if not IMAGES_DIR.is_dir():
        return []
    return sorted(f.name for f in IMAGES_DIR.iterdir() if f.suffix.lower() in (".jpg", ".jpeg"))


@router.get("")
async def list_images():
    """List all available MRI images."""
    files = _list_image_files()
    images = []
    for filename in files:
        filepath = IMAGES_DIR / filename
        images.append({
            "filename": filename,
            "size_bytes": filepath.stat().st_size,
            "url": f"/api/images/{filename}",
        })
    return {"images": images, "total": len(images)}


@router.get("/{filename}")
async def get_image(filename: str):
    """Serve an individual MRI image as JPEG."""
    filepath = IMAGES_DIR / filename
    if not filepath.is_file() or filepath.suffix.lower() not in (".jpg", ".jpeg"):
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
    # Prevent path traversal
    if not filepath.resolve().is_relative_to(IMAGES_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return FileResponse(filepath, media_type="image/jpeg")


@router.get("/{filename}/metadata")
async def get_image_metadata(filename: str):
    """Return synthetic DICOM-like metadata for a local MRI image."""
    filepath = IMAGES_DIR / filename
    if not filepath.is_file() or filepath.suffix.lower() not in (".jpg", ".jpeg"):
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")
    # Extract index from filename for varying metadata
    idx = "".join(c for c in filename if c.isdigit()) or "0"
    slice_num = int(idx)
    return {
        "filename": filename,
        "modality": "MR",
        "series_description": "Local MRI",
        "rows": 512,
        "columns": 512,
        "slice_number": slice_num,
        "slice_thickness": 5.0,
        "pixel_spacing": [0.5, 0.5],
        "window_center": 128,
        "window_width": 256,
        "patient_id": "LOCAL-001",
        "study_description": "Brain MRI",
        "size_bytes": filepath.stat().st_size,
    }
