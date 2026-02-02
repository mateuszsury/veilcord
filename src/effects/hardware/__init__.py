"""
Hardware detection and quality adaptation for effects processing.

Provides automatic detection of GPU/CPU capabilities and adaptive quality
preset selection for optimal performance across different hardware.
"""

from .gpu_detector import HardwareDetector
from .quality_adapter import QualityAdapter, QualityPreset
from .resource_monitor import ResourceMonitor

__all__ = [
    "HardwareDetector",
    "QualityAdapter",
    "QualityPreset",
    "ResourceMonitor",
]
