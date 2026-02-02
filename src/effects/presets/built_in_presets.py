"""
Built-in effect presets for common use cases.

Provides pre-configured presets for Work, Gaming, Streaming, Fun effects,
Privacy, and Podcast scenarios with optimized settings.
"""

from typing import Optional, List
from datetime import datetime

from src.effects.presets.preset_manager import EffectPreset


# Built-in presets dictionary
BUILT_IN_PRESETS = {}


def get_preset(name: str) -> Optional[EffectPreset]:
    """
    Get built-in preset by name.

    Args:
        name: Preset name (case-insensitive)

    Returns:
        EffectPreset if found, None otherwise
    """
    return BUILT_IN_PRESETS.get(name.lower())


def get_all_builtin_names() -> List[str]:
    """
    Get list of all built-in preset names.

    Returns:
        List of preset names
    """
    return list(BUILT_IN_PRESETS.keys())


# Create built-in presets
def _create_built_in_presets():
    """Initialize all built-in presets."""
    global BUILT_IN_PRESETS

    # None preset - no effects
    BUILT_IN_PRESETS["none"] = EffectPreset(
        name="none",
        version="1.0",
        audio={
            "noise_cancellation": "none",
            "effect_chain": []
        },
        video={
            "background": {"type": "none"},
            "beauty_filter": {"enabled": False, "intensity": 0},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "none"}
        },
        hardware_requirements={
            "requires_gpu": False,
            "min_vram_mb": 0,
            "recommended_quality": "low"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Work preset - professional appearance
    BUILT_IN_PRESETS["work"] = EffectPreset(
        name="work",
        version="1.0",
        audio={
            "noise_cancellation": "deepfilter",
            "effect_chain": [
                {"type": "NoiseGate", "threshold_db": -40, "ratio": 4},
                {"type": "DeEsser", "frequency": 6000},
                {"type": "Compressor", "threshold_db": -20, "ratio": 2.5},
                {"type": "EQ", "preset": "clarity"}
            ]
        },
        video={
            "background": {"type": "blur", "intensity": "medium"},
            "beauty_filter": {"enabled": True, "intensity": 30},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "none"}
        },
        hardware_requirements={
            "requires_gpu": False,  # Has CPU fallbacks
            "min_vram_mb": 1024,
            "recommended_quality": "high"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Gaming preset - loud and clear
    BUILT_IN_PRESETS["gaming"] = EffectPreset(
        name="gaming",
        version="1.0",
        audio={
            "noise_cancellation": "deepfilter",
            "effect_chain": [
                {"type": "NoiseGate", "threshold_db": -35, "ratio": 6},
                {"type": "Compressor", "threshold_db": -15, "ratio": 4},
                {"type": "EQ", "preset": "presence"}
            ]
        },
        video={
            "background": {"type": "none"},
            "beauty_filter": {"enabled": False, "intensity": 0},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "none"}
        },
        hardware_requirements={
            "requires_gpu": False,
            "min_vram_mb": 512,
            "recommended_quality": "medium"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Streaming preset - polished setup
    BUILT_IN_PRESETS["streaming"] = EffectPreset(
        name="streaming",
        version="1.0",
        audio={
            "noise_cancellation": "deepfilter",
            "effect_chain": [
                {"type": "NoiseGate", "threshold_db": -40, "ratio": 4},
                {"type": "DeEsser", "frequency": 6000},
                {"type": "Compressor", "threshold_db": -18, "ratio": 3},
                {"type": "EQ", "preset": "warmth"}
            ]
        },
        video={
            "background": {"type": "blur", "intensity": "light"},
            "beauty_filter": {"enabled": True, "intensity": 50},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "none"},
            "lighting_correction": True
        },
        hardware_requirements={
            "requires_gpu": True,  # Best quality needs GPU
            "min_vram_mb": 2048,
            "recommended_quality": "ultra"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Fun Robot preset
    BUILT_IN_PRESETS["fun_robot"] = EffectPreset(
        name="fun_robot",
        version="1.0",
        audio={
            "noise_cancellation": "rnnoise",
            "effect_chain": [
                {"type": "RobotVoice", "pitch_shift": -5},
                {"type": "Reverb", "room_size": "small"}
            ]
        },
        video={
            "background": {"type": "none"},
            "beauty_filter": {"enabled": False, "intensity": 0},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "sunglasses", "style": "black"}
        },
        hardware_requirements={
            "requires_gpu": False,
            "min_vram_mb": 512,
            "recommended_quality": "medium"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Fun Helium preset
    BUILT_IN_PRESETS["fun_helium"] = EffectPreset(
        name="fun_helium",
        version="1.0",
        audio={
            "noise_cancellation": "none",
            "effect_chain": [
                {"type": "PitchShift", "semitones": 7}
            ]
        },
        video={
            "background": {"type": "none"},
            "beauty_filter": {"enabled": False, "intensity": 0},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "party_hat"}
        },
        hardware_requirements={
            "requires_gpu": False,
            "min_vram_mb": 256,
            "recommended_quality": "low"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Privacy preset - maximum privacy
    BUILT_IN_PRESETS["privacy"] = EffectPreset(
        name="privacy",
        version="1.0",
        audio={
            "noise_cancellation": "deepfilter",  # Blocks most background
            "effect_chain": []
        },
        video={
            "background": {"type": "blur", "intensity": "heavy"},
            "beauty_filter": {"enabled": False, "intensity": 0},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "none"}
        },
        hardware_requirements={
            "requires_gpu": False,
            "min_vram_mb": 1024,
            "recommended_quality": "medium"
        },
        created_at=datetime.now(),
        is_builtin=True
    )

    # Podcast preset - podcast-quality audio
    BUILT_IN_PRESETS["podcast"] = EffectPreset(
        name="podcast",
        version="1.0",
        audio={
            "noise_cancellation": "deepfilter",
            "effect_chain": [
                {"type": "NoiseGate", "threshold_db": -45, "ratio": 4},
                {"type": "DeEsser", "frequency": 6000},
                {"type": "Compressor", "threshold_db": -20, "ratio": 2},
                {"type": "EQ", "preset": "podcast"}
            ]
        },
        video={
            "background": {"type": "blur", "intensity": "light"},
            "beauty_filter": {"enabled": True, "intensity": 20},
            "creative_filter": {"type": "none"},
            "ar_overlay": {"type": "none"}
        },
        hardware_requirements={
            "requires_gpu": False,
            "min_vram_mb": 1024,
            "recommended_quality": "high"
        },
        created_at=datetime.now(),
        is_builtin=True
    )


# Initialize presets on module import
_create_built_in_presets()
