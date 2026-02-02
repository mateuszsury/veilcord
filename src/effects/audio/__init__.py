"""
Audio effects package.

Provides noise cancellation, voice effects, and audio effect chains
for real-time voice processing in calls.
"""

__all__ = []

# Attempt to import noise cancellation components
try:
    from .noise_cancellation import NoiseReducer, NoiseCancellationMethod
    __all__.extend(["NoiseReducer", "NoiseCancellationMethod"])
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Could not import noise_cancellation: {e}")

# Attempt to import effect chain components
try:
    from .effect_chain import AudioEffectChain, AudioEffect, NoiseReducerEffect
    __all__.extend(["AudioEffectChain", "AudioEffect", "NoiseReducerEffect"])
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Could not import effect_chain: {e}")
