"""
Hardware detection and quality adaptation for effects processing.

Provides automatic detection of GPU/CPU capabilities and adaptive quality
preset selection for optimal performance across different hardware.
"""

from .gpu_detector import HardwareDetector

__all__ = ["HardwareDetector"]
