"""
Background segmentation using MediaPipe Selfie Segmentation.

Provides real-time person/background separation for virtual backgrounds,
background blur, and background replacement effects.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available - background segmentation will be disabled")


@dataclass
class SegmentationResult:
    """
    Container for background segmentation result.

    Attributes:
        mask: Segmentation mask as float array (0.0-1.0), same size as input
        person_mask: Boolean mask where True indicates person pixels
        background_mask: Boolean mask where True indicates background pixels
        image_width: Original image width in pixels
        image_height: Original image height in pixels
    """

    mask: np.ndarray
    person_mask: np.ndarray
    background_mask: np.ndarray
    image_width: int
    image_height: int


class BackgroundSegmenter:
    """
    Real-time background segmentation using MediaPipe Selfie Segmentation.

    Separates person from background for virtual background effects.
    Optimized for real-time performance with edge smoothing for natural compositing.

    Usage:
        segmenter = BackgroundSegmenter(model_selection=1)
        result = segmenter.process(frame, threshold=0.5)
        if result:
            # Apply blur or replacement
            output = segmenter.apply_mask(frame, result.mask, background)
        segmenter.close()
    """

    def __init__(self, model_selection: int = 1):
        """
        Initialize background segmenter.

        Args:
            model_selection: Model to use
                0 = General model (256x256) - more accurate but slower
                1 = Landscape model (144x256) - faster for video calls
        """
        self.model_selection = model_selection

        if not MEDIAPIPE_AVAILABLE:
            logger.error("Cannot initialize BackgroundSegmenter - MediaPipe not installed")
            self.segmenter = None
            return

        # Initialize MediaPipe Selfie Segmentation
        try:
            self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
            self.segmenter = self.mp_selfie_segmentation.SelfieSegmentation(
                model_selection=model_selection
            )

            model_name = "general (256x256)" if model_selection == 0 else "landscape (144x256)"
            logger.info(f"BackgroundSegmenter initialized: model={model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Selfie Segmentation: {e}")
            self.segmenter = None

        # Cache for optimization (avoid reprocessing if frame unchanged)
        self._last_frame_hash: Optional[int] = None
        self._last_result: Optional[SegmentationResult] = None

    def process(
        self,
        frame: np.ndarray,
        threshold: float = 0.5
    ) -> Optional[SegmentationResult]:
        """
        Process frame and generate segmentation mask.

        Args:
            frame: BGR image as numpy array (OpenCV format)
            threshold: Threshold for binary mask (0.0-1.0)
                Higher = more strict person detection
                Lower = more lenient (may include shadows)

        Returns:
            SegmentationResult if successful, None otherwise
        """
        if self.segmenter is None:
            return None

        try:
            h, w = frame.shape[:2]

            # Check cache (skip processing if frame unchanged)
            frame_hash = hash(frame.tobytes())
            if frame_hash == self._last_frame_hash and self._last_result is not None:
                return self._last_result

            # Convert BGR to RGB (MediaPipe requirement)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process with MediaPipe
            results = self.segmenter.process(frame_rgb)

            if results.segmentation_mask is None:
                logger.warning("No segmentation mask returned from MediaPipe")
                return None

            # Get segmentation mask (float values 0.0-1.0)
            mask = results.segmentation_mask

            # Apply threshold to create binary masks
            person_mask = mask > threshold
            background_mask = ~person_mask

            # Create result
            result = SegmentationResult(
                mask=mask,
                person_mask=person_mask,
                background_mask=background_mask,
                image_width=w,
                image_height=h
            )

            # Update cache
            self._last_frame_hash = frame_hash
            self._last_result = result

            return result

        except Exception as e:
            logger.error(f"Error processing frame in BackgroundSegmenter: {e}")
            return None

    def apply_mask(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        replacement: np.ndarray
    ) -> np.ndarray:
        """
        Composite person onto replacement background using mask.

        Args:
            frame: Original BGR frame
            mask: Segmentation mask (0.0-1.0 float array)
            replacement: Replacement background (same size as frame)

        Returns:
            Composited image with person on new background
        """
        try:
            h, w = frame.shape[:2]

            # Ensure replacement is correct size
            if replacement.shape[:2] != (h, w):
                replacement = cv2.resize(replacement, (w, h))

            # Create smooth edge mask (expand mask dimensions for broadcasting)
            mask_3channel = np.stack([mask] * 3, axis=-1)

            # Apply alpha blending
            output = (
                frame * mask_3channel +
                replacement * (1 - mask_3channel)
            ).astype(np.uint8)

            return output

        except Exception as e:
            logger.error(f"Error applying mask: {e}")
            return frame

    def get_edge_mask(
        self,
        mask: np.ndarray,
        blur_radius: int = 5
    ) -> np.ndarray:
        """
        Create soft edge mask for smooth compositing.

        Applies Gaussian blur to mask edges to prevent hard cutouts
        around person (especially hair).

        Args:
            mask: Binary or float segmentation mask
            blur_radius: Blur kernel radius (larger = softer edges)

        Returns:
            Smoothed mask (0.0-1.0 float array)
        """
        try:
            # Ensure mask is float type
            if mask.dtype != np.float32:
                mask = mask.astype(np.float32)

            # Apply Gaussian blur for soft edges
            kernel_size = blur_radius * 2 + 1  # Must be odd
            soft_mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)

            return soft_mask

        except Exception as e:
            logger.error(f"Error creating edge mask: {e}")
            return mask

    def apply_blur_background(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        blur_amount: int = 55
    ) -> np.ndarray:
        """
        Apply background blur effect (keep person sharp).

        Args:
            frame: Original BGR frame
            mask: Segmentation mask (0.0-1.0 float array)
            blur_amount: Blur kernel size (must be odd, larger = more blur)

        Returns:
            Frame with blurred background
        """
        try:
            # Ensure blur_amount is odd
            if blur_amount % 2 == 0:
                blur_amount += 1

            # Create blurred version of entire frame
            blurred = cv2.GaussianBlur(frame, (blur_amount, blur_amount), 0)

            # Get soft edge mask for smooth transition
            soft_mask = self.get_edge_mask(mask, blur_radius=5)

            # Composite sharp person on blurred background
            output = self.apply_mask(frame, soft_mask, blurred)

            return output

        except Exception as e:
            logger.error(f"Error applying background blur: {e}")
            return frame

    def apply_virtual_background(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        background_image: np.ndarray
    ) -> np.ndarray:
        """
        Replace background with custom image.

        Args:
            frame: Original BGR frame
            mask: Segmentation mask (0.0-1.0 float array)
            background_image: Background image (will be resized to match frame)

        Returns:
            Frame with replaced background
        """
        try:
            # Get soft edge mask for natural hair/edge blending
            soft_mask = self.get_edge_mask(mask, blur_radius=5)

            # Apply replacement with soft edges
            output = self.apply_mask(frame, soft_mask, background_image)

            return output

        except Exception as e:
            logger.error(f"Error applying virtual background: {e}")
            return frame

    def close(self):
        """Release MediaPipe resources."""
        if self.segmenter:
            self.segmenter.close()
            self.segmenter = None
            logger.info("BackgroundSegmenter closed")

        self._last_frame_hash = None
        self._last_result = None
