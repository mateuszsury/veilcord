"""
Creative video filters for artistic effects.

Provides vintage, cartoon, color grading, and vignette effects
using OpenCV for real-time video processing in DiscordOpus.

Classes:
    VintageFilter: Sepia/retro look with faded colors
    CartoonFilter: Comic book/cartoon effect with edge detection
    ColorGradingFilter: LUT-based color adjustments (warm, cool, dramatic, etc.)
    VignetteFilter: Darkened corners for cinematic look

Constants:
    CREATIVE_PRESETS: Dictionary of preset filter combinations
"""

import logging
from typing import Dict, Any, Optional, Tuple

import cv2
import numpy as np

from .beauty_filters import VideoEffect

logger = logging.getLogger(__name__)


class VintageFilter(VideoEffect):
    """
    Vintage/retro filter with sepia and faded look.

    Creates classic vintage photo effect using LUT-based
    transformation for sepia tones and raised blacks for
    a faded appearance.

    Attributes:
        intensity: Effect strength (0.0 to 1.0)
        style: "sepia" or "faded"
    """

    def __init__(
        self,
        intensity: float = 0.7,
        style: str = "sepia",
        enabled: bool = True
    ):
        """
        Initialize vintage filter.

        Args:
            intensity: Effect intensity (0.0 to 1.0)
            style: "sepia" or "faded"
            enabled: Whether effect is active
        """
        super().__init__("Vintage Filter", intensity, enabled)
        self.style = style
        self._sepia_lut = self._create_sepia_lut()
        self._faded_lut = self._create_faded_lut()

    def _create_sepia_lut(self) -> np.ndarray:
        """
        Create sepia tone transformation matrix.

        Classic sepia transformation that converts RGB to
        warm brown tones.

        Returns:
            3x3 transformation matrix
        """
        # Classic sepia transformation matrix
        return np.array([
            [0.272, 0.534, 0.131],  # Blue channel
            [0.349, 0.686, 0.168],  # Green channel
            [0.393, 0.769, 0.189]   # Red channel
        ], dtype=np.float32)

    def _create_faded_lut(self) -> np.ndarray:
        """
        Create faded/washed out look transformation.

        Raises blacks and slightly desaturates for
        vintage faded photo effect.

        Returns:
            256-element lookup table
        """
        # Raise blacks (add offset to shadows)
        lut = np.arange(256, dtype=np.float32)
        lut = lut * 0.85 + 30  # Scale down and lift shadows
        lut = np.clip(lut, 0, 255).astype(np.uint8)
        return lut

    def _apply_sepia(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply sepia tone effect.

        Args:
            frame: Input BGR image

        Returns:
            Sepia-toned BGR image
        """
        # Convert BGR to RGB for transformation
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Apply sepia transformation
        sepia = cv2.transform(rgb, self._sepia_lut)

        # Clip values and convert back to BGR
        sepia = np.clip(sepia, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(sepia, cv2.COLOR_RGB2BGR)

        return result

    def _apply_faded(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply faded/washed out effect.

        Args:
            frame: Input BGR image

        Returns:
            Faded BGR image
        """
        # Apply LUT to each channel
        result = cv2.LUT(frame, self._faded_lut)

        # Slightly desaturate
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = (hsv[:, :, 1] * 0.7).astype(np.uint8)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return result

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with vintage filter.

        Args:
            frame: Input BGR image

        Returns:
            Vintage-styled BGR image
        """
        if not self.enabled or frame is None or self.intensity == 0.0:
            return frame

        try:
            # Apply selected style
            if self.style == "sepia":
                filtered = self._apply_sepia(frame)
            elif self.style == "faded":
                filtered = self._apply_faded(frame)
            else:
                filtered = self._apply_sepia(frame)

            # Blend with original based on intensity
            result = cv2.addWeighted(
                frame, 1.0 - self.intensity,
                filtered, self.intensity,
                0
            )

            return result
        except Exception as e:
            logger.error(f"Vintage filter failed: {e}")
            return frame

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = super().to_dict()
        data["style"] = self.style
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VintageFilter":
        """Deserialize from dictionary."""
        return cls(
            intensity=data.get("intensity", 0.7),
            style=data.get("style", "sepia"),
            enabled=data.get("enabled", True)
        )


class CartoonFilter(VideoEffect):
    """
    Cartoon/comic book effect.

    Creates stylized cartoon look using edge detection
    and color quantization (palette reduction).

    Attributes:
        intensity: Effect strength (0.0 to 1.0)
        num_colors: Number of colors in quantized palette
        edge_thickness: Thickness of detected edges
    """

    def __init__(
        self,
        intensity: float = 0.8,
        num_colors: int = 8,
        edge_thickness: int = 1,
        enabled: bool = True
    ):
        """
        Initialize cartoon filter.

        Args:
            intensity: Effect intensity (0.0 to 1.0)
            num_colors: Colors in palette (fewer = more stylized)
            edge_thickness: Edge outline weight (1-3)
            enabled: Whether effect is active
        """
        super().__init__("Cartoon Filter", intensity, enabled)
        self.num_colors = max(2, min(16, num_colors))
        self.edge_thickness = max(1, min(3, edge_thickness))

    def _detect_edges(self, frame: np.ndarray) -> np.ndarray:
        """
        Detect edges using adaptive thresholding.

        Args:
            frame: Input BGR image

        Returns:
            Binary edge map (0 or 255)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply median blur to reduce noise
        gray = cv2.medianBlur(gray, 5)

        # Adaptive threshold for edge detection
        edges = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            blockSize=9,
            C=2
        )

        # Dilate edges if thickness > 1
        if self.edge_thickness > 1:
            kernel = np.ones((self.edge_thickness, self.edge_thickness), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)

        return edges

    def _quantize_colors(self, frame: np.ndarray) -> np.ndarray:
        """
        Reduce color palette using k-means clustering.

        Args:
            frame: Input BGR image

        Returns:
            Color-quantized BGR image
        """
        # Reshape to pixel array
        h, w = frame.shape[:2]
        pixels = frame.reshape((-1, 3)).astype(np.float32)

        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels,
            self.num_colors,
            None,
            criteria,
            attempts=3,
            flags=cv2.KMEANS_PP_CENTERS
        )

        # Convert back to uint8
        centers = centers.astype(np.uint8)
        quantized = centers[labels.flatten()]

        # Reshape to original image dimensions
        result = quantized.reshape((h, w, 3))

        return result

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with cartoon filter.

        Args:
            frame: Input BGR image

        Returns:
            Cartoon-styled BGR image
        """
        if not self.enabled or frame is None or self.intensity == 0.0:
            return frame

        try:
            # Detect edges
            edges = self._detect_edges(frame)

            # Quantize colors
            quantized = self._quantize_colors(frame)

            # Apply bilateral filter for smoother cartoon look
            quantized = cv2.bilateralFilter(quantized, 9, 75, 75)

            # Convert edges to BGR
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

            # Combine quantized colors with edges (edges darken the image)
            cartoon = cv2.bitwise_and(quantized, edges_bgr)

            # Blend with original based on intensity
            result = cv2.addWeighted(
                frame, 1.0 - self.intensity,
                cartoon, self.intensity,
                0
            )

            return result
        except Exception as e:
            logger.error(f"Cartoon filter failed: {e}")
            return frame

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = super().to_dict()
        data["num_colors"] = self.num_colors
        data["edge_thickness"] = self.edge_thickness
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CartoonFilter":
        """Deserialize from dictionary."""
        return cls(
            intensity=data.get("intensity", 0.8),
            num_colors=data.get("num_colors", 8),
            edge_thickness=data.get("edge_thickness", 1),
            enabled=data.get("enabled", True)
        )


class ColorGradingFilter(VideoEffect):
    """
    LUT-based color grading filter.

    Provides preset color grades (warm, cool, dramatic, etc.)
    and custom adjustments for temperature, tint, saturation,
    and contrast.

    Attributes:
        intensity: Effect strength (0.0 to 1.0)
        preset: Selected preset name or "custom"
    """

    PRESETS = {
        "warm": {"temperature": 20, "tint": 0, "saturation": 1.1, "contrast": 1.0},
        "cool": {"temperature": -20, "tint": 0, "saturation": 1.0, "contrast": 1.0},
        "dramatic": {"temperature": 0, "tint": 0, "saturation": 1.2, "contrast": 1.3},
        "soft": {"temperature": 5, "tint": 5, "saturation": 0.9, "contrast": 0.8},
        "vibrant": {"temperature": 0, "tint": 0, "saturation": 1.4, "contrast": 1.05},
    }

    def __init__(
        self,
        intensity: float = 0.7,
        preset: str = "warm",
        enabled: bool = True
    ):
        """
        Initialize color grading filter.

        Args:
            intensity: Effect intensity (0.0 to 1.0)
            preset: Preset name ("warm", "cool", "dramatic", "soft", "vibrant")
            enabled: Whether effect is active
        """
        super().__init__("Color Grading", intensity, enabled)
        self.preset = preset if preset in self.PRESETS else "warm"
        self._temperature = 0
        self._tint = 0
        self._saturation = 1.0
        self._contrast = 1.0
        self.set_preset(self.preset)

    def set_preset(self, name: str):
        """
        Apply a color grading preset.

        Args:
            name: Preset name
        """
        if name in self.PRESETS:
            self.preset = name
            params = self.PRESETS[name]
            self._temperature = params["temperature"]
            self._tint = params["tint"]
            self._saturation = params["saturation"]
            self._contrast = params["contrast"]

    def custom_adjustments(
        self,
        temperature: float = 0,
        tint: float = 0,
        saturation: float = 1.0,
        contrast: float = 1.0
    ):
        """
        Set custom color grading adjustments.

        Args:
            temperature: Color temperature (-50 to 50, negative=cool, positive=warm)
            tint: Color tint (-50 to 50, negative=green, positive=magenta)
            saturation: Saturation multiplier (0.0 to 2.0)
            contrast: Contrast multiplier (0.5 to 2.0)
        """
        self.preset = "custom"
        self._temperature = max(-50, min(50, temperature))
        self._tint = max(-50, min(50, tint))
        self._saturation = max(0.0, min(2.0, saturation))
        self._contrast = max(0.5, min(2.0, contrast))

    def _adjust_temperature(self, frame: np.ndarray) -> np.ndarray:
        """
        Adjust color temperature.

        Args:
            frame: Input BGR image

        Returns:
            Temperature-adjusted BGR image
        """
        if self._temperature == 0:
            return frame

        result = frame.copy().astype(np.float32)

        # Positive = warmer (increase red, decrease blue)
        # Negative = cooler (decrease red, increase blue)
        if self._temperature > 0:
            result[:, :, 2] = np.clip(result[:, :, 2] + self._temperature, 0, 255)  # Red
            result[:, :, 0] = np.clip(result[:, :, 0] - self._temperature * 0.5, 0, 255)  # Blue
        else:
            result[:, :, 0] = np.clip(result[:, :, 0] - self._temperature, 0, 255)  # Blue
            result[:, :, 2] = np.clip(result[:, :, 2] + self._temperature * 0.5, 0, 255)  # Red

        return result.astype(np.uint8)

    def _adjust_tint(self, frame: np.ndarray) -> np.ndarray:
        """
        Adjust color tint (green-magenta).

        Args:
            frame: Input BGR image

        Returns:
            Tint-adjusted BGR image
        """
        if self._tint == 0:
            return frame

        result = frame.copy().astype(np.float32)

        # Positive = magenta (increase red and blue)
        # Negative = green (increase green)
        if self._tint > 0:
            result[:, :, 2] = np.clip(result[:, :, 2] + self._tint * 0.5, 0, 255)  # Red
            result[:, :, 0] = np.clip(result[:, :, 0] + self._tint * 0.5, 0, 255)  # Blue
        else:
            result[:, :, 1] = np.clip(result[:, :, 1] - self._tint, 0, 255)  # Green

        return result.astype(np.uint8)

    def _adjust_saturation(self, frame: np.ndarray) -> np.ndarray:
        """
        Adjust color saturation.

        Args:
            frame: Input BGR image

        Returns:
            Saturation-adjusted BGR image
        """
        if self._saturation == 1.0:
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self._saturation, 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        return result

    def _adjust_contrast(self, frame: np.ndarray) -> np.ndarray:
        """
        Adjust contrast.

        Args:
            frame: Input BGR image

        Returns:
            Contrast-adjusted BGR image
        """
        if self._contrast == 1.0:
            return frame

        # Apply contrast around midpoint (127)
        result = frame.astype(np.float32)
        result = ((result - 127.5) * self._contrast) + 127.5
        result = np.clip(result, 0, 255).astype(np.uint8)

        return result

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with color grading.

        Args:
            frame: Input BGR image

        Returns:
            Color-graded BGR image
        """
        if not self.enabled or frame is None or self.intensity == 0.0:
            return frame

        try:
            # Apply adjustments
            result = self._adjust_temperature(frame)
            result = self._adjust_tint(result)
            result = self._adjust_saturation(result)
            result = self._adjust_contrast(result)

            # Blend with original based on intensity
            result = cv2.addWeighted(
                frame, 1.0 - self.intensity,
                result, self.intensity,
                0
            )

            return result
        except Exception as e:
            logger.error(f"Color grading failed: {e}")
            return frame

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = super().to_dict()
        data.update({
            "preset": self.preset,
            "temperature": self._temperature,
            "tint": self._tint,
            "saturation": self._saturation,
            "contrast": self._contrast,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorGradingFilter":
        """Deserialize from dictionary."""
        filter_obj = cls(
            intensity=data.get("intensity", 0.7),
            preset=data.get("preset", "warm"),
            enabled=data.get("enabled", True)
        )
        if data.get("preset") == "custom":
            filter_obj.custom_adjustments(
                temperature=data.get("temperature", 0),
                tint=data.get("tint", 0),
                saturation=data.get("saturation", 1.0),
                contrast=data.get("contrast", 1.0)
            )
        return filter_obj


class VignetteFilter(VideoEffect):
    """
    Vignette effect (darkened corners).

    Creates cinematic look by darkening edges and corners
    of the frame while keeping center bright.

    Attributes:
        intensity: Effect strength (0.0 to 1.0)
        strength: Darkness of vignette (0.0 to 1.0)
        radius: Size of vignette (0.5 to 1.5)
    """

    def __init__(
        self,
        intensity: float = 0.6,
        strength: float = 0.5,
        radius: float = 1.0,
        enabled: bool = True
    ):
        """
        Initialize vignette filter.

        Args:
            intensity: Effect intensity (0.0 to 1.0)
            strength: Darkness of corners (0.0 to 1.0)
            radius: Vignette size (0.5 to 1.5, larger = more center brightness)
            enabled: Whether effect is active
        """
        super().__init__("Vignette", intensity, enabled)
        self.strength = max(0.0, min(1.0, strength))
        self.radius = max(0.5, min(1.5, radius))
        self._cached_mask: Optional[np.ndarray] = None
        self._cached_dimensions: Optional[Tuple[int, int]] = None

    def _create_vignette_mask(self, width: int, height: int) -> np.ndarray:
        """
        Create vignette mask (radial gradient from center).

        Args:
            width: Frame width
            height: Frame height

        Returns:
            Vignette mask (0.0 to 1.0)
        """
        # Check cache
        if (self._cached_mask is not None and
            self._cached_dimensions == (width, height)):
            return self._cached_mask

        # Create coordinate grid
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)

        # Calculate distance from center
        distance = np.sqrt(X**2 + Y**2)

        # Apply radius scaling
        distance = distance / self.radius

        # Create radial gradient (1.0 at center, 0.0 at edges)
        mask = 1.0 - np.clip(distance, 0, 1)

        # Apply strength (controls how dark the edges get)
        mask = mask ** (1.0 / (self.strength + 0.1))  # Power curve for smooth falloff

        # Expand to 3 channels
        mask = np.repeat(mask[:, :, np.newaxis], 3, axis=2)

        # Cache the mask
        self._cached_mask = mask.astype(np.float32)
        self._cached_dimensions = (width, height)

        return self._cached_mask

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process frame with vignette effect.

        Args:
            frame: Input BGR image

        Returns:
            Vignetted BGR image
        """
        if not self.enabled or frame is None or self.intensity == 0.0:
            return frame

        try:
            h, w = frame.shape[:2]

            # Get vignette mask
            mask = self._create_vignette_mask(w, h)

            # Apply vignette
            vignetted = (frame.astype(np.float32) * mask).astype(np.uint8)

            # Blend with original based on intensity
            result = cv2.addWeighted(
                frame, 1.0 - self.intensity,
                vignetted, self.intensity,
                0
            )

            return result
        except Exception as e:
            logger.error(f"Vignette filter failed: {e}")
            return frame

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = super().to_dict()
        data.update({
            "strength": self.strength,
            "radius": self.radius,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VignetteFilter":
        """Deserialize from dictionary."""
        return cls(
            intensity=data.get("intensity", 0.6),
            strength=data.get("strength", 0.5),
            radius=data.get("radius", 1.0),
            enabled=data.get("enabled", True)
        )


# Preset filter combinations
CREATIVE_PRESETS: Dict[str, Dict[str, Any]] = {
    "vintage_warm": {
        "filters": [
            {"type": "VintageFilter", "intensity": 0.7, "style": "sepia"},
            {"type": "ColorGradingFilter", "intensity": 0.5, "preset": "warm"},
            {"type": "VignetteFilter", "intensity": 0.4, "strength": 0.3, "radius": 1.2},
        ],
        "description": "Warm vintage look with sepia tones and subtle vignette"
    },
    "vintage_cool": {
        "filters": [
            {"type": "VintageFilter", "intensity": 0.6, "style": "faded"},
            {"type": "ColorGradingFilter", "intensity": 0.5, "preset": "cool"},
            {"type": "VignetteFilter", "intensity": 0.5, "strength": 0.4, "radius": 1.0},
        ],
        "description": "Cool vintage look with faded colors and vignette"
    },
    "cartoon": {
        "filters": [
            {"type": "CartoonFilter", "intensity": 0.8, "num_colors": 8, "edge_thickness": 1},
        ],
        "description": "Comic book/cartoon effect with edge detection"
    },
    "dramatic": {
        "filters": [
            {"type": "ColorGradingFilter", "intensity": 0.7, "preset": "dramatic"},
            {"type": "VignetteFilter", "intensity": 0.6, "strength": 0.6, "radius": 0.9},
        ],
        "description": "High contrast dramatic look with strong vignette"
    },
    "soft_glow": {
        "filters": [
            {"type": "ColorGradingFilter", "intensity": 0.6, "preset": "soft"},
        ],
        "description": "Soft, dreamy look with reduced contrast"
    },
    "vibrant": {
        "filters": [
            {"type": "ColorGradingFilter", "intensity": 0.7, "preset": "vibrant"},
        ],
        "description": "Highly saturated vibrant colors"
    },
}
