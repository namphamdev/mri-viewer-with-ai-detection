"""Convert detection results to overlay masks, heatmaps, and findings."""

import base64
import io
import logging
import uuid
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Jet-like colormap lookup table (256 entries, RGBA)
# Simplified jet colormap: blue -> cyan -> green -> yellow -> red
_JET_LUT: np.ndarray | None = None


def _get_jet_lut() -> np.ndarray:
    """Build a 256-entry jet colormap lookup table (RGBA, uint8)."""
    global _JET_LUT
    if _JET_LUT is not None:
        return _JET_LUT

    lut = np.zeros((256, 4), dtype=np.uint8)
    for i in range(256):
        t = i / 255.0
        # Simplified jet colormap
        if t < 0.125:
            r, g, b = 0.0, 0.0, 0.5 + t * 4.0
        elif t < 0.375:
            r, g, b = 0.0, (t - 0.125) * 4.0, 1.0
        elif t < 0.625:
            r, g, b = (t - 0.375) * 4.0, 1.0, 1.0 - (t - 0.375) * 4.0
        elif t < 0.875:
            r, g, b = 1.0, 1.0 - (t - 0.625) * 4.0, 0.0
        else:
            r, g, b = 1.0 - (t - 0.875) * 4.0, 0.0, 0.0

        lut[i] = [
            int(np.clip(r, 0, 1) * 255),
            int(np.clip(g, 0, 1) * 255),
            int(np.clip(b, 0, 1) * 255),
            255,  # Alpha set later based on mask intensity
        ]

    _JET_LUT = lut
    return _JET_LUT


@dataclass
class Finding:
    """A single detected anomaly finding."""

    finding_id: str = field(default_factory=lambda: f"finding-{uuid.uuid4().hex[:8]}")
    finding_type: str = "anomaly"
    description: str = ""
    confidence: float = 0.0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    severity: str = "low"

    def to_dict(self) -> dict:
        return {
            "id": self.finding_id,
            "type": self.finding_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "location": {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height,
            },
            "severity": self.severity,
        }


def mask_to_heatmap_png(
    mask: np.ndarray,
    alpha_scale: float = 0.7,
) -> bytes:
    """Convert a float mask (0-1) to a colored heatmap PNG with transparency.

    Args:
        mask: 2D float array in 0-1 range (detection probability).
        alpha_scale: Maximum alpha for the overlay (0-1).

    Returns:
        PNG bytes (RGBA) suitable for overlaying on the original image.
    """
    h, w = mask.shape
    lut = _get_jet_lut()

    # Map mask values to colormap indices
    indices = (np.clip(mask, 0, 1) * 255).astype(np.uint8)

    # Apply colormap
    rgba = lut[indices.ravel()].reshape(h, w, 4).copy()

    # Set alpha based on mask intensity (low values = transparent)
    alpha = (np.clip(mask, 0, 1) * alpha_scale * 255).astype(np.uint8)
    rgba[:, :, 3] = alpha

    image = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def heatmap_to_base64(png_bytes: bytes) -> str:
    """Encode PNG bytes as base64 string."""
    return base64.b64encode(png_bytes).decode("ascii")


def extract_findings_from_mask(
    mask: np.ndarray,
    threshold: float = 0.3,
) -> list[Finding]:
    """Extract individual findings (bounding boxes) from a detection mask.

    Uses connected component labeling on the thresholded mask.

    Args:
        mask: 2D float array in 0-1 range.
        threshold: Minimum value to consider as a detection.

    Returns:
        List of Finding objects with bounding boxes and confidence scores.
    """
    from scipy import ndimage

    binary = mask > threshold
    labeled, num_features = ndimage.label(binary)

    findings = []
    for i in range(1, num_features + 1):
        region = labeled == i
        region_mask = mask * region

        # Bounding box
        rows = np.any(region, axis=1)
        cols = np.any(region, axis=0)
        if not rows.any() or not cols.any():
            continue
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Confidence = mean intensity in the region
        confidence = float(region_mask[region].mean())
        peak = float(region_mask.max())
        area = int(region.sum())

        # Severity based on confidence and area
        if peak > 0.8 and area > 100:
            severity = "high"
        elif peak > 0.5 or area > 50:
            severity = "moderate"
        else:
            severity = "low"

        # Description based on characteristics
        desc = _describe_finding(confidence, area, severity)

        findings.append(
            Finding(
                description=desc,
                confidence=confidence,
                x=int(cmin),
                y=int(rmin),
                width=int(cmax - cmin + 1),
                height=int(rmax - rmin + 1),
                severity=severity,
            )
        )

    # Sort by confidence descending
    findings.sort(key=lambda f: f.confidence, reverse=True)

    return findings


def _describe_finding(confidence: float, area: int, severity: str) -> str:
    """Generate a human-readable description for a finding."""
    if severity == "high":
        return "Hyperintense region detected with significant deviation from normal tissue"
    elif severity == "moderate":
        return "Hyperintense region detected"
    else:
        return "Subtle intensity variation detected"


def generate_summary(findings: list[Finding], regions_analyzed: int = 1) -> dict:
    """Generate a summary of all findings."""
    if not findings:
        return {
            "total_findings": 0,
            "max_confidence": 0.0,
            "regions_analyzed": regions_analyzed,
            "recommendation": "No significant anomalies detected.",
        }

    max_conf = max(f.confidence for f in findings)
    has_high = any(f.severity == "high" for f in findings)
    has_moderate = any(f.severity == "moderate" for f in findings)

    if has_high:
        rec = "Significant regions of interest detected. Urgent clinical review recommended."
    elif has_moderate:
        rec = "Regions of interest detected. Clinical review recommended."
    else:
        rec = "Minor variations detected. Routine follow-up may be sufficient."

    return {
        "total_findings": len(findings),
        "max_confidence": round(max_conf, 3),
        "regions_analyzed": regions_analyzed,
        "recommendation": rec,
    }
