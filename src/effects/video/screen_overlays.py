"""
Screen sharing overlay effects for DiscordOpus.

Provides basic overlays for screen sharing: watermarks, borders, and cursor highlighting.
These are simpler than full video effects, optimized for screen sharing performance.

Classes:
    ScreenOverlay: Base class for screen overlays
    WatermarkOverlay: Text or image watermarks
    BorderOverlay: Frame border around screen capture
    CursorHighlight: Cursor position highlighting
    ScreenOverlayManager: Manages multiple overlays
"""

import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional, List

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ScreenOverlay(ABC):
    """
    Base class for screen sharing overlays.

    All screen overlays implement this interface for consistent processing.
    """

    def __init__(self):
        """Initialize the overlay."""
        self.enabled: bool = True

    @abstractmethod
    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply overlay to frame.

        Args:
            frame: Input frame (RGB numpy array)

        Returns:
            Frame with overlay applied
        """
        pass


class WatermarkOverlay(ScreenOverlay):
    """
    Watermark overlay for screen sharing.

    Supports text watermarks or image watermarks with configurable position
    and opacity. Useful for branding or attribution during screen shares.

    Examples:
        >>> # Text watermark
        >>> overlay = WatermarkOverlay(text="DiscordOpus")
        >>> overlay.set_text("My Name", font_size=20, color=(255, 255, 255))

        >>> # Image watermark
        >>> overlay = WatermarkOverlay(image_path="logo.png")
        >>> overlay.set_image("logo.png", max_size=80)
    """

    def __init__(
        self,
        text: Optional[str] = None,
        image_path: Optional[str] = None,
        position: str = "bottom_right"
    ):
        """
        Initialize watermark overlay.

        Args:
            text: Text watermark content (mutually exclusive with image_path)
            image_path: Path to image watermark (mutually exclusive with text)
            position: Watermark position ("top_left", "top_right", "bottom_left",
                     "bottom_right", "center")
        """
        super().__init__()
        self.text: Optional[str] = text
        self.font_size: int = 24
        self.opacity: float = 0.5
        self.color: Tuple[int, int, int] = (255, 255, 255)
        self.image: Optional[np.ndarray] = None
        self.position: str = position

        # Load image if provided
        if image_path:
            self.set_image(image_path)

    def set_text(
        self,
        text: str,
        font_size: int = 24,
        color: Tuple[int, int, int] = (255, 255, 255)
    ):
        """
        Configure text watermark.

        Args:
            text: Watermark text
            font_size: Font size (10-72)
            color: RGB color tuple
        """
        self.text = text
        self.font_size = max(10, min(72, font_size))
        self.color = color
        self.image = None  # Clear image watermark
        logger.debug(f"Text watermark set: '{text}' (size={font_size})")

    def set_image(self, image_path: str, max_size: int = 100):
        """
        Load and configure image watermark.

        Args:
            image_path: Path to watermark image
            max_size: Maximum width/height in pixels (preserves aspect ratio)
        """
        try:
            # Load image with alpha channel if available
            img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

            if img is None:
                logger.error(f"Failed to load watermark image: {image_path}")
                return

            # Resize to max_size while preserving aspect ratio
            h, w = img.shape[:2]
            scale = min(max_size / w, max_size / h)

            if scale < 1.0:
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Convert to RGB if no alpha channel
            if img.shape[2] == 3:
                self.image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                # Has alpha channel - convert BGRA to RGBA
                self.image = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)

            self.text = None  # Clear text watermark
            logger.info(f"Image watermark loaded: {image_path} ({img.shape[1]}x{img.shape[0]})")

        except Exception as e:
            logger.error(f"Error loading watermark image: {e}")

    def _calculate_position(
        self,
        frame_size: Tuple[int, int],
        overlay_size: Tuple[int, int],
        position: str,
        padding: int = 10
    ) -> Tuple[int, int]:
        """
        Calculate overlay position coordinates.

        Args:
            frame_size: (width, height) of frame
            overlay_size: (width, height) of overlay
            position: Position string
            padding: Padding from edges in pixels

        Returns:
            (x, y) coordinates for top-left corner of overlay
        """
        frame_w, frame_h = frame_size
        overlay_w, overlay_h = overlay_size

        if position == "top_left":
            return (padding, padding)
        elif position == "top_right":
            return (frame_w - overlay_w - padding, padding)
        elif position == "bottom_left":
            return (padding, frame_h - overlay_h - padding)
        elif position == "bottom_right":
            return (frame_w - overlay_w - padding, frame_h - overlay_h - padding)
        elif position == "center":
            return ((frame_w - overlay_w) // 2, (frame_h - overlay_h) // 2)
        else:
            # Default to bottom_right
            return (frame_w - overlay_w - padding, frame_h - overlay_h - padding)

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply watermark to frame.

        Args:
            frame: Input RGB frame

        Returns:
            Frame with watermark overlay
        """
        if not self.enabled:
            return frame

        if self.text:
            # Text watermark
            return self._apply_text_watermark(frame)
        elif self.image is not None:
            # Image watermark
            return self._apply_image_watermark(frame)
        else:
            # No watermark configured
            return frame

    def _apply_text_watermark(self, frame: np.ndarray) -> np.ndarray:
        """Apply text watermark to frame."""
        # Create a copy to avoid modifying original
        result = frame.copy()

        # Calculate text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = self.font_size / 30.0  # Scale factor for size
        thickness = max(1, int(font_scale * 2))

        (text_w, text_h), baseline = cv2.getTextSize(
            self.text, font, font_scale, thickness
        )

        # Add some padding to text size
        text_h += baseline

        # Calculate position
        frame_h, frame_w = frame.shape[:2]
        x, y = self._calculate_position(
            (frame_w, frame_h),
            (text_w, text_h),
            self.position
        )

        # Adjust y for text baseline
        y += text_h - baseline

        # Create overlay with text
        overlay = result.copy()
        cv2.putText(
            overlay,
            self.text,
            (x, y),
            font,
            font_scale,
            self.color,
            thickness,
            cv2.LINE_AA
        )

        # Blend with opacity
        cv2.addWeighted(overlay, self.opacity, result, 1 - self.opacity, 0, result)

        return result

    def _apply_image_watermark(self, frame: np.ndarray) -> np.ndarray:
        """Apply image watermark to frame."""
        # Create a copy to avoid modifying original
        result = frame.copy()

        # Calculate position
        frame_h, frame_w = frame.shape[:2]
        wm_h, wm_w = self.image.shape[:2]
        x, y = self._calculate_position(
            (frame_w, frame_h),
            (wm_w, wm_h),
            self.position
        )

        # Ensure watermark fits in frame
        if x < 0 or y < 0 or x + wm_w > frame_w or y + wm_h > frame_h:
            logger.warning("Watermark doesn't fit in frame, skipping")
            return result

        # Extract region of interest
        roi = result[y:y+wm_h, x:x+wm_w]

        # Handle alpha channel if present
        if self.image.shape[2] == 4:
            # RGBA image - use alpha channel for blending
            wm_rgb = self.image[:, :, :3]
            alpha = self.image[:, :, 3] / 255.0 * self.opacity
            alpha = alpha[:, :, np.newaxis]

            # Blend using alpha
            blended = (wm_rgb * alpha + roi * (1 - alpha)).astype(np.uint8)
        else:
            # RGB image - use opacity for blending
            blended = cv2.addWeighted(self.image, self.opacity, roi, 1 - self.opacity, 0)

        # Place blended region back
        result[y:y+wm_h, x:x+wm_w] = blended

        return result


class BorderOverlay(ScreenOverlay):
    """
    Border/frame overlay for screen sharing.

    Draws a border around the shared screen. Useful for highlighting
    the screen share or providing visual separation.

    Examples:
        >>> # Simple solid border
        >>> overlay = BorderOverlay(color=(0, 120, 255), thickness=3)

        >>> # Rounded border
        >>> overlay = BorderOverlay(style="rounded", corner_radius=20)
    """

    def __init__(
        self,
        color: Tuple[int, int, int] = (0, 120, 255),
        thickness: int = 3
    ):
        """
        Initialize border overlay.

        Args:
            color: RGB border color (default: blue)
            thickness: Border thickness in pixels (1-20)
        """
        super().__init__()
        self.color: Tuple[int, int, int] = color
        self.thickness: int = max(1, min(20, thickness))
        self.style: str = "solid"
        self.corner_radius: int = 10

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply border to frame.

        Args:
            frame: Input RGB frame

        Returns:
            Frame with border overlay
        """
        if not self.enabled:
            return frame

        # Create a copy to avoid modifying original
        result = frame.copy()

        h, w = frame.shape[:2]

        if self.style == "rounded":
            # Draw rounded rectangle border
            # Note: cv2.rectangle doesn't support rounded corners directly
            # We'll use a simple approximation with circles at corners

            radius = min(self.corner_radius, min(w, h) // 4)
            half_thick = self.thickness // 2

            # Draw the four sides
            cv2.line(result, (radius, half_thick), (w - radius, half_thick),
                    self.color, self.thickness)  # Top
            cv2.line(result, (radius, h - half_thick), (w - radius, h - half_thick),
                    self.color, self.thickness)  # Bottom
            cv2.line(result, (half_thick, radius), (half_thick, h - radius),
                    self.color, self.thickness)  # Left
            cv2.line(result, (w - half_thick, radius), (w - half_thick, h - radius),
                    self.color, self.thickness)  # Right

            # Draw rounded corners
            cv2.ellipse(result, (radius, radius), (radius, radius),
                       180, 0, 90, self.color, self.thickness)  # Top-left
            cv2.ellipse(result, (w - radius, radius), (radius, radius),
                       270, 0, 90, self.color, self.thickness)  # Top-right
            cv2.ellipse(result, (radius, h - radius), (radius, radius),
                       90, 0, 90, self.color, self.thickness)  # Bottom-left
            cv2.ellipse(result, (w - radius, h - radius), (radius, radius),
                       0, 0, 90, self.color, self.thickness)  # Bottom-right
        else:
            # Simple solid border
            half_thick = self.thickness // 2
            cv2.rectangle(
                result,
                (half_thick, half_thick),
                (w - half_thick, h - half_thick),
                self.color,
                self.thickness
            )

        return result


class CursorHighlight(ScreenOverlay):
    """
    Cursor position highlighting for screen sharing.

    Highlights the cursor position with a circle, spotlight, or ring effect.
    Helps viewers follow the presenter's cursor during screen shares.

    Note: Cursor position must be provided externally as mss doesn't capture
    cursor position. Use pyautogui.position() or similar to track cursor.

    Examples:
        >>> overlay = CursorHighlight(style="circle")
        >>> overlay.set_cursor_position(100, 200)
        >>> frame = overlay.process(frame)
    """

    def __init__(
        self,
        color: Tuple[int, int, int] = (255, 255, 0),
        radius: int = 30,
        style: str = "circle"
    ):
        """
        Initialize cursor highlight overlay.

        Args:
            color: RGB highlight color (default: yellow)
            radius: Highlight radius in pixels
            style: Highlight style ("circle", "spotlight", "ring")
        """
        super().__init__()
        self.color: Tuple[int, int, int] = color
        self.radius: int = radius
        self.opacity: float = 0.5
        self.style: str = style
        self.click_flash: bool = False

        # Cursor position (None until set)
        self._cursor_x: Optional[int] = None
        self._cursor_y: Optional[int] = None

    def set_cursor_position(self, x: int, y: int):
        """
        Update cursor position.

        Args:
            x: Cursor x coordinate
            y: Cursor y coordinate
        """
        self._cursor_x = x
        self._cursor_y = y

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply cursor highlight to frame.

        Args:
            frame: Input RGB frame

        Returns:
            Frame with cursor highlight
        """
        if not self.enabled or self._cursor_x is None or self._cursor_y is None:
            return frame

        # Create a copy to avoid modifying original
        result = frame.copy()
        h, w = frame.shape[:2]

        # Ensure cursor is within frame bounds
        if not (0 <= self._cursor_x < w and 0 <= self._cursor_y < h):
            return result

        # Create overlay
        overlay = result.copy()

        if self.style == "circle":
            # Filled circle with opacity
            cv2.circle(
                overlay,
                (self._cursor_x, self._cursor_y),
                self.radius,
                self.color,
                -1  # Filled
            )
        elif self.style == "ring":
            # Ring (hollow circle)
            thickness = max(2, self.radius // 10)
            cv2.circle(
                overlay,
                (self._cursor_x, self._cursor_y),
                self.radius,
                self.color,
                thickness
            )
        elif self.style == "spotlight":
            # Gradient spotlight effect (simple version using circle)
            # For a true spotlight, we'd use radial gradient
            cv2.circle(
                overlay,
                (self._cursor_x, self._cursor_y),
                self.radius,
                self.color,
                -1
            )
            # Draw a brighter inner circle
            cv2.circle(
                overlay,
                (self._cursor_x, self._cursor_y),
                self.radius // 2,
                (255, 255, 255),
                -1
            )

        # Blend with opacity
        cv2.addWeighted(overlay, self.opacity, result, 1 - self.opacity, 0, result)

        return result


class ScreenOverlayManager:
    """
    Manages multiple screen overlays.

    Applies overlays in order and provides preset configurations for
    common screen sharing scenarios.

    Examples:
        >>> manager = ScreenOverlayManager()
        >>> manager.add_overlay(WatermarkOverlay(text="My Stream"))
        >>> manager.add_overlay(BorderOverlay())
        >>> frame = manager.process(frame)
    """

    def __init__(self):
        """Initialize overlay manager."""
        self.overlays: List[ScreenOverlay] = []
        logger.debug("ScreenOverlayManager initialized")

    def add_overlay(self, overlay: ScreenOverlay):
        """
        Add overlay to processing chain.

        Args:
            overlay: Overlay instance to add
        """
        self.overlays.append(overlay)
        logger.debug(f"Added overlay: {overlay.__class__.__name__}")

    def remove_overlay(self, overlay_type: type):
        """
        Remove all overlays of specified type.

        Args:
            overlay_type: Overlay class to remove
        """
        before_count = len(self.overlays)
        self.overlays = [o for o in self.overlays if not isinstance(o, overlay_type)]
        removed = before_count - len(self.overlays)
        if removed > 0:
            logger.debug(f"Removed {removed} {overlay_type.__name__} overlay(s)")

    def clear_overlays(self):
        """Remove all overlays."""
        self.overlays.clear()
        logger.debug("Cleared all overlays")

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply all enabled overlays to frame.

        Args:
            frame: Input RGB frame

        Returns:
            Frame with all overlays applied
        """
        result = frame
        for overlay in self.overlays:
            if overlay.enabled:
                result = overlay.process(result)
        return result

    @classmethod
    def create_preset(cls, preset_name: str) -> 'ScreenOverlayManager':
        """
        Create manager with preset overlay configuration.

        Args:
            preset_name: Preset name ("presentation", "branded", "minimal")

        Returns:
            Configured ScreenOverlayManager

        Examples:
            >>> manager = ScreenOverlayManager.create_preset("presentation")
        """
        manager = cls()

        if preset_name == "presentation":
            # Border + cursor highlight for presentations
            manager.add_overlay(BorderOverlay(color=(0, 120, 255), thickness=3))
            manager.add_overlay(CursorHighlight(color=(255, 255, 0), radius=30))
        elif preset_name == "branded":
            # Watermark for branded content
            manager.add_overlay(WatermarkOverlay(text="DiscordOpus", position="bottom_right"))
        elif preset_name == "minimal":
            # Just a subtle border
            manager.add_overlay(BorderOverlay(color=(200, 200, 200), thickness=1))

        logger.info(f"Created preset overlay manager: {preset_name}")
        return manager
