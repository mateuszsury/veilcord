"""
Video effects module for real-time video processing.

Provides face tracking, background segmentation, and AR overlay capabilities
using MediaPipe and OpenCV for DiscordOpus video calls.

Available effects:
- Face tracking with 478 facial landmarks (MediaPipe Face Mesh)
- Background segmentation for virtual backgrounds (MediaPipe Selfie Segmentation)
- Video effect base class for custom effects

Classes:
    FaceTracker: Real-time face landmark detection
    FaceLandmarks: Container for face landmark data
    BackgroundSegmenter: Background/person segmentation
    SegmentationResult: Container for segmentation mask data
    VideoEffect: Base class for video effects
"""

import logging

logger = logging.getLogger(__name__)

# Try to import video effect classes
try:
    from .face_tracker import FaceTracker, FaceLandmarks
    from .segmentation import BackgroundSegmenter, SegmentationResult

    __all__ = [
        "FaceTracker",
        "FaceLandmarks",
        "BackgroundSegmenter",
        "SegmentationResult",
    ]

    logger.info("Video effects module loaded successfully")

except ImportError as e:
    logger.warning(f"Video effects unavailable (missing mediapipe): {e}")

    # Provide graceful degradation with stub classes
    class FaceTracker:
        """Stub FaceTracker when mediapipe is unavailable."""
        def __init__(self, *args, **kwargs):
            logger.error("FaceTracker requires mediapipe to be installed")

        def process(self, frame):
            return None

        def close(self):
            pass

    class FaceLandmarks:
        """Stub FaceLandmarks when mediapipe is unavailable."""
        pass

    class BackgroundSegmenter:
        """Stub BackgroundSegmenter when mediapipe is unavailable."""
        def __init__(self, *args, **kwargs):
            logger.error("BackgroundSegmenter requires mediapipe to be installed")

        def process(self, frame, threshold=0.5):
            return None

        def close(self):
            pass

    class SegmentationResult:
        """Stub SegmentationResult when mediapipe is unavailable."""
        pass

    __all__ = [
        "FaceTracker",
        "FaceLandmarks",
        "BackgroundSegmenter",
        "SegmentationResult",
    ]
