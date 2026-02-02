"""
Beauty filters for video enhancement.

Provides skin smoothing and lighting correction effects using OpenCV
for real-time video processing in DiscordOpus video calls.

Classes:
    VideoEffect: Base class for all video effects
    BeautyFilter: Skin smoothing filter using bilateral filtering
    LightingCorrection: Lighting enhancement using CLAHE
    CombinedBeautyFilter: Combines beauty and lighting effects
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoEffect(ABC):
    """
    Base class for all video effects.

    Provides common interface for video processing effects with
    intensity controls and serialization support.

    Attributes:
        name: Human-readable effect name
        enabled: Whether the effect is currently active
        intensity: Effect intensity from 0.0 (none) to 1.0 (full)
    """

    def __init__(self, name: str, intensity: float = 0.5, enabled: bool = True):
        """
        Initialize video effect.

        Args:
            name: Effect name
            intensity: Effect intensity (0.0 to 1.0)
            enabled: Whether effect is active
        """
        self._name = name
        self._enabled = enabled
        self._intensity = max(0.0, min(1.0, intensity))

    @property
    def name(self) -> str:
        """Get effect name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Get whether effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Set whether effect is enabled."""
        self._enabled = value

    @property
    def intensity(self) -> float:
        """Get effect intensity (0.0 to 1.0)."""
        return self._intensity

    @intensity.setter
    def intensity(self, value: float):
        """Set effect intensity (0.0 to 1.0)."""
        self._intensity = max(0.0, min(1.0, value))

    @abstractmethod
    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a video frame with this effect.

        Args:
            frame: Input BGR image

        Returns:
            Processed BGR image
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize effect to dictionary.

        Returns:
            Dictionary with effect configuration
        """
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "enabled": self.enabled,
            "intensity": self.intensity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VideoEffect":
        """
        Deserialize effect from dictionary.

        Args:
            data: Dictionary with effect configuration

        Returns:
            VideoEffect instance
        """
        return cls(
            intensity=data.get("intensity", 0.5),
            enabled=data.get("enabled", True)
        )


class BeautyFilter(VideoEffect):
    """
    Skin smoothing beauty filter.

    Uses bilateral filtering to smooth skin while preserving edges
    (like facial features). Works in LAB color space for better
    skin tone handling.

    The filter applies edge-preserving smoothing that reduces
    blemishes and texture while keeping important facial details sharp.

    Attributes:
        intensity: Smoothing strength (0.0 to 1.0)
    """

    def __init__(self, intensity: float = 0.5, enabled: bool = True):
        """
        Initialize beauty filter.

        Args:
            intensity: Smoothing intensity (0.0 to 1.0)
            enabled: Whether effect is active
        """
        super().__init__("Beauty Filter", intensity, enabled)

    def smooth_skin(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply skin smoothing to frame.

        Uses bilateral filter in LAB color space to smooth skin
        while preserving edges and important facial features.

        Args:
            frame: Input BGR image

        Returns:
            Smoothed BGR image
        """
        if self.intensity == 0.0:
            return frame

        # Convert to LAB color space (better for skin tones)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Calculate bilateral filter parameters based on intensity
        # Higher intensity = more smoothing
        d = 5 + int(4 * self.intensity)  # Diameter: 5-9
        sigma_color = 50 + int(50 * self.intensity)  # Color similarity: 50-100
        sigma_space = 50 + int(50 * self.intensity)  # Spatial distance: 50-100

        # Apply bilateral filter to L channel (preserves edges)
        l_smoothed = cv2.bilateralFilter(l_channel, d, sigma_color, sigma_space)

        # Blend original and smoothed based on intensity
        l_blended = cv2.addWeighted(
            l_channel, 1.0 - self.intensity,
            l_smoothed, self.intensity,
            0
        )

        # Merge channels and convert back to BGR
        lab_smoothed = cv2.merge([l_blended, a_channel, b_channel])
        result = cv2.cvtColor(lab_smoothed, cv2.COLOR_LAB2BGR)

        return result

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with beauty filter.

        Args:
            frame: Input BGR image

        Returns:
            Beautified BGR image
        """
        if not self.enabled or frame is None:
            return frame

        try:
            return self.smooth_skin(frame)
        except Exception as e:
            logger.error(f"Beauty filter processing failed: {e}")
            return frame


class LightingCorrection(VideoEffect):
    """
    Lighting correction filter.

    Improves appearance in poor lighting conditions using:
    - CLAHE (Contrast Limited Adaptive Histogram Equalization) for better contrast
    - Optional automatic white balance for color correction

    Particularly useful for dark or unevenly lit environments.

    Attributes:
        intensity: Correction strength (0.0 to 1.0)
        auto_white_balance_enabled: Whether to apply white balance
    """

    def __init__(
        self,
        intensity: float = 0.5,
        auto_white_balance_enabled: bool = False,
        enabled: bool = True
    ):
        """
        Initialize lighting correction.

        Args:
            intensity: Correction intensity (0.0 to 1.0)
            auto_white_balance_enabled: Whether to apply white balance
            enabled: Whether effect is active
        """
        super().__init__("Lighting Correction", intensity, enabled)
        self.auto_white_balance_enabled = auto_white_balance_enabled

    def correct_lighting(self, frame: np.ndarray) -> np.ndarray:
        """
        Correct lighting using CLAHE.

        Applies Contrast Limited Adaptive Histogram Equalization
        to improve visibility in dark or poorly lit conditions.

        Args:
            frame: Input BGR image

        Returns:
            Lighting-corrected BGR image
        """
        if self.intensity == 0.0:
            return frame

        # Convert to HSV for value channel processing
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h_channel, s_channel, v_channel = cv2.split(hsv)

        # Create CLAHE object with intensity-based parameters
        clip_limit = 1.5 + (1.5 * self.intensity)  # 1.5 to 3.0
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))

        # Apply CLAHE to V channel
        v_corrected = clahe.apply(v_channel)

        # Blend original and corrected based on intensity
        v_blended = cv2.addWeighted(
            v_channel, 1.0 - self.intensity,
            v_corrected, self.intensity,
            0
        )

        # Merge channels and convert back to BGR
        hsv_corrected = cv2.merge([h_channel, s_channel, v_blended])
        result = cv2.cvtColor(hsv_corrected, cv2.COLOR_HSV2BGR)

        return result

    def auto_white_balance(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply automatic white balance.

        Uses simple gray world assumption to normalize color channels.

        Args:
            frame: Input BGR image

        Returns:
            White-balanced BGR image
        """
        # Calculate average for each channel
        avg_b = np.mean(frame[:, :, 0])
        avg_g = np.mean(frame[:, :, 1])
        avg_r = np.mean(frame[:, :, 2])

        # Calculate gray (average of all channels)
        gray = (avg_b + avg_g + avg_r) / 3.0

        # Avoid division by zero
        if avg_b == 0 or avg_g == 0 or avg_r == 0:
            return frame

        # Calculate scaling factors
        scale_b = gray / avg_b
        scale_g = gray / avg_g
        scale_r = gray / avg_r

        # Apply scaling
        result = frame.copy()
        result[:, :, 0] = np.clip(frame[:, :, 0] * scale_b, 0, 255).astype(np.uint8)
        result[:, :, 1] = np.clip(frame[:, :, 1] * scale_g, 0, 255).astype(np.uint8)
        result[:, :, 2] = np.clip(frame[:, :, 2] * scale_r, 0, 255).astype(np.uint8)

        return result

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with lighting correction.

        Args:
            frame: Input BGR image

        Returns:
            Lighting-corrected BGR image
        """
        if not self.enabled or frame is None:
            return frame

        try:
            result = self.correct_lighting(frame)

            if self.auto_white_balance_enabled:
                result = self.auto_white_balance(result)

            return result
        except Exception as e:
            logger.error(f"Lighting correction failed: {e}")
            return frame

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = super().to_dict()
        data["auto_white_balance_enabled"] = self.auto_white_balance_enabled
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LightingCorrection":
        """Deserialize from dictionary."""
        return cls(
            intensity=data.get("intensity", 0.5),
            auto_white_balance_enabled=data.get("auto_white_balance_enabled", False),
            enabled=data.get("enabled", True)
        )


class CombinedBeautyFilter(VideoEffect):
    """
    Combined beauty and lighting correction filter.

    Convenience class that applies both skin smoothing and lighting
    correction with a single intensity control.

    This is the most commonly used beauty filter preset, providing
    a natural-looking enhancement for video calls.

    Attributes:
        intensity: Overall enhancement strength (0.0 to 1.0)
        beauty_filter: BeautyFilter instance
        lighting_correction: LightingCorrection instance
    """

    def __init__(self, intensity: float = 0.5, enabled: bool = True):
        """
        Initialize combined beauty filter.

        Args:
            intensity: Overall enhancement intensity (0.0 to 1.0)
            enabled: Whether effect is active
        """
        super().__init__("Combined Beauty Filter", intensity, enabled)

        # Create sub-filters with same intensity
        self.beauty_filter = BeautyFilter(intensity=intensity, enabled=True)
        self.lighting_correction = LightingCorrection(intensity=intensity, enabled=True)

    @property
    def intensity(self) -> float:
        """Get effect intensity."""
        return self._intensity

    @intensity.setter
    def intensity(self, value: float):
        """Set effect intensity for all sub-filters."""
        self._intensity = max(0.0, min(1.0, value))
        self.beauty_filter.intensity = self._intensity
        self.lighting_correction.intensity = self._intensity

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with combined filters.

        Applies lighting correction first, then beauty filter
        for best results.

        Args:
            frame: Input BGR image

        Returns:
            Enhanced BGR image
        """
        if not self.enabled or frame is None:
            return frame

        try:
            # Apply lighting correction first
            result = self.lighting_correction.process(frame)

            # Then apply beauty filter
            result = self.beauty_filter.process(result)

            return result
        except Exception as e:
            logger.error(f"Combined beauty filter failed: {e}")
            return frame

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = super().to_dict()
        data["beauty_filter"] = self.beauty_filter.to_dict()
        data["lighting_correction"] = self.lighting_correction.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CombinedBeautyFilter":
        """Deserialize from dictionary."""
        return cls(
            intensity=data.get("intensity", 0.5),
            enabled=data.get("enabled", True)
        )
