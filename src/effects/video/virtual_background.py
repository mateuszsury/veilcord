"""
Virtual background effects using MediaPipe segmentation.

Provides background blur, solid color replacement, custom image backgrounds,
and animated backgrounds for video calls.
"""

import logging
from enum import Enum
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass

import cv2
import numpy as np

from .segmentation import BackgroundSegmenter

logger = logging.getLogger(__name__)


class BackgroundType(Enum):
    """Virtual background effect types."""
    NONE = "none"
    BLUR = "blur"
    COLOR = "color"
    IMAGE = "image"
    ANIMATED = "animated"


class AnimatedBackground:
    """
    Helper class for animated backgrounds (GIF or video loops).

    Preloads frames into memory for smooth playback without I/O latency.
    """

    def __init__(self, source: str):
        """
        Load animated background from GIF or video file.

        Args:
            source: Path to GIF or video file

        Raises:
            ValueError: If source cannot be loaded
        """
        self._frames: List[np.ndarray] = []
        self._current_index: int = 0
        self.fps: float = 30.0

        try:
            cap = cv2.VideoCapture(source)

            if not cap.isOpened():
                raise ValueError(f"Cannot open animated background: {source}")

            # Get FPS if available
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                self.fps = fps

            # Preload all frames
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                self._frames.append(frame)

            cap.release()

            if len(self._frames) == 0:
                raise ValueError(f"No frames loaded from {source}")

            logger.info(f"Loaded animated background: {len(self._frames)} frames at {self.fps} FPS")

        except Exception as e:
            logger.error(f"Failed to load animated background from {source}: {e}")
            raise

    def get_next_frame(self) -> np.ndarray:
        """
        Get next frame in animation sequence.

        Returns:
            BGR frame as numpy array (loops back to start when finished)
        """
        if not self._frames:
            # Shouldn't happen if __init__ succeeded, but be safe
            raise ValueError("No frames available in animated background")

        frame = self._frames[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._frames)
        return frame


class VirtualBackground:
    """
    Virtual background effects with blur, color, image, and animation support.

    Uses MediaPipe segmentation to separate person from background and apply effects.
    Includes edge smoothing for natural hair/clothing blending.

    Usage:
        vbg = VirtualBackground()
        vbg.set_blur(strength=50)
        output = vbg.process(frame)

    Or with existing segmenter:
        segmenter = BackgroundSegmenter()
        vbg = VirtualBackground(segmenter=segmenter)
        vbg.set_color(0, 177, 64)  # Green screen
        output = vbg.process(frame)
    """

    def __init__(self, segmenter: Optional[BackgroundSegmenter] = None):
        """
        Initialize virtual background processor.

        Args:
            segmenter: Existing BackgroundSegmenter to use (creates new one if None)
        """
        self.segmenter = segmenter if segmenter is not None else BackgroundSegmenter(model_selection=1)

        # Current effect settings
        self.mode: BackgroundType = BackgroundType.NONE
        self.enabled: bool = True

        # Effect parameters
        self.blur_strength: int = 50  # 1-100
        self.background_color: Tuple[int, int, int] = (30, 30, 40)  # BGR
        self.background_image: Optional[np.ndarray] = None
        self._animated_background: Optional[AnimatedBackground] = None
        self.edge_smoothing: float = 0.5  # 0.0-1.0, controls edge blur amount

        # Performance optimization: cache resized background
        self._cached_background: Optional[np.ndarray] = None
        self._cached_frame_size: Optional[Tuple[int, int]] = None

    def set_blur(self, strength: int = 50):
        """
        Enable background blur effect.

        Args:
            strength: Blur intensity (1-100)
                10-30: Light blur (professional)
                40-60: Medium blur (balanced)
                70-100: Heavy blur (strong privacy)
        """
        self.mode = BackgroundType.BLUR
        self.blur_strength = max(1, min(100, strength))  # Clamp to 1-100
        logger.info(f"Virtual background set to BLUR (strength={self.blur_strength})")

    def set_color(self, r: int, g: int, b: int):
        """
        Enable solid color background replacement.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        self.mode = BackgroundType.COLOR
        # Store as BGR for OpenCV
        self.background_color = (b, g, r)
        self._clear_cache()
        logger.info(f"Virtual background set to COLOR (RGB={r},{g},{b})")

    def set_image(self, image_path: str):
        """
        Enable custom image background replacement.

        Args:
            image_path: Path to background image file

        Raises:
            ValueError: If image cannot be loaded
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot load image: {image_path}")

            self.background_image = image
            self.mode = BackgroundType.IMAGE
            self._clear_cache()
            logger.info(f"Virtual background set to IMAGE ({image_path})")

        except Exception as e:
            logger.error(f"Failed to set image background: {e}")
            raise

    def set_image_from_array(self, image: np.ndarray):
        """
        Set background from numpy array directly.

        Args:
            image: BGR image as numpy array
        """
        self.background_image = image.copy()
        self.mode = BackgroundType.IMAGE
        self._clear_cache()
        logger.info("Virtual background set to IMAGE (from array)")

    def set_animated(self, source: str):
        """
        Enable animated background (GIF or video loop).

        Args:
            source: Path to GIF or video file

        Raises:
            ValueError: If source cannot be loaded
        """
        try:
            self._animated_background = AnimatedBackground(source)
            self.mode = BackgroundType.ANIMATED
            self._clear_cache()
            logger.info(f"Virtual background set to ANIMATED ({source})")

        except Exception as e:
            logger.error(f"Failed to set animated background: {e}")
            raise

    def set_builtin(self, name: str):
        """
        Apply built-in background preset by name.

        Args:
            name: Built-in background name (see BUILT_IN_BACKGROUNDS)

        Raises:
            KeyError: If name not found in BUILT_IN_BACKGROUNDS
        """
        if name not in BUILT_IN_BACKGROUNDS:
            raise KeyError(f"Unknown built-in background: {name}")

        config = BUILT_IN_BACKGROUNDS[name]
        bg_type = config["type"]

        if bg_type == "blur":
            self.set_blur(config["strength"])
        elif bg_type == "color":
            r, g, b = config["color"]
            self.set_color(r, g, b)
        elif bg_type == "image":
            try:
                self.set_image(config["path"])
            except ValueError as e:
                # Gracefully handle missing image files (for development)
                logger.warning(f"Built-in image not found: {config['path']} - {e}")
                # Fall back to solid color as placeholder
                self.set_color(30, 30, 40)

        logger.info(f"Applied built-in background: {name}")

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply virtual background effect to frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            Processed frame with virtual background applied
        """
        if self.mode == BackgroundType.NONE or not self.enabled:
            return frame

        # Get segmentation mask
        result = self.segmenter.process(frame, threshold=0.5)
        if result is None:
            logger.warning("Segmentation failed, returning original frame")
            return frame

        mask = result.mask

        # Apply edge smoothing
        smooth_mask = self._smooth_edges(mask)

        # Apply appropriate background effect
        if self.mode == BackgroundType.BLUR:
            return self._apply_blur(frame, smooth_mask)
        elif self.mode == BackgroundType.COLOR:
            return self._apply_color(frame, smooth_mask)
        elif self.mode == BackgroundType.IMAGE:
            return self._apply_image(frame, smooth_mask)
        elif self.mode == BackgroundType.ANIMATED:
            return self._apply_animated(frame, smooth_mask)
        else:
            return frame

    def _apply_blur(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply background blur effect.

        Args:
            frame: Original BGR frame
            mask: Smoothed segmentation mask (0.0-1.0 float array)

        Returns:
            Frame with blurred background
        """
        try:
            # Map blur_strength (1-100) to kernel size
            # strength=1 → kernel=17, strength=100 → kernel=95
            kernel_size = int(15 + (self.blur_strength * 0.8))

            # Ensure kernel size is odd
            if kernel_size % 2 == 0:
                kernel_size += 1

            # Create blurred version of entire frame
            blurred = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

            # Composite person on blurred background
            mask_3channel = np.stack([mask] * 3, axis=-1)
            output = (
                frame * mask_3channel +
                blurred * (1 - mask_3channel)
            ).astype(np.uint8)

            return output

        except Exception as e:
            logger.error(f"Error applying blur background: {e}")
            return frame

    def _apply_color(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply solid color background replacement.

        Args:
            frame: Original BGR frame
            mask: Smoothed segmentation mask (0.0-1.0 float array)

        Returns:
            Frame with solid color background
        """
        try:
            h, w = frame.shape[:2]

            # Create solid color background
            color_bg = np.full((h, w, 3), self.background_color, dtype=np.uint8)

            # Composite person on color background
            mask_3channel = np.stack([mask] * 3, axis=-1)
            output = (
                frame * mask_3channel +
                color_bg * (1 - mask_3channel)
            ).astype(np.uint8)

            return output

        except Exception as e:
            logger.error(f"Error applying color background: {e}")
            return frame

    def _apply_image(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply custom image background replacement.

        Args:
            frame: Original BGR frame
            mask: Smoothed segmentation mask (0.0-1.0 float array)

        Returns:
            Frame with custom image background
        """
        if self.background_image is None:
            logger.warning("No background image set, using original frame")
            return frame

        try:
            h, w = frame.shape[:2]

            # Check cache to avoid repeated resizing
            if self._cached_background is None or self._cached_frame_size != (h, w):
                # Resize background image to match frame
                self._cached_background = cv2.resize(self.background_image, (w, h))
                self._cached_frame_size = (h, w)

            # Composite person on image background
            mask_3channel = np.stack([mask] * 3, axis=-1)
            output = (
                frame * mask_3channel +
                self._cached_background * (1 - mask_3channel)
            ).astype(np.uint8)

            return output

        except Exception as e:
            logger.error(f"Error applying image background: {e}")
            return frame

    def _apply_animated(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply animated background replacement.

        Args:
            frame: Original BGR frame
            mask: Smoothed segmentation mask (0.0-1.0 float array)

        Returns:
            Frame with animated background
        """
        if self._animated_background is None:
            logger.warning("No animated background set, using original frame")
            return frame

        try:
            h, w = frame.shape[:2]

            # Get next frame from animation
            bg_frame = self._animated_background.get_next_frame()

            # Resize to match frame size
            bg_frame = cv2.resize(bg_frame, (w, h))

            # Composite person on animated background
            mask_3channel = np.stack([mask] * 3, axis=-1)
            output = (
                frame * mask_3channel +
                bg_frame * (1 - mask_3channel)
            ).astype(np.uint8)

            return output

        except Exception as e:
            logger.error(f"Error applying animated background: {e}")
            return frame

    def _smooth_edges(self, mask: np.ndarray) -> np.ndarray:
        """
        Apply edge smoothing to mask for natural blending.

        Uses Gaussian blur on mask edges to prevent harsh cutoffs
        around person (especially hair and clothing).

        Args:
            mask: Segmentation mask (0.0-1.0 float array)

        Returns:
            Smoothed mask (0.0-1.0 float array)
        """
        try:
            # Map edge_smoothing (0.0-1.0) to blur radius (1-10)
            blur_radius = int(1 + (self.edge_smoothing * 9))

            # Ensure mask is float type
            if mask.dtype != np.float32:
                mask = mask.astype(np.float32)

            # Apply Gaussian blur for soft edges
            kernel_size = blur_radius * 2 + 1  # Must be odd
            soft_mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)

            return soft_mask

        except Exception as e:
            logger.error(f"Error smoothing edges: {e}")
            return mask

    def _clear_cache(self):
        """Clear cached background (called when background changes)."""
        self._cached_background = None
        self._cached_frame_size = None

    def to_dict(self) -> dict:
        """
        Serialize virtual background settings to dictionary.

        Returns:
            Dictionary with current settings (for preset saving)
        """
        data = {
            "mode": self.mode.value,
            "enabled": self.enabled,
            "blur_strength": self.blur_strength,
            "edge_smoothing": self.edge_smoothing,
        }

        if self.mode == BackgroundType.COLOR:
            # Convert BGR to RGB for serialization
            b, g, r = self.background_color
            data["color"] = [r, g, b]

        # Note: Image and animated backgrounds are not serialized
        # (too large, rely on file paths)

        return data

    @classmethod
    def from_dict(cls, data: dict, segmenter: Optional[BackgroundSegmenter] = None) -> "VirtualBackground":
        """
        Deserialize virtual background settings from dictionary.

        Args:
            data: Dictionary with settings
            segmenter: Optional existing BackgroundSegmenter

        Returns:
            VirtualBackground instance with loaded settings
        """
        vbg = cls(segmenter=segmenter)

        vbg.enabled = data.get("enabled", True)
        vbg.blur_strength = data.get("blur_strength", 50)
        vbg.edge_smoothing = data.get("edge_smoothing", 0.5)

        mode_str = data.get("mode", "none")
        mode = BackgroundType(mode_str)

        if mode == BackgroundType.BLUR:
            vbg.set_blur(vbg.blur_strength)
        elif mode == BackgroundType.COLOR:
            color = data.get("color", [30, 30, 40])
            vbg.set_color(*color)
        elif mode == BackgroundType.NONE:
            vbg.mode = BackgroundType.NONE

        return vbg


# Built-in background presets
BUILT_IN_BACKGROUNDS: Dict[str, dict] = {
    "blur_light": {
        "type": "blur",
        "strength": 30
    },
    "blur_medium": {
        "type": "blur",
        "strength": 50
    },
    "blur_heavy": {
        "type": "blur",
        "strength": 80
    },
    "solid_dark": {
        "type": "color",
        "color": (30, 30, 40)  # RGB
    },
    "solid_green": {
        "type": "color",
        "color": (0, 177, 64)  # Green screen
    },
    "solid_blue": {
        "type": "color",
        "color": (80, 50, 30)  # Dark blue
    },
    "office": {
        "type": "image",
        "path": "assets/backgrounds/office.jpg"
    },
    "living_room": {
        "type": "image",
        "path": "assets/backgrounds/living_room.jpg"
    },
    "space": {
        "type": "image",
        "path": "assets/backgrounds/space.jpg"  # Cosmic theme!
    }
}
