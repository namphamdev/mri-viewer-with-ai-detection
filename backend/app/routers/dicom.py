"""DICOM proxy endpoints — bridges frontend to the PACS server."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services import pacs_client
from app.services.dicom_utils import raw_frame_to_png

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/studies", tags=["dicom"])


@router.get("/{study_uid}/series")
async def list_study_series(study_uid: str) -> dict[str, Any]:
    """List all series in a study."""
    try:
        raw = await pacs_client.get_study_series(study_uid)
        series_list = []
        for s in raw:
            series_list.append({
                "series_uid": s.get("0020000E", {}).get("Value", [""])[0],
                "description": s.get("0008103E", {}).get("Value", ["Unknown"])[0],
                "modality": s.get("00080060", {}).get("Value", [""])[0],
                "num_instances": s.get("00201209", {}).get("Value", [0])[0],
            })
        return {"series": series_list, "total": len(series_list)}
    except httpx.ConnectError as e:
        logger.error("Cannot connect to PACS server: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Cannot connect to PACS server.",
        )
    except httpx.TimeoutException as e:
        logger.error("PACS server timeout: %s", e)
        raise HTTPException(
            status_code=504,
            detail="PACS server request timed out.",
        )
    except httpx.HTTPStatusError as e:
        logger.error("PACS server returned error: %s", e)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PACS server error: {e.response.status_code}",
        )


@router.get("/{study_uid}/series/{series_uid}/metadata")
async def get_series_metadata(
    study_uid: str,
    series_uid: str,
) -> list[dict[str, Any]]:
    """Proxy series metadata from the PACS server.

    Returns the DICOM JSON metadata array for all instances in the series.
    """
    try:
        return await pacs_client.get_series_metadata(study_uid, series_uid)
    except httpx.ConnectError as e:
        logger.error("Cannot connect to PACS server: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Cannot connect to PACS server. Please check the server URL.",
        )
    except httpx.TimeoutException as e:
        logger.error("PACS server timeout: %s", e)
        raise HTTPException(
            status_code=504,
            detail="PACS server request timed out.",
        )
    except httpx.HTTPStatusError as e:
        logger.error("PACS server returned error: %s", e)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PACS server error: {e.response.status_code}",
        )


@router.get("/{study_uid}/series/{series_uid}/instances")
async def list_instances(
    study_uid: str,
    series_uid: str,
) -> list[dict[str, Any]]:
    """List all instances in a series."""
    try:
        return await pacs_client.get_series_instances(study_uid, series_uid)
    except httpx.ConnectError as e:
        logger.error("Cannot connect to PACS server: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Cannot connect to PACS server.",
        )
    except httpx.TimeoutException as e:
        logger.error("PACS server timeout: %s", e)
        raise HTTPException(
            status_code=504,
            detail="PACS server request timed out.",
        )
    except httpx.HTTPStatusError as e:
        logger.error("PACS server returned error: %s", e)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PACS server error: {e.response.status_code}",
        )


@router.get(
    "/{study_uid}/series/{series_uid}/instances/{instance_uid}/frames/{frame}"
)
async def get_frame(
    study_uid: str,
    series_uid: str,
    instance_uid: str,
    frame: int = 1,
    window_center: float | None = Query(None, description="Window center for display"),
    window_width: float | None = Query(None, description="Window width for display"),
    rows: int = Query(512, description="Image rows (from metadata)"),
    columns: int = Query(512, description="Image columns (from metadata)"),
    bits_allocated: int = Query(16, description="Bits allocated per pixel"),
    pixel_representation: int = Query(0, description="0=unsigned, 1=signed"),
) -> Response:
    """Get a single frame as a PNG image.

    Fetches raw frame data from PACS, applies windowing, and returns PNG.
    The client should supply image dimensions from the metadata endpoint.
    """
    try:
        raw_bytes = await pacs_client.get_instance_frame(
            study_uid, series_uid, instance_uid, frame
        )

        png_bytes = raw_frame_to_png(
            raw_bytes,
            rows=rows,
            columns=columns,
            bits_allocated=bits_allocated,
            pixel_representation=pixel_representation,
            window_center=window_center,
            window_width=window_width,
        )

        return Response(content=png_bytes, media_type="image/png")

    except httpx.ConnectError as e:
        logger.error("Cannot connect to PACS server: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Cannot connect to PACS server.",
        )
    except httpx.TimeoutException as e:
        logger.error("PACS server timeout: %s", e)
        raise HTTPException(
            status_code=504,
            detail="PACS server request timed out.",
        )
    except httpx.HTTPStatusError as e:
        logger.error("PACS server returned error: %s", e)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PACS server error: {e.response.status_code}",
        )
