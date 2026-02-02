"""
Effects package for audio and video processing.

Provides AI-based noise cancellation, DSP effects, virtual backgrounds,
beauty filters, and AR overlays for real-time communication.

This module exports all effect classes, presets, and utilities for
easy access throughout the application.
"""

__version__ = "0.1.0"

# ========== Hardware Module ==========
from src.effects.hardware import (
    HardwareDetector,
    QualityAdapter,
    QualityPreset,
    ResourceMonitor,
)

# ========== Audio Module ==========
from src.effects.audio import (
    # Noise cancellation
    NoiseReducer,
    NoiseCancellationMethod,
    # Effect chain
    AudioEffectChain,
    AudioEffect,
    NoiseReducerEffect,
    # Voice effects
    PitchShiftEffect,
    RobotVoiceEffect,
    HeliumVoiceEffect,
    EchoEffect,
    ReverbEffect,
    # Enhancement effects
    CompressorEffect,
    EqualizerEffect,
    DeEsserEffect,
    NoiseGateEffect,
    EQPreset,
    # Presets and utilities
    AUDIO_PRESETS,
    create_preset_chain,
)

# Voice message effects
from src.effects.audio.voice_message_effects import (
    VoiceMessageEffects,
    VoiceMessageEffectMetadata,
)

# ========== Video Module ==========
from src.effects.video import (
    # Face tracking
    FaceTracker,
    FaceLandmarks,
    # Segmentation
    BackgroundSegmenter,
    SegmentationResult,
    # Video effect base
    VideoEffect,
    # Beauty filters
    BeautyFilter,
    LightingCorrection,
    CombinedBeautyFilter,
    # Creative filters
    VintageFilter,
    CartoonFilter,
    ColorGradingFilter,
    VignetteFilter,
    CREATIVE_PRESETS,
    # Screen overlays
    ScreenOverlay,
    WatermarkOverlay,
    BorderOverlay,
    CursorHighlight,
    ScreenOverlayManager,
    # Presets
    VIDEO_FILTER_PRESETS,
    create_filter_preset,
)

# AR overlays (conditionally imported)
try:
    from src.effects.video.ar_overlays import (
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
    AR_AVAILABLE = True
except ImportError:
    AR_AVAILABLE = False

# Virtual background (requires segmentation)
try:
    from src.effects.video.virtual_background import (
        VirtualBackground,
        BackgroundType,
    )
    VIRTUAL_BACKGROUND_AVAILABLE = True
except ImportError:
    VIRTUAL_BACKGROUND_AVAILABLE = False

# ========== Tracks Module ==========
from src.effects.tracks import (
    AudioEffectsTrack,
    VideoEffectsTrack,
    VideoEffectsPipeline,
)

# ========== Presets Module ==========
from src.effects.presets import (
    PresetManager,
    EffectPreset,
    BUILT_IN_PRESETS,
    get_preset,
    get_all_builtin_names,
)

# ========== Package-Level Utilities ==========

# Singleton instances
_hardware_detector = None
_quality_adapter = None
_preset_manager = None


def get_hardware_detector() -> HardwareDetector:
    """
    Get singleton HardwareDetector instance.

    Returns:
        HardwareDetector instance
    """
    global _hardware_detector
    if _hardware_detector is None:
        _hardware_detector = HardwareDetector()
    return _hardware_detector


def get_quality_adapter() -> QualityAdapter:
    """
    Get singleton QualityAdapter instance.

    Returns:
        QualityAdapter instance
    """
    global _quality_adapter
    if _quality_adapter is None:
        _quality_adapter = QualityAdapter()
    return _quality_adapter


def get_preset_manager() -> PresetManager:
    """
    Get singleton PresetManager instance.

    Returns:
        PresetManager instance
    """
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = PresetManager()
    return _preset_manager


def apply_preset(name: str):
    """
    Apply a preset by name and get configured effect chains.

    Args:
        name: Preset name (from BUILT_IN_PRESETS or user presets)

    Returns:
        Tuple of (AudioEffectChain, VideoEffectsPipeline)

    Raises:
        ValueError: If preset not found

    Examples:
        # Apply built-in preset
        audio_chain, video_pipeline = apply_preset("work")

        # Apply user preset
        audio_chain, video_pipeline = apply_preset("my_custom_preset")
    """
    preset = get_preset(name)
    if preset is None:
        raise ValueError(f"Preset '{name}' not found")

    # Create audio chain
    audio_chain = AudioEffectChain()
    if preset.audio_effects:
        for effect_config in preset.audio_effects:
            # Reconstruct effect from config
            # This would need implementation in AudioEffectChain
            pass

    # Create video pipeline
    video_pipeline = VideoEffectsPipeline()
    if preset.video_effects:
        for effect_config in preset.video_effects:
            # Reconstruct effect from config
            # This would need implementation in VideoEffectsPipeline
            pass

    return audio_chain, video_pipeline


# ========== Exports ==========

__all__ = [
    # Version
    "__version__",

    # Hardware
    "HardwareDetector",
    "QualityAdapter",
    "QualityPreset",
    "ResourceMonitor",

    # Audio - Noise cancellation
    "NoiseReducer",
    "NoiseCancellationMethod",

    # Audio - Effect chain
    "AudioEffectChain",
    "AudioEffect",
    "NoiseReducerEffect",

    # Audio - Voice effects
    "PitchShiftEffect",
    "RobotVoiceEffect",
    "HeliumVoiceEffect",
    "EchoEffect",
    "ReverbEffect",

    # Audio - Enhancement
    "CompressorEffect",
    "EqualizerEffect",
    "DeEsserEffect",
    "NoiseGateEffect",
    "EQPreset",

    # Audio - Presets
    "AUDIO_PRESETS",
    "create_preset_chain",

    # Audio - Voice messages
    "VoiceMessageEffects",
    "VoiceMessageEffectMetadata",

    # Video - Face tracking
    "FaceTracker",
    "FaceLandmarks",

    # Video - Segmentation
    "BackgroundSegmenter",
    "SegmentationResult",

    # Video - Effect base
    "VideoEffect",

    # Video - Beauty filters
    "BeautyFilter",
    "LightingCorrection",
    "CombinedBeautyFilter",

    # Video - Creative filters
    "VintageFilter",
    "CartoonFilter",
    "ColorGradingFilter",
    "VignetteFilter",
    "CREATIVE_PRESETS",

    # Video - Screen overlays
    "ScreenOverlay",
    "WatermarkOverlay",
    "BorderOverlay",
    "CursorHighlight",
    "ScreenOverlayManager",

    # Video - Presets
    "VIDEO_FILTER_PRESETS",
    "create_filter_preset",

    # Tracks
    "AudioEffectsTrack",
    "VideoEffectsTrack",
    "VideoEffectsPipeline",

    # Presets
    "PresetManager",
    "EffectPreset",
    "BUILT_IN_PRESETS",
    "get_preset",
    "get_all_builtin_names",

    # Package utilities
    "get_hardware_detector",
    "get_quality_adapter",
    "get_preset_manager",
    "apply_preset",

    # Feature flags
    "AR_AVAILABLE",
    "VIRTUAL_BACKGROUND_AVAILABLE",
]

# Conditionally add AR overlays to exports if available
if AR_AVAILABLE:
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

# Conditionally add virtual background to exports if available
if VIRTUAL_BACKGROUND_AVAILABLE:
    __all__.extend([
        "VirtualBackground",
        "BackgroundType",
    ])
