"""High-level anomaly detection pipeline.

Uses image-processing techniques (intensity statistics, texture analysis,
morphological operations) as the primary detection method.
Falls back to U-Net model inference when weights are available.
"""

import logging
import time

import numpy as np
from scipy import ndimage
from scipy.ndimage import gaussian_filter

from app.ai.model import load_model, predict_with_model, is_torch_available
from app.ai.postprocessing import (
    Finding,
    extract_findings_from_mask,
    generate_summary,
    heatmap_to_base64,
    mask_to_heatmap_png,
)
from app.ai.preprocessing import preprocess_for_detection

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model = None
_model_loaded = False


def _get_model():
    """Get the model singleton, loading once on first call."""
    global _model, _model_loaded
    if not _model_loaded:
        _model = load_model()
        _model_loaded = True
    return _model


def detect_anomalies_image_processing(
    image: np.ndarray,
    sensitivity: float = 0.5,
) -> np.ndarray:
    """Detect anomalies using image-processing approach.

    Analyzes intensity statistics and finds regions that deviate
    significantly from the expected tissue distribution.

    Args:
        image: Preprocessed 2D float array (0-1 range).
        sensitivity: Detection sensitivity 0.0 (low) to 1.0 (high).

    Returns:
        Detection mask as 2D float array (0-1), same shape as input.
    """
    h, w = image.shape

    # Create a brain mask (non-background regions)
    # Threshold at a low value to separate brain from background
    brain_mask = image > 0.1

    # Erode the brain mask slightly to avoid edge artifacts
    brain_mask = ndimage.binary_erosion(brain_mask, iterations=3)

    if brain_mask.sum() < 100:
        # Not enough tissue detected — return empty mask
        logger.warning("Insufficient tissue in image for analysis")
        return np.zeros_like(image)

    # Compute tissue statistics within the brain mask
    tissue_values = image[brain_mask]
    tissue_mean = tissue_values.mean()
    tissue_std = tissue_values.std()

    if tissue_std < 1e-6:
        return np.zeros_like(image)

    # Sensitivity controls the threshold:
    # Low sensitivity (0.0) -> high threshold (3.0 std) -> fewer detections
    # High sensitivity (1.0) -> low threshold (1.0 std) -> more detections
    threshold_std = 3.0 - (sensitivity * 2.0)  # Range: 3.0 to 1.0
    threshold_std = max(threshold_std, 0.5)

    # Find hyperintense regions (above mean + threshold * std)
    hyper_mask = (image > (tissue_mean + threshold_std * tissue_std)) & brain_mask

    # Find hypointense regions (below mean - threshold * std)
    hypo_mask = (image < (tissue_mean - threshold_std * tissue_std)) & brain_mask

    # Combine anomaly regions
    anomaly_binary = hyper_mask | hypo_mask

    # Clean up with morphological operations
    # Remove small noise
    anomaly_binary = ndimage.binary_opening(anomaly_binary, iterations=2)
    # Fill small gaps
    anomaly_binary = ndimage.binary_closing(anomaly_binary, iterations=2)
    # Remove tiny connected components
    labeled, num_features = ndimage.label(anomaly_binary)
    min_size = max(10, int(20 * sensitivity))  # Minimum region size
    for i in range(1, num_features + 1):
        if (labeled == i).sum() < min_size:
            anomaly_binary[labeled == i] = False

    # Create a smooth probability mask from the anomaly regions
    # Use the z-score deviation as the base probability
    z_scores = np.abs(image - tissue_mean) / tissue_std
    z_scores = z_scores * brain_mask  # Only within brain

    # Normalize z-scores to 0-1 range
    max_z = z_scores.max()
    if max_z > 0:
        probability = z_scores / max_z
    else:
        probability = np.zeros_like(image)

    # Mask by detected anomaly regions and smooth
    probability = probability * anomaly_binary.astype(np.float64)
    probability = gaussian_filter(probability, sigma=2.0)

    # Re-normalize to 0-1
    max_prob = probability.max()
    if max_prob > 0:
        probability = probability / max_prob

    return probability


def run_detection(
    pixel_array: np.ndarray,
    sensitivity: float = 0.5,
    analysis_type: str = "anomaly",
) -> dict:
    """Run the full anomaly detection pipeline.

    Args:
        pixel_array: Raw DICOM pixel data (2D numpy array).
        sensitivity: Detection sensitivity (0.0-1.0).
        analysis_type: Type of analysis ("anomaly" or "segmentation").

    Returns:
        Full detection result dictionary matching the API response schema.
    """
    start_time = time.time()

    # Preprocess
    preprocessed = preprocess_for_detection(pixel_array, target_size=256)

    # Try model-based detection first, fall back to image processing
    model = _get_model()
    if model is not None and analysis_type == "segmentation":
        try:
            mask = predict_with_model(model, preprocessed)
            logger.info("Used U-Net model for detection")
        except Exception as e:
            logger.warning("Model inference failed, falling back: %s", e)
            mask = detect_anomalies_image_processing(preprocessed, sensitivity)
    else:
        mask = detect_anomalies_image_processing(preprocessed, sensitivity)

    # Extract findings from the mask
    findings: list[Finding] = extract_findings_from_mask(
        mask, threshold=max(0.1, 0.5 - sensitivity * 0.4)
    )

    # Generate heatmap overlay
    heatmap_png = mask_to_heatmap_png(mask, alpha_scale=0.7)
    overlay_b64 = heatmap_to_base64(heatmap_png)

    # Build response
    processing_time_ms = int((time.time() - start_time) * 1000)

    return {
        "status": "completed",
        "analysis_type": analysis_type,
        "processing_time_ms": processing_time_ms,
        "findings": [f.to_dict() for f in findings],
        "overlay": {
            "type": "heatmap",
            "data": overlay_b64,
            "width": 256,
            "height": 256,
            "colormap": "jet",
        },
        "summary": generate_summary(findings),
    }


def run_detection_on_synthetic(
    sensitivity: float = 0.5,
    analysis_type: str = "anomaly",
) -> dict:
    """Run detection on a synthetic MRI-like image for demo/testing.

    Generates a synthetic brain-like image with an anomaly injected,
    then runs the detection pipeline on it.
    """
    start_time = time.time()

    # Create a synthetic brain-like image (256x256)
    size = 256
    y, x = np.ogrid[-1:1:complex(0, size), -1:1:complex(0, size)]

    # Brain shape (ellipse)
    brain = ((x / 0.7) ** 2 + (y / 0.85) ** 2) < 1.0
    brain_img = brain.astype(np.float64) * 0.5

    # Add some texture variation (simulating tissue)
    rng = np.random.RandomState(42)
    texture = gaussian_filter(rng.randn(size, size), sigma=10) * 0.05
    brain_img += texture * brain

    # White matter regions (slightly brighter)
    wm = ((x / 0.4) ** 2 + (y / 0.5) ** 2) < 1.0
    brain_img += wm.astype(np.float64) * 0.15

    # Inject an anomaly (hyperintense region)
    anomaly_cx, anomaly_cy = 0.25, -0.15
    anomaly_r = 0.12
    anomaly = ((x - anomaly_cx) ** 2 + (y - anomaly_cy) ** 2) < anomaly_r**2
    brain_img += anomaly.astype(np.float64) * 0.35

    # Clip to valid range
    brain_img = np.clip(brain_img, 0, 1)

    # Run detection
    mask = detect_anomalies_image_processing(brain_img, sensitivity)

    findings = extract_findings_from_mask(
        mask, threshold=max(0.1, 0.5 - sensitivity * 0.4)
    )

    heatmap_png = mask_to_heatmap_png(mask, alpha_scale=0.7)
    overlay_b64 = heatmap_to_base64(heatmap_png)

    processing_time_ms = int((time.time() - start_time) * 1000)

    return {
        "status": "completed",
        "analysis_type": analysis_type,
        "processing_time_ms": processing_time_ms,
        "findings": [f.to_dict() for f in findings],
        "overlay": {
            "type": "heatmap",
            "data": overlay_b64,
            "width": size,
            "height": size,
            "colormap": "jet",
        },
        "summary": generate_summary(findings),
    }
