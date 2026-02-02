"""
AR face overlays using MediaPipe face landmarks.

Provides Snapchat/Instagram-style face filters with real-time tracking:
- Glasses and sunglasses (positioned over eyes)
- Hats and crowns (positioned above head)
- Masks (covers face)
- Face filters (dog, cat face replacements)
- Custom overlays with configurable anchor points

Overlays automatically rotate and scale with head movement.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Dict
from pathlib import Path

import numpy as np
import cv2

from .face_tracker import FaceTracker, FaceLandmarks

logger = logging.getLogger(__name__)


# Helper functions to avoid circular imports with FaceTracker
def _get_eye_distance(landmarks: FaceLandmarks) -> float:
    """Calculate distance between eye centers in pixels."""
    try:
        left_eye = landmarks.get_landmark(FaceLandmarks.LEFT_EYE_CENTER)
        right_eye = landmarks.get_landmark(FaceLandmarks.RIGHT_EYE_CENTER)

        distance = np.sqrt(
            (right_eye[0] - left_eye[0]) ** 2 +
            (right_eye[1] - left_eye[1]) ** 2
        )
        return float(distance)
    except (IndexError, ValueError) as e:
        logger.error(f"Error calculating eye distance: {e}")
        return 100.0  # Default fallback


def _get_face_angle(landmarks: FaceLandmarks) -> Tuple[float, float, float]:
    """Estimate face rotation angles (yaw, pitch, roll) from landmarks."""
    try:
        left_eye = np.array(landmarks.get_landmark(FaceLandmarks.LEFT_EYE_CENTER))
        right_eye = np.array(landmarks.get_landmark(FaceLandmarks.RIGHT_EYE_CENTER))

        # Calculate roll (head tilt left/right)
        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        roll = np.degrees(np.arctan2(dy, dx))

        return (0.0, 0.0, float(roll))  # Simplified - only roll matters for overlays
    except (IndexError, ValueError) as e:
        logger.error(f"Error calculating face angle: {e}")
        return (0.0, 0.0, 0.0)


class OverlayType(Enum):
    """Types of AR overlays."""
    GLASSES = "glasses"
    SUNGLASSES = "sunglasses"
    HAT = "hat"
    MASK = "mask"
    FACE_FILTER = "face_filter"
    MUSTACHE = "mustache"
    EARS = "ears"
    CUSTOM = "custom"


@dataclass
class OverlayAnchor:
    """
    Configuration for positioning an overlay on the face.

    Attributes:
        primary_landmark: Main anchor point (MediaPipe landmark index)
        secondary_landmark: Reference point for scale/rotation
        offset_x: Normalized horizontal offset from primary (-1.0 to 1.0)
        offset_y: Normalized vertical offset from primary (-1.0 to 1.0)
        scale_factor: Multiplier for eye distance (base scale unit)
    """
    primary_landmark: int
    secondary_landmark: int
    offset_x: float = 0.0
    offset_y: float = 0.0
    scale_factor: float = 1.0


# Pre-defined anchor configurations for each overlay type
OVERLAY_ANCHORS: Dict[OverlayType, OverlayAnchor] = {
    OverlayType.GLASSES: OverlayAnchor(
        primary_landmark=33,  # Left eye center
        secondary_landmark=263,  # Right eye center
        offset_x=0.0,
        offset_y=-0.05,  # Slightly above eyes
        scale_factor=2.2  # ~2.2x eye distance for standard glasses
    ),
    OverlayType.SUNGLASSES: OverlayAnchor(
        primary_landmark=33,
        secondary_landmark=263,
        offset_x=0.0,
        offset_y=-0.05,
        scale_factor=2.4  # Slightly larger than regular glasses
    ),
    OverlayType.HAT: OverlayAnchor(
        primary_landmark=10,  # Forehead
        secondary_landmark=152,  # Chin (for scale reference)
        offset_x=0.0,
        offset_y=-0.3,  # Above head
        scale_factor=1.8  # Scale based on face height
    ),
    OverlayType.MASK: OverlayAnchor(
        primary_landmark=1,  # Nose tip
        secondary_landmark=152,  # Chin
        offset_x=0.0,
        offset_y=0.0,
        scale_factor=1.5  # Cover upper face
    ),
    OverlayType.FACE_FILTER: OverlayAnchor(
        primary_landmark=1,  # Nose tip (center of face)
        secondary_landmark=152,  # Chin
        offset_x=0.0,
        offset_y=0.0,
        scale_factor=2.5  # Full face coverage
    ),
    OverlayType.MUSTACHE: OverlayAnchor(
        primary_landmark=13,  # Upper lip
        secondary_landmark=14,  # Lower lip
        offset_x=0.0,
        offset_y=0.05,  # Slightly below nose
        scale_factor=0.8  # Smaller than glasses
    ),
    OverlayType.EARS: OverlayAnchor(
        primary_landmark=10,  # Forehead (centered above head)
        secondary_landmark=152,  # Chin
        offset_x=0.0,
        offset_y=-0.4,  # Above head
        scale_factor=1.5
    ),
}


class AROverlay:
    """
    AR overlay that tracks and composites onto face using landmarks.

    Handles loading, positioning, scaling, rotation, and alpha blending
    of overlay images onto video frames.

    Usage:
        overlay = AROverlay(OverlayType.GLASSES, "assets/overlays/round_glasses.png")
        result_frame = overlay.apply(frame, landmarks)
    """

    def __init__(
        self,
        overlay_type: OverlayType,
        image_path: Optional[str] = None,
        anchor: Optional[OverlayAnchor] = None
    ):
        """
        Initialize AR overlay.

        Args:
            overlay_type: Type of overlay
            image_path: Path to PNG image with alpha channel (if None, uses placeholder)
            anchor: Custom anchor configuration (if None, uses default for type)
        """
        self.overlay_type = overlay_type
        self.image_path = image_path

        # Load overlay image (BGRA with alpha)
        if image_path and os.path.exists(image_path):
            self.image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if self.image is None:
                logger.error(f"Failed to load overlay image: {image_path}")
                self.image = self._create_placeholder()
            elif self.image.shape[2] != 4:
                logger.warning(f"Overlay image lacks alpha channel: {image_path}")
                # Add alpha channel
                self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2BGRA)
        else:
            if image_path:
                logger.warning(f"Overlay image not found: {image_path}, using placeholder")
            self.image = self._create_placeholder()

        # Use custom anchor or default for type
        self.anchor = anchor if anchor else OVERLAY_ANCHORS.get(
            overlay_type,
            OverlayAnchor(primary_landmark=1, secondary_landmark=152)
        )

        # Overlay state
        self.enabled = True
        self.scale = 1.0  # Additional scale adjustment (0.5 - 2.0)
        self.offset = (0.0, 0.0)  # Additional position offset (normalized)

    def _create_placeholder(self) -> np.ndarray:
        """
        Create a placeholder overlay for testing without assets.

        Returns:
            BGRA image with simple colored shape
        """
        size = 512
        placeholder = np.zeros((size, size, 4), dtype=np.uint8)

        # Different shapes/colors for different types
        if self.overlay_type == OverlayType.GLASSES:
            # Two circles for glasses
            cv2.circle(placeholder, (150, 256), 100, (255, 200, 150, 200), -1)
            cv2.circle(placeholder, (362, 256), 100, (255, 200, 150, 200), -1)
            # Bridge
            cv2.rectangle(placeholder, (250, 246), (262, 266), (255, 200, 150, 200), -1)
        elif self.overlay_type == OverlayType.HAT:
            # Triangle for hat
            pts = np.array([[256, 100], [150, 400], [362, 400]], np.int32)
            cv2.fillPoly(placeholder, [pts], (200, 50, 50, 200))
        elif self.overlay_type == OverlayType.MASK:
            # Oval for mask
            cv2.ellipse(placeholder, (256, 256), (200, 150), 0, 0, 360, (150, 50, 200, 200), -1)
        else:
            # Generic circle
            cv2.circle(placeholder, (256, 256), 200, (100, 100, 255, 200), -1)

        logger.debug(f"Created placeholder for {self.overlay_type}")
        return placeholder

    def _calculate_transform(
        self,
        landmarks: FaceLandmarks
    ) -> Tuple[Tuple[int, int], float, float]:
        """
        Calculate position, scale, and rotation for overlay.

        Args:
            landmarks: Face landmarks

        Returns:
            Tuple of (position, scale, rotation):
                - position: (x, y) pixel coordinates for overlay center
                - scale: Scale factor for overlay
                - rotation: Rotation angle in degrees
        """
        try:
            # Get anchor points
            primary = landmarks.get_landmark(self.anchor.primary_landmark)
            secondary = landmarks.get_landmark(self.anchor.secondary_landmark)

            # Calculate base scale from eye distance (using helper function)
            eye_distance = _get_eye_distance(landmarks)
            base_scale = eye_distance * self.anchor.scale_factor * self.scale

            # Calculate rotation from face angle (using helper function)
            _, _, roll = _get_face_angle(landmarks)

            # Calculate position (midpoint between primary and secondary)
            center_x = (primary[0] + secondary[0]) // 2
            center_y = (primary[1] + secondary[1]) // 2

            # Apply anchor offsets (scaled by eye distance)
            offset_x_pixels = int(self.anchor.offset_x * eye_distance)
            offset_y_pixels = int(self.anchor.offset_y * eye_distance)

            # Apply additional user offsets
            offset_x_pixels += int(self.offset[0] * eye_distance)
            offset_y_pixels += int(self.offset[1] * eye_distance)

            position = (center_x + offset_x_pixels, center_y + offset_y_pixels)

            return position, base_scale, roll

        except Exception as e:
            logger.error(f"Error calculating transform: {e}")
            # Return safe defaults
            return (0, 0), 1.0, 0.0

    def apply(self, frame: np.ndarray, landmarks: FaceLandmarks) -> np.ndarray:
        """
        Apply overlay to frame using face landmarks.

        Args:
            frame: BGR image (OpenCV format)
            landmarks: Face landmarks from FaceTracker

        Returns:
            Frame with overlay composited (BGR format)
        """
        if not self.enabled:
            return frame

        try:
            # Calculate transform
            position, scale, rotation = self._calculate_transform(landmarks)

            # Resize overlay
            overlay_height, overlay_width = self.image.shape[:2]
            new_width = int(overlay_width * scale / overlay_width)
            new_height = int(overlay_height * scale / overlay_width)

            if new_width <= 0 or new_height <= 0:
                return frame

            resized_overlay = cv2.resize(
                self.image,
                (new_width, new_height),
                interpolation=cv2.INTER_LINEAR
            )

            # Rotate overlay
            if abs(rotation) > 0.5:  # Only rotate if significant
                rotated_overlay = self._rotate_image(resized_overlay, rotation)
            else:
                rotated_overlay = resized_overlay

            # Alpha blend onto frame
            result = self._alpha_blend(frame, rotated_overlay, position[0], position[1])

            return result

        except Exception as e:
            logger.error(f"Error applying overlay: {e}")
            return frame

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotate image around its center, preserving alpha channel.

        Args:
            image: BGRA image
            angle: Rotation angle in degrees (counter-clockwise)

        Returns:
            Rotated BGRA image
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)

        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new image size to contain rotated image
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        # Adjust rotation matrix for new size
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]

        # Rotate with alpha channel
        rotated = cv2.warpAffine(
            image,
            M,
            (new_w, new_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0)
        )

        return rotated

    def _alpha_blend(
        self,
        frame: np.ndarray,
        overlay: np.ndarray,
        x: int,
        y: int
    ) -> np.ndarray:
        """
        Alpha blend overlay onto frame at specified position.

        Handles overlay extending beyond frame bounds.

        Args:
            frame: BGR background image
            overlay: BGRA overlay image
            x: X coordinate for overlay center
            y: Y coordinate for overlay center

        Returns:
            Composited BGR frame
        """
        overlay_h, overlay_w = overlay.shape[:2]
        frame_h, frame_w = frame.shape[:2]

        # Calculate overlay top-left position
        x1 = x - overlay_w // 2
        y1 = y - overlay_h // 2
        x2 = x1 + overlay_w
        y2 = y1 + overlay_h

        # Clip to frame bounds
        frame_x1 = max(0, x1)
        frame_y1 = max(0, y1)
        frame_x2 = min(frame_w, x2)
        frame_y2 = min(frame_h, y2)

        # Calculate corresponding overlay region
        overlay_x1 = frame_x1 - x1
        overlay_y1 = frame_y1 - y1
        overlay_x2 = overlay_x1 + (frame_x2 - frame_x1)
        overlay_y2 = overlay_y1 + (frame_y2 - frame_y1)

        # Check if overlay is completely outside frame
        if frame_x2 <= frame_x1 or frame_y2 <= frame_y1:
            return frame

        # Extract regions
        frame_region = frame[frame_y1:frame_y2, frame_x1:frame_x2]
        overlay_region = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2]

        # Separate alpha channel
        overlay_bgr = overlay_region[:, :, :3]
        alpha = overlay_region[:, :, 3:4] / 255.0  # Normalize to 0-1

        # Alpha blend
        blended = (overlay_bgr * alpha + frame_region * (1 - alpha)).astype(np.uint8)

        # Copy result back to frame
        result = frame.copy()
        result[frame_y1:frame_y2, frame_x1:frame_x2] = blended

        return result

    def to_dict(self) -> dict:
        """Serialize overlay configuration to dict."""
        return {
            "type": self.overlay_type.value,
            "image_path": self.image_path,
            "enabled": self.enabled,
            "scale": self.scale,
            "offset": self.offset,
            "anchor": {
                "primary_landmark": self.anchor.primary_landmark,
                "secondary_landmark": self.anchor.secondary_landmark,
                "offset_x": self.anchor.offset_x,
                "offset_y": self.anchor.offset_y,
                "scale_factor": self.anchor.scale_factor,
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AROverlay":
        """Deserialize overlay from dict."""
        overlay_type = OverlayType(data["type"])
        anchor = OverlayAnchor(**data["anchor"])

        overlay = cls(
            overlay_type=overlay_type,
            image_path=data.get("image_path"),
            anchor=anchor
        )

        overlay.enabled = data.get("enabled", True)
        overlay.scale = data.get("scale", 1.0)
        overlay.offset = tuple(data.get("offset", (0.0, 0.0)))

        return overlay


# Specialized overlay classes
class GlassesOverlay(AROverlay):
    """
    Specialized overlay for glasses positioned over eyes.

    Uses left/right eye landmarks for precise positioning and
    adjusts for face tilt.
    """

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.GLASSES,
            image_path=image_path
        )


class SunglassesOverlay(AROverlay):
    """Sunglasses variant - slightly larger than regular glasses."""

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.SUNGLASSES,
            image_path=image_path
        )


class HatOverlay(AROverlay):
    """
    Hat overlay positioned above forehead.

    Scales based on face width and stays above head during movement.
    """

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.HAT,
            image_path=image_path
        )


class MaskOverlay(AROverlay):
    """
    Mask overlay covering upper face (eyes + nose area).

    Handles partial face occlusion.
    """

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.MASK,
            image_path=image_path
        )


class FaceFilterOverlay(AROverlay):
    """
    Full face replacement filter (dog, cat face, etc.).

    Uses mesh warping for more complex face transformations.
    """

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.FACE_FILTER,
            image_path=image_path
        )


class MustacheOverlay(AROverlay):
    """Mustache overlay positioned below nose."""

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.MUSTACHE,
            image_path=image_path
        )


class EarsOverlay(AROverlay):
    """Animal ears overlay positioned above head."""

    def __init__(self, image_path: Optional[str] = None):
        super().__init__(
            overlay_type=OverlayType.EARS,
            image_path=image_path
        )


class AROverlayManager:
    """
    Manager for multiple AR overlays with face tracking.

    Handles applying multiple overlays to video frames using shared
    face tracking. Supports presets and configuration serialization.

    Usage:
        manager = AROverlayManager(face_tracker)
        manager.add_overlay(GlassesOverlay())
        result = manager.process(frame)
    """

    def __init__(self, face_tracker: Optional[FaceTracker] = None):
        """
        Initialize overlay manager.

        Args:
            face_tracker: Shared FaceTracker instance (if None, creates new one)
        """
        self.face_tracker = face_tracker if face_tracker else FaceTracker(max_faces=1)
        self.overlays: List[AROverlay] = []

    def add_overlay(self, overlay: AROverlay):
        """
        Add overlay to active list.

        Args:
            overlay: AROverlay instance to add
        """
        self.overlays.append(overlay)
        logger.info(f"Added overlay: {overlay.overlay_type}")

    def remove_overlay(self, overlay_type: OverlayType):
        """
        Remove all overlays of given type.

        Args:
            overlay_type: Type of overlay to remove
        """
        initial_count = len(self.overlays)
        self.overlays = [o for o in self.overlays if o.overlay_type != overlay_type]
        removed_count = initial_count - len(self.overlays)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} overlay(s) of type {overlay_type}")

    def clear_overlays(self):
        """Remove all overlays."""
        self.overlays.clear()
        logger.info("Cleared all overlays")

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply all enabled overlays to frame.

        Args:
            frame: BGR image (OpenCV format)

        Returns:
            Frame with overlays composited
        """
        if not self.overlays:
            return frame

        # Get face landmarks
        landmarks = self.face_tracker.process(frame)

        if landmarks is None:
            # No face detected - return original frame
            return frame

        # Apply each enabled overlay in order
        result = frame
        for overlay in self.overlays:
            if overlay.enabled:
                result = overlay.apply(result, landmarks)

        return result

    def set_single_overlay(self, overlay: AROverlay):
        """
        Clear existing overlays and set single overlay.

        Args:
            overlay: AROverlay to set as only active overlay
        """
        self.clear_overlays()
        self.add_overlay(overlay)

    def to_dict(self) -> dict:
        """Serialize manager configuration to dict."""
        return {
            "overlays": [overlay.to_dict() for overlay in self.overlays]
        }

    @classmethod
    def from_dict(cls, data: dict, face_tracker: Optional[FaceTracker] = None) -> "AROverlayManager":
        """
        Deserialize manager from dict.

        Args:
            data: Serialized configuration
            face_tracker: Shared FaceTracker instance

        Returns:
            AROverlayManager instance
        """
        manager = cls(face_tracker)

        for overlay_data in data.get("overlays", []):
            overlay = AROverlay.from_dict(overlay_data)
            manager.add_overlay(overlay)

        return manager

    def close(self):
        """Release resources."""
        if self.face_tracker:
            self.face_tracker.close()
            self.face_tracker = None

        self.overlays.clear()
        logger.info("AROverlayManager closed")


# Built-in overlay presets (paths relative to assets/overlays/)
BUILT_IN_OVERLAYS: Dict[str, AROverlay] = {
    "glasses_round": GlassesOverlay(),  # Uses placeholder for now
    "glasses_aviator": GlassesOverlay(),
    "sunglasses_black": SunglassesOverlay(),
    "party_hat": HatOverlay(),
    "crown": HatOverlay(),
    "mask_venetian": MaskOverlay(),
    "cat_ears": EarsOverlay(),
    "dog_filter": FaceFilterOverlay(),
}


def create_placeholder_overlay(overlay_type: OverlayType) -> AROverlay:
    """
    Create overlay with placeholder image for testing.

    Used when actual overlay assets aren't available.

    Args:
        overlay_type: Type of overlay to create

    Returns:
        AROverlay with placeholder image
    """
    return AROverlay(overlay_type=overlay_type, image_path=None)
