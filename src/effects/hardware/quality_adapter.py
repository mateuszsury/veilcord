"""
Quality preset selection based on hardware capabilities.

Automatically selects appropriate quality levels for audio/video effects
based on detected hardware (CUDA/OpenCL/CPU).
"""

import logging
from enum import Enum
from typing import Optional

from .gpu_detector import HardwareDetector

logger = logging.getLogger(__name__)


class QualityPreset(Enum):
    """
    Quality presets for audio/video effects processing.

    Presets determine which algorithms and resolution settings are used:

    - ULTRA: CUDA GPU - DeepFilterNet3, high-res segmentation (1080p)
    - HIGH: OpenCL GPU - DeepFilterNet3, medium-res segmentation (720p)
    - MEDIUM: CPU - RNNoise only, low-res segmentation (480p)
    - LOW: Minimal CPU - RNNoise only, minimal segmentation (360p)
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class QualityAdapter:
    """
    Adaptive quality preset selector based on hardware capabilities.

    Automatically selects the best quality preset for detected hardware,
    with option for manual override.

    Usage:
        adapter = QualityAdapter(HardwareDetector())
        preset = adapter.get_active_preset()  # Auto-selected or override

        if preset == QualityPreset.ULTRA:
            # Use DeepFilterNet3 on CUDA, 1080p video
        elif preset == QualityPreset.HIGH:
            # Use DeepFilterNet3 on OpenCL, 720p video
        else:
            # Use RNNoise, lower resolution video
    """

    def __init__(self, detector: HardwareDetector):
        """
        Initialize quality adapter.

        Args:
            detector: HardwareDetector instance for capability detection
        """
        self._detector = detector
        self._manual_override: Optional[QualityPreset] = None

    def auto_select(self) -> QualityPreset:
        """
        Automatically select quality preset based on detected hardware.

        Selection logic:
        - CUDA GPU → ULTRA (best quality, GPU-accelerated AI)
        - OpenCL GPU → HIGH (good quality, GPU-accelerated AI)
        - CPU only → MEDIUM (acceptable quality, lightweight AI)

        Returns:
            QualityPreset based on hardware capabilities
        """
        if self._detector.has_cuda:
            logger.info("Auto-selected ULTRA quality (CUDA GPU)")
            return QualityPreset.ULTRA
        elif self._detector.has_opencl:
            logger.info("Auto-selected HIGH quality (OpenCL GPU)")
            return QualityPreset.HIGH
        else:
            logger.info("Auto-selected MEDIUM quality (CPU only)")
            return QualityPreset.MEDIUM

    def set_manual_override(self, preset: Optional[QualityPreset]) -> None:
        """
        Set manual quality override.

        Allows user to force a specific quality level regardless of hardware.
        Useful for:
        - Reducing quality to save battery/CPU
        - Testing lower quality modes
        - Forcing higher quality if auto-detection is wrong

        Args:
            preset: Quality preset to force, or None to clear override
        """
        if preset is not None:
            logger.info("Manual quality override set: %s", preset.value)
        else:
            logger.info("Manual quality override cleared")
        self._manual_override = preset

    def get_active_preset(self) -> QualityPreset:
        """
        Get currently active quality preset.

        Returns manual override if set, otherwise auto-selected preset.

        Returns:
            Active quality preset
        """
        if self._manual_override is not None:
            return self._manual_override
        return self.auto_select()

    @property
    def is_overridden(self) -> bool:
        """True if manual override is active."""
        return self._manual_override is not None
