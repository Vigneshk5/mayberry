"""
Device detection and configuration for Apple Silicon MPS, CUDA, and CPU.
"""

import os

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import torch


def get_device() -> str:
    """Detect and return the best available compute device."""
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_device_info() -> dict:
    """Return detailed device information."""
    device = get_device()
    info = {
        "device": device,
        "mps_available": torch.backends.mps.is_available(),
        "cuda_available": torch.cuda.is_available(),
    }
    if device == "cuda":
        info["cuda_device_name"] = torch.cuda.get_device_name(0)
    return info
