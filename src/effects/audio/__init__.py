"""
Audio effects package.

Provides noise cancellation, voice effects, enhancement effects,
and audio effect chains for real-time voice processing in calls.
"""

import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)

__all__ = []

# Attempt to import noise cancellation components
try:
    from .noise_cancellation import NoiseReducer, NoiseCancellationMethod
    __all__.extend(["NoiseReducer", "NoiseCancellationMethod"])
except ImportError as e:
    logger.warning(f"Could not import noise_cancellation: {e}")

# Attempt to import effect chain components
try:
    from .effect_chain import AudioEffectChain, AudioEffect, NoiseReducerEffect
    __all__.extend(["AudioEffectChain", "AudioEffect", "NoiseReducerEffect"])
except ImportError as e:
    logger.warning(f"Could not import effect_chain: {e}")

# Attempt to import voice effects
try:
    from .voice_effects import (
        PitchShiftEffect,
        RobotVoiceEffect,
        HeliumVoiceEffect,
        EchoEffect,
        ReverbEffect
    )
    __all__.extend([
        "PitchShiftEffect",
        "RobotVoiceEffect",
        "HeliumVoiceEffect",
        "EchoEffect",
        "ReverbEffect"
    ])
except ImportError as e:
    logger.warning(f"Could not import voice_effects: {e}")

# Attempt to import enhancement effects
try:
    from .enhancement import (
        NoiseGateEffect,
        DeEsserEffect,
        CompressorEffect,
        EqualizerEffect,
        EQPreset
    )
    __all__.extend([
        "NoiseGateEffect",
        "DeEsserEffect",
        "CompressorEffect",
        "EqualizerEffect",
        "EQPreset"
    ])
except ImportError as e:
    logger.warning(f"Could not import enhancement: {e}")

# Attempt to import voice message effects
try:
    from .voice_message_effects import VoiceMessageEffects, VoiceMessageEffectMetadata
    __all__.extend([
        "VoiceMessageEffects",
        "VoiceMessageEffectMetadata"
    ])
except ImportError as e:
    logger.warning(f"Could not import voice_message_effects: {e}")


# Built-in audio effect presets
AUDIO_PRESETS: Dict[str, Callable[[], AudioEffectChain]] = {}


def _create_none_preset() -> AudioEffectChain:
    """Empty chain (no effects)."""
    return AudioEffectChain([])


def _create_professional_voice_preset() -> AudioEffectChain:
    """Professional voice quality for calls and recordings."""
    try:
        return AudioEffectChain([
            NoiseReducerEffect(),  # AI noise cancellation
            NoiseGateEffect(threshold_db=-40, ratio=4),  # Gate background
            DeEsserEffect(sensitivity=50),  # Reduce sibilance
            CompressorEffect(threshold_db=-20, ratio=3, makeup_gain_db=3),  # Even levels
            EqualizerEffect(preset=EQPreset.CLARITY, intensity=0.8),  # Clarity boost
        ])
    except NameError:
        logger.warning("Professional voice preset requires all enhancement effects")
        return AudioEffectChain([])


def _create_gaming_preset() -> AudioEffectChain:
    """Loud and clear for gaming/streaming."""
    try:
        return AudioEffectChain([
            NoiseReducerEffect(),  # AI noise cancellation
            CompressorEffect(threshold_db=-25, ratio=6, makeup_gain_db=10),  # Heavy compression
            EqualizerEffect(preset=EQPreset.PRESENCE, intensity=1.0),  # Strong presence
        ])
    except NameError:
        logger.warning("Gaming preset requires enhancement effects")
        return AudioEffectChain([])


def _create_podcast_preset() -> AudioEffectChain:
    """Warm, natural voice for podcasts."""
    try:
        return AudioEffectChain([
            NoiseReducerEffect(),  # AI noise cancellation
            NoiseGateEffect(threshold_db=-45, ratio=3),  # Gentle gate
            DeEsserEffect(sensitivity=40),  # Subtle de-essing
            CompressorEffect(threshold_db=-20, ratio=2.5, makeup_gain_db=3),  # Gentle compression
            EqualizerEffect(preset=EQPreset.WARMTH, intensity=0.7),  # Warm tone
        ])
    except NameError:
        logger.warning("Podcast preset requires enhancement effects")
        return AudioEffectChain([])


def _create_robot_preset() -> AudioEffectChain:
    """Robot voice transformation."""
    try:
        return AudioEffectChain([
            NoiseReducerEffect(),  # Clean input
            RobotVoiceEffect(intensity=0.8),  # Robot transformation
        ])
    except NameError:
        logger.warning("Robot preset requires voice effects")
        return AudioEffectChain([])


def _create_helium_preset() -> AudioEffectChain:
    """Helium/chipmunk voice transformation."""
    try:
        return AudioEffectChain([
            NoiseReducerEffect(),  # Clean input
            HeliumVoiceEffect(semitones=8, intensity=1.0),  # Helium transformation
        ])
    except NameError:
        logger.warning("Helium preset requires voice effects")
        return AudioEffectChain([])


def _create_echo_chamber_preset() -> AudioEffectChain:
    """Echo chamber with reverb."""
    try:
        return AudioEffectChain([
            NoiseReducerEffect(),  # Clean input
            EchoEffect(delay_ms=300, feedback=0.5, intensity=0.6),  # Echo
            ReverbEffect(room_size=0.8, damping=0.6, intensity=0.4),  # Large reverb
        ])
    except NameError:
        logger.warning("Echo chamber preset requires voice effects")
        return AudioEffectChain([])


# Register all presets
AUDIO_PRESETS = {
    "none": _create_none_preset,
    "professional_voice": _create_professional_voice_preset,
    "gaming": _create_gaming_preset,
    "podcast": _create_podcast_preset,
    "robot": _create_robot_preset,
    "helium": _create_helium_preset,
    "echo_chamber": _create_echo_chamber_preset,
}


def create_preset_chain(preset_name: str) -> AudioEffectChain:
    """
    Create an effect chain from a preset.

    Args:
        preset_name: Name of preset to create

    Returns:
        AudioEffectChain configured for the preset

    Raises:
        ValueError: If preset_name is not recognized

    Examples:
        # Create professional voice chain
        chain = create_preset_chain("professional_voice")

        # Create robot voice chain
        chain = create_preset_chain("robot")

        # List available presets
        presets = list(AUDIO_PRESETS.keys())
    """
    if preset_name not in AUDIO_PRESETS:
        raise ValueError(
            f"Unknown preset '{preset_name}'. "
            f"Available presets: {', '.join(AUDIO_PRESETS.keys())}"
        )

    return AUDIO_PRESETS[preset_name]()


__all__.extend(["AUDIO_PRESETS", "create_preset_chain"])
