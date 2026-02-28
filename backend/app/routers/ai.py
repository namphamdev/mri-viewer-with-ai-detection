"""AI analysis endpoints — anomaly detection for MRI images."""

import logging
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from PIL import Image
from pydantic import BaseModel, Field

from app.ai.detector import run_detection, run_detection_on_synthetic
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class AnalyzeRequest(BaseModel):
    """Request body for the AI analysis endpoint."""

    image_name: str = Field(..., description="Image filename (e.g. 'image_001.jpg')")
    sensitivity: float = Field(
        0.5, ge=0.0, le=1.0, description="Detection sensitivity (0.0-1.0)"
    )
    analysis_type: str = Field(
        "anomaly", description="Analysis type: 'anomaly' or 'segmentation'"
    )


@router.post("/analyze")
async def ai_analyze(request: AnalyzeRequest) -> dict[str, Any]:
    """Run AI anomaly detection on a local MRI JPEG image.

    Loads the image from the configured images directory,
    converts to grayscale numpy array, and runs the detection pipeline.

    Returns findings, an overlay heatmap, and a summary.
    """
    logger.info(
        "AI analysis request: image=%s sensitivity=%.2f type=%s",
        request.image_name,
        request.sensitivity,
        request.analysis_type,
    )

    # Validate filename to prevent path traversal
    if "/" in request.image_name or "\\" in request.image_name or ".." in request.image_name:
        raise HTTPException(status_code=400, detail="Invalid image name")

    image_path = Path(settings.images_dir) / request.image_name

    if not image_path.is_file():
        # Fall back to synthetic demo if image not found
        logger.warning("Image not found at %s, using synthetic demo", image_path)
        result = run_detection_on_synthetic(
            sensitivity=request.sensitivity,
            analysis_type=request.analysis_type,
        )
        return result

    try:
        # Load JPEG as grayscale numpy array
        pil_img = Image.open(image_path).convert("L")
        pixel_array = np.array(pil_img)

        logger.info("Loaded image %s: shape=%s dtype=%s", request.image_name, pixel_array.shape, pixel_array.dtype)

        result = run_detection(
            pixel_array,
            sensitivity=request.sensitivity,
            analysis_type=request.analysis_type,
        )
        return result

    except Exception as e:
        logger.error("Failed to process image %s: %s", request.image_name, e)
        raise HTTPException(status_code=500, detail=f"Image processing failed: {e}")
