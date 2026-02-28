"""DICOM image preprocessing for AI model input."""

import logging

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def normalize_pixel_data(pixel_array: np.ndarray) -> np.ndarray:
    """Normalize pixel data to 0-1 float range.

    Handles various DICOM pixel value ranges (8-bit, 12-bit, 16-bit).
    """
    img = pixel_array.astype(np.float64)
    min_val = img.min()
    max_val = img.max()

    if max_val > min_val:
        img = (img - min_val) / (max_val - min_val)
    else:
        img = np.zeros_like(img, dtype=np.float64)

    return img


def resize_for_model(image: np.ndarray, target_size: int = 256) -> np.ndarray:
    """Resize a 2D image to target_size x target_size for model input.

    Uses PIL for high-quality resizing with antialiasing.
    Returns a float64 array in 0-1 range.
    """
    # Convert to PIL for quality resizing
    if image.dtype != np.uint8:
        # Scale to 0-255 for PIL
        img_uint8 = (np.clip(image, 0.0, 1.0) * 255).astype(np.uint8)
    else:
        img_uint8 = image

    pil_img = Image.fromarray(img_uint8, mode="L")
    pil_img = pil_img.resize((target_size, target_size), Image.LANCZOS)

    # Convert back to float 0-1
    return np.array(pil_img, dtype=np.float64) / 255.0


def preprocess_for_detection(
    pixel_array: np.ndarray,
    target_size: int = 256,
) -> np.ndarray:
    """Full preprocessing pipeline: normalize and resize.

    Args:
        pixel_array: Raw DICOM pixel data (2D numpy array).
        target_size: Output size (square).

    Returns:
        Preprocessed image as float64 array in 0-1 range, shape (target_size, target_size).
    """
    # Handle 3D arrays (multi-frame) — take first slice
    if pixel_array.ndim == 3:
        pixel_array = pixel_array[0]

    if pixel_array.ndim != 2:
        raise ValueError(f"Expected 2D pixel array, got shape {pixel_array.shape}")

    normalized = normalize_pixel_data(pixel_array)
    resized = resize_for_model(normalized, target_size)

    logger.debug(
        "Preprocessed image: input %s -> output %s, range [%.3f, %.3f]",
        pixel_array.shape,
        resized.shape,
        resized.min(),
        resized.max(),
    )

    return resized
