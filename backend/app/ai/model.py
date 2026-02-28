"""AI model loading and inference.

Provides a U-Net model stub for future real model integration.
Falls back to image-processing approach when no weights are available.
"""

import logging
import os
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Path where model weights would be stored
MODEL_WEIGHTS_DIR = Path(__file__).parent / "weights"
UNET_WEIGHTS_FILE = MODEL_WEIGHTS_DIR / "unet_brain_mri.pt"

# Flag for PyTorch availability
_torch_available = False
try:
    import torch
    import torch.nn as nn

    _torch_available = True
except ImportError:
    logger.info("PyTorch not available — using image-processing fallback only")


def is_torch_available() -> bool:
    """Check if PyTorch is installed."""
    return _torch_available


if _torch_available:
    import torch
    import torch.nn as nn

    class DoubleConv(nn.Module):
        """Two consecutive conv-bn-relu blocks."""

        def __init__(self, in_ch: int, out_ch: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    class UNet(nn.Module):
        """Minimal U-Net for brain MRI segmentation.

        Input:  (B, 1, 256, 256) grayscale
        Output: (B, 1, 256, 256) probability mask
        """

        def __init__(self):
            super().__init__()
            # Encoder
            self.enc1 = DoubleConv(1, 32)
            self.enc2 = DoubleConv(32, 64)
            self.enc3 = DoubleConv(64, 128)

            # Bottleneck
            self.bottleneck = DoubleConv(128, 256)

            # Decoder
            self.up3 = nn.ConvTranspose2d(256, 128, 2, stride=2)
            self.dec3 = DoubleConv(256, 128)
            self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
            self.dec2 = DoubleConv(128, 64)
            self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
            self.dec1 = DoubleConv(64, 32)

            self.pool = nn.MaxPool2d(2)
            self.out_conv = nn.Conv2d(32, 1, 1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # Encoder
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool(e1))
            e3 = self.enc3(self.pool(e2))

            # Bottleneck
            b = self.bottleneck(self.pool(e3))

            # Decoder with skip connections
            d3 = self.dec3(torch.cat([self.up3(b), e3], dim=1))
            d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
            d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

            return torch.sigmoid(self.out_conv(d1))


def load_model():
    """Load the U-Net model with pre-trained weights if available.

    Returns:
        The model in eval mode if weights exist, else None.
    """
    if not _torch_available:
        logger.info("PyTorch not available, model loading skipped")
        return None

    if not UNET_WEIGHTS_FILE.exists():
        logger.info(
            "No model weights found at %s — using image-processing fallback",
            UNET_WEIGHTS_FILE,
        )
        return None

    try:
        model = UNet()
        state_dict = torch.load(UNET_WEIGHTS_FILE, map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()
        logger.info("U-Net model loaded from %s", UNET_WEIGHTS_FILE)
        return model
    except Exception as e:
        logger.error("Failed to load U-Net model: %s", e)
        return None


def predict_with_model(model, image: np.ndarray) -> np.ndarray:
    """Run inference on a preprocessed image using the U-Net model.

    Args:
        model: Loaded U-Net model.
        image: Preprocessed 2D float array (256x256), range 0-1.

    Returns:
        Probability mask as 2D float array (256x256), range 0-1.
    """
    if not _torch_available or model is None:
        raise RuntimeError("Model not available")

    import torch

    # Convert to tensor: (1, 1, H, W)
    tensor = torch.from_numpy(image).float().unsqueeze(0).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)

    # Convert back to numpy: (H, W)
    return output.squeeze().cpu().numpy()
