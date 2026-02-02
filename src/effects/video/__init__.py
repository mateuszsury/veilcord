"""
Video effects module for real-time video processing.

Provides face tracking, background segmentation, beauty filters, creative
effects, and AR overlays using MediaPipe and OpenCV for DiscordOpus video calls.

Available effects:
- Face tracking with 478 facial landmarks (MediaPipe Face Mesh)
- Background segmentation for virtual backgrounds (MediaPipe Selfie Segmentation)
- Beauty filters (skin smoothing, lighting correction)
- Creative filters (vintage, cartoon, color grading, vignette)
- AR overlays (glasses, hats, masks, face filters)
- Video effect base class for custom effects

Classes:
    FaceTracker: Real-time face landmark detection
    FaceLandmarks: Container for face landmark data
    BackgroundSegmenter: Background/person segmentation
    SegmentationResult: Container for segmentation mask data
    VideoEffect: Base class for video effects
    BeautyFilter: Skin smoothing filter
    LightingCorrection: Lighting enhancement filter
    CombinedBeautyFilter: Combined beauty and lighting filter
    VintageFilter: Vintage/retro effect
    CartoonFilter: Cartoon/comic book effect
    ColorGradingFilter: Color grading and adjustments
    VignetteFilter: Vignette effect (darkened corners)
    AROverlay: Base class for AR face overlays
    AROverlayManager: Manager for multiple AR overlays
    GlassesOverlay, SunglassesOverlay, HatOverlay, etc.: Specialized overlays

Constants:
    VIDEO_FILTER_PRESETS: Dictionary of all available filter presets
    CREATIVE_PRESETS: Dictionary of creative filter combinations
    BUILT_IN_OVERLAYS: Dictionary of built-in AR overlays
"""

import logging
from typing import Dict, Any, Optional

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

# Import beauty and creative filters (always available with OpenCV)
from .beauty_filters import (
    VideoEffect,
    BeautyFilter,
    LightingCorrection,
    CombinedBeautyFilter,
)
from .creative_filters import (
    VintageFilter,
    CartoonFilter,
    ColorGradingFilter,
    VignetteFilter,
    CREATIVE_PRESETS,
)

# Import AR overlays (requires MediaPipe)
try:
    from .ar_overlays import (
        AROverlay,
        AROverlayManager,
        OverlayType,
        OverlayAnchor,
        OVERLAY_ANCHORS,
        BUILT_IN_OVERLAYS,
        GlassesOverlay,
        SunglassesOverlay,
        HatOverlay,
        MaskOverlay,
        FaceFilterOverlay,
        MustacheOverlay,
        EarsOverlay,
        create_placeholder_overlay,
    )
    AR_OVERLAYS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AR overlays unavailable: {e}")
    AR_OVERLAYS_AVAILABLE = False

# Add to __all__
__all__.extend([
    "VideoEffect",
    "BeautyFilter",
    "LightingCorrection",
    "CombinedBeautyFilter",
    "VintageFilter",
    "CartoonFilter",
    "ColorGradingFilter",
    "VignetteFilter",
    "CREATIVE_PRESETS",
    "VIDEO_FILTER_PRESETS",
    "create_filter_preset",
])

if AR_OVERLAYS_AVAILABLE:
    __all__.extend([
        "AROverlay",
        "AROverlayManager",
        "OverlayType",
        "OverlayAnchor",
        "OVERLAY_ANCHORS",
        "BUILT_IN_OVERLAYS",
        "GlassesOverlay",
        "SunglassesOverlay",
        "HatOverlay",
        "MaskOverlay",
        "FaceFilterOverlay",
        "MustacheOverlay",
        "EarsOverlay",
        "create_placeholder_overlay",
    ])

# Combined preset dictionary with all available filters
VIDEO_FILTER_PRESETS: Dict[str, Dict[str, Any]] = {
    # No filter
    "none": {
        "description": "No video filters applied",
        "filters": []
    },

    # Beauty filter presets
    "beauty_light": {
        "description": "Light beauty enhancement",
        "filters": [
            {"type": "BeautyFilter", "intensity": 0.3}
        ]
    },
    "beauty_medium": {
        "description": "Medium beauty enhancement",
        "filters": [
            {"type": "BeautyFilter", "intensity": 0.5}
        ]
    },
    "beauty_full": {
        "description": "Full beauty enhancement with lighting correction",
        "filters": [
            {"type": "CombinedBeautyFilter", "intensity": 0.7}
        ]
    },

    # Creative presets (from CREATIVE_PRESETS)
    "vintage_warm": CREATIVE_PRESETS["vintage_warm"],
    "vintage_cool": CREATIVE_PRESETS["vintage_cool"],
    "cartoon": CREATIVE_PRESETS["cartoon"],
    "dramatic": CREATIVE_PRESETS["dramatic"],
    "soft_glow": CREATIVE_PRESETS["soft_glow"],
    "vibrant": CREATIVE_PRESETS["vibrant"],
}


def create_filter_preset(name: str) -> Optional[VideoEffect]:
    """
    Factory function to create filter instances from preset names.

    Args:
        name: Preset name from VIDEO_FILTER_PRESETS

    Returns:
        VideoEffect instance or None if preset not found

    Examples:
        >>> filter = create_filter_preset("beauty_medium")
        >>> filter = create_filter_preset("vintage_warm")
    """
    if name not in VIDEO_FILTER_PRESETS:
        logger.error(f"Unknown filter preset: {name}")
        return None

    preset = VIDEO_FILTER_PRESETS[name]
    filters_config = preset.get("filters", [])

    if not filters_config:
        # "none" preset
        return None

    # For now, return the first filter (single filter presets)
    # In the future, this could return a composite filter chain
    filter_config = filters_config[0]
    filter_type = filter_config.get("type")

    # Map type string to class
    filter_classes = {
        "BeautyFilter": BeautyFilter,
        "LightingCorrection": LightingCorrection,
        "CombinedBeautyFilter": CombinedBeautyFilter,
        "VintageFilter": VintageFilter,
        "CartoonFilter": CartoonFilter,
        "ColorGradingFilter": ColorGradingFilter,
        "VignetteFilter": VignetteFilter,
    }

    filter_class = filter_classes.get(filter_type)
    if not filter_class:
        logger.error(f"Unknown filter type: {filter_type}")
        return None

    # Create instance with config parameters
    try:
        return filter_class.from_dict(filter_config)
    except Exception as e:
        logger.error(f"Failed to create filter {filter_type}: {e}")
        return None


logger.info(f"Video filters loaded: {len(VIDEO_FILTER_PRESETS)} presets available")
