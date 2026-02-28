"""DICOM pixel data extraction and image conversion utilities."""

import io
import logging
import re

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def extract_pixel_data_from_multipart(raw_bytes: bytes) -> bytes:
    """Extract pixel data from a multipart/related DICOM response.

    The PACS server returns multipart/related data. We need to strip the
    MIME boundaries and extract the raw pixel payload.
    """
    # Look for the boundary in the response
    # Multipart boundary is typically after the first \r\n\r\n
    # Try to find DICOM-style multipart boundaries
    boundary_match = re.search(rb"--([^\r\n]+)", raw_bytes)
    if boundary_match:
        boundary = boundary_match.group(0)
        parts = raw_bytes.split(boundary)
        for part in parts:
            # Skip empty parts and the closing boundary
            if not part.strip() or part.strip() == b"--":
                continue
            # Find the content after headers (double CRLF or double LF)
            header_end = part.find(b"\r\n\r\n")
            if header_end == -1:
                header_end = part.find(b"\n\n")
            if header_end != -1:
                content = part[header_end + 4 :].strip()
                if content:
                    return content

    # If no boundary found, return as-is (might already be raw data)
    return raw_bytes


def apply_windowing(
    pixel_array: np.ndarray,
    window_center: float | None = None,
    window_width: float | None = None,
) -> np.ndarray:
    """Apply DICOM windowing (contrast adjustment) to pixel data.

    Converts raw pixel values to display values (0-255) using the
    window center/width parameters common in medical imaging.
    """
    img = pixel_array.astype(np.float64)

    if window_center is not None and window_width is not None:
        # Standard DICOM linear windowing
        lower = window_center - window_width / 2
        upper = window_center + window_width / 2
        img = np.clip(img, lower, upper)
        img = ((img - lower) / (upper - lower)) * 255.0
    else:
        # Auto-window: scale full range to 0-255
        min_val = img.min()
        max_val = img.max()
        if max_val > min_val:
            img = ((img - min_val) / (max_val - min_val)) * 255.0
        else:
            img = np.zeros_like(img)

    return img.astype(np.uint8)


def pixel_array_to_png(
    pixel_array: np.ndarray,
    window_center: float | None = None,
    window_width: float | None = None,
) -> bytes:
    """Convert a DICOM pixel array to PNG bytes.

    Applies windowing and converts to an 8-bit grayscale PNG.
    """
    windowed = apply_windowing(pixel_array, window_center, window_width)

    # Handle multi-frame or 3D arrays — take first slice if needed
    if windowed.ndim == 3:
        windowed = windowed[0]

    image = Image.fromarray(windowed, mode="L")

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def raw_frame_to_png(
    raw_bytes: bytes,
    rows: int,
    columns: int,
    bits_allocated: int = 16,
    pixel_representation: int = 0,
    window_center: float | None = None,
    window_width: float | None = None,
) -> bytes:
    """Convert raw pixel bytes to a PNG image.

    This is used when we have raw frame data (from multipart response)
    and metadata about the image dimensions.
    """
    # Determine numpy dtype from DICOM attributes
    if bits_allocated == 8:
        dtype = np.uint8
    elif bits_allocated == 16:
        dtype = np.int16 if pixel_representation == 1 else np.uint16
    elif bits_allocated == 32:
        dtype = np.int32 if pixel_representation == 1 else np.uint32
    else:
        dtype = np.uint16

    try:
        pixel_data = extract_pixel_data_from_multipart(raw_bytes)
        pixel_array = np.frombuffer(pixel_data, dtype=dtype)
        pixel_array = pixel_array.reshape((rows, columns))
    except (ValueError, Exception) as e:
        logger.error("Failed to parse raw pixel data: %s", e)
        # Return a placeholder black image
        pixel_array = np.zeros((rows, columns), dtype=np.uint8)

    return pixel_array_to_png(pixel_array, window_center, window_width)
