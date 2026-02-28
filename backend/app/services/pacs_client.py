"""DICOMweb HTTP client for communicating with the PACS server."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Reusable async HTTP client — created once, shared across requests
_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Get or create the shared async HTTP client."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.pacs_base_url,
            timeout=httpx.Timeout(settings.pacs_timeout),
            verify=False,  # Some PACS servers use self-signed certs
            headers={
                "x-share-access-key": settings.pacs_access_key,
                "x-share-study-instance-uid": settings.default_study_uid,
                "Referer": (
                    f"https://pacs.mids.com.vn/viewer/viewer"
                    f"?StudyInstanceUIDs={settings.default_study_uid}"
                    f"&access_key={settings.pacs_access_key}"
                ),
            },
        )
    return _client


async def close_client() -> None:
    """Close the shared HTTP client."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def get_study_series(study_uid: str) -> list[dict[str, Any]]:
    """List all series in a study via WADO-RS /series endpoint."""
    client = await get_client()
    url = f"/studies/{study_uid}/series"
    logger.info("Fetching study series: %s", url)

    response = await client.get(
        url,
        headers={"Accept": "application/dicom+json"},
    )
    response.raise_for_status()
    return response.json()


async def get_series_metadata(
    study_uid: str, series_uid: str
) -> list[dict[str, Any]]:
    """Fetch series metadata via WADO-RS /metadata endpoint.

    Returns a JSON array of DICOM dataset objects.
    """
    client = await get_client()
    url = f"/studies/{study_uid}/series/{series_uid}/metadata"
    logger.info("Fetching metadata: %s", url)

    response = await client.get(
        url,
        headers={"Accept": "application/dicom+json"},
    )
    response.raise_for_status()
    return response.json()


async def get_series_instances(
    study_uid: str, series_uid: str
) -> list[dict[str, Any]]:
    """List instances in a series via WADO-RS /instances endpoint."""
    client = await get_client()
    url = f"/studies/{study_uid}/series/{series_uid}/instances"
    logger.info("Fetching instances: %s", url)

    response = await client.get(
        url,
        headers={"Accept": "application/dicom+json"},
    )
    response.raise_for_status()
    return response.json()


async def get_instance_frame(
    study_uid: str,
    series_uid: str,
    instance_uid: str,
    frame: int = 1,
) -> bytes:
    """Retrieve raw frame data for a specific instance.

    Returns the raw DICOM/multipart bytes from the PACS server.
    """
    client = await get_client()
    url = (
        f"/studies/{study_uid}/series/{series_uid}"
        f"/instances/{instance_uid}/frames/{frame}"
    )
    logger.info("Fetching frame: %s", url)

    response = await client.get(
        url,
        headers={
            "Accept": "multipart/related; type=application/octet-stream",
        },
    )
    response.raise_for_status()
    return response.content


async def get_instance_bulk(
    study_uid: str,
    series_uid: str,
    instance_uid: str,
) -> bytes:
    """Retrieve full DICOM instance as raw bytes (WADO-RS)."""
    client = await get_client()
    url = (
        f"/studies/{study_uid}/series/{series_uid}"
        f"/instances/{instance_uid}"
    )
    logger.info("Fetching full instance: %s", url)

    response = await client.get(
        url,
        headers={
            "Accept": "multipart/related; type=application/dicom",
        },
    )
    response.raise_for_status()
    return response.content
