"""
Audio effect chain for composing multiple effects.

Provides a framework for chaining audio effects in the correct order
to avoid artifacts and maximize quality.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

import numpy as np

from .noise_cancellation import NoiseReducer, NoiseCancellationMethod

logger = logging.getLogger(__name__)


class AudioEffect(ABC):
    """
    Abstract base class for audio effects.

    All audio effects must implement this interface to be used
    in the AudioEffectChain.

    The recommended effect order for professional audio processing:
    1. Gate (noise gate to remove background noise)
    2. De-esser (reduce harsh sibilance)
    3. Corrective EQ (fix frequency problems)
    4. Compressor (even out levels)
    5. Creative EQ (enhance tone)
    6. Effects (reverb, delay, etc.)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get effect name."""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        pass

    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool):
        """Enable or disable effect."""
        pass

    @abstractmethod
    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Process audio through this effect.

        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio
        """
        pass

    @abstractmethod
    def get_latency_ms(self) -> float:
        """
        Get approximate latency introduced by this effect.

        Returns:
            Latency in milliseconds
        """
        pass


class AudioEffectChain:
    """
    Chain multiple audio effects for sequential processing.

    Effects are applied in order, with each effect's output
    becoming the next effect's input. Disabled effects are skipped.

    The chain tracks total latency and warns if it exceeds 150ms,
    which is the threshold where users start to notice delay in conversations.

    Examples:
        # Create chain with effects
        chain = AudioEffectChain([
            NoiseReducerEffect(),
            CompressorEffect(),
        ])

        # Process audio
        clean_audio = chain.process(noisy_audio, sample_rate=48000)

        # Add effect at specific position
        chain.add_effect(EQEffect(), index=1)

        # Remove effect by name
        chain.remove_effect("compressor")

        # Check total latency
        print(f"Total latency: {chain.get_total_latency_ms()}ms")

        # Save/load chain configuration
        config = chain.to_dict()
        new_chain = AudioEffectChain.from_dict(config)
    """

    def __init__(self, effects: Optional[List[AudioEffect]] = None):
        """
        Initialize effect chain.

        Args:
            effects: List of effects to apply in order, or None for empty chain
        """
        self.effects: List[AudioEffect] = effects or []

    def add_effect(self, effect: AudioEffect, index: Optional[int] = None):
        """
        Add effect to chain.

        Args:
            effect: Effect to add
            index: Position to insert effect, or None to append at end
        """
        if index is None:
            self.effects.append(effect)
            logger.debug(f"Added effect '{effect.name}' at end of chain")
        else:
            self.effects.insert(index, effect)
            logger.debug(f"Added effect '{effect.name}' at position {index}")

    def remove_effect(self, effect_name: str):
        """
        Remove effect from chain by name.

        Args:
            effect_name: Name of effect to remove
        """
        self.effects = [e for e in self.effects if e.name != effect_name]
        logger.debug(f"Removed effect '{effect_name}' from chain")

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply all enabled effects in order.

        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio after all effects applied
        """
        processed = audio

        for effect in self.effects:
            if effect.enabled:
                try:
                    processed = effect.process(processed, sample_rate)
                except Exception as e:
                    logger.error(f"Error processing effect '{effect.name}': {e}")
                    # Continue with unprocessed audio on error
                    pass

        return processed

    def get_total_latency_ms(self) -> float:
        """
        Calculate total latency of all enabled effects.

        Warns if total latency exceeds 150ms threshold
        (per research pitfall #1).

        Returns:
            Total latency in milliseconds
        """
        total = sum(
            effect.get_latency_ms()
            for effect in self.effects
            if effect.enabled
        )

        if total > 150:
            logger.warning(
                f"Total effect chain latency ({total:.1f}ms) exceeds 150ms threshold. "
                "Users may experience noticeable delay in conversations. "
                "Consider disabling some effects or switching to lower-latency alternatives."
            )

        return total

    def clear(self):
        """Remove all effects from chain."""
        self.effects.clear()
        logger.debug("Cleared all effects from chain")

    def get_effect(self, name: str) -> Optional[AudioEffect]:
        """
        Get effect by name.

        Args:
            name: Effect name

        Returns:
            Effect if found, None otherwise
        """
        for effect in self.effects:
            if effect.name == name:
                return effect
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize chain to dictionary.

        Returns:
            Dictionary representation of chain (for JSON serialization)
        """
        return {
            "version": "1.0",
            "effects": [
                {
                    "type": type(effect).__name__,
                    "name": effect.name,
                    "enabled": effect.enabled,
                    # Add effect-specific parameters here
                    # Each effect should implement its own serialization
                }
                for effect in self.effects
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioEffectChain":
        """
        Deserialize chain from dictionary.

        Args:
            data: Dictionary representation of chain

        Returns:
            Reconstructed AudioEffectChain

        Note:
            This is a basic implementation. In a full implementation,
            you would need to register effect types and their constructors
            to properly reconstruct effect instances with their parameters.
        """
        # Basic implementation - would need effect registry for full deserialization
        logger.warning("from_dict() requires effect registry for full reconstruction")
        return cls()


class NoiseReducerEffect(AudioEffect):
    """
    Wrapper for NoiseReducer to use in effect chains.

    This allows noise cancellation to be part of the effect chain
    and managed alongside other effects.

    Examples:
        # Create with auto-selected method
        noise_effect = NoiseReducerEffect()

        # Create with specific method
        noise_effect = NoiseReducerEffect(
            method=NoiseCancellationMethod.RNNOISE
        )

        # Toggle on/off
        noise_effect.enabled = False

        # Use in chain
        chain = AudioEffectChain([noise_effect])
    """

    def __init__(self, method: Optional[NoiseCancellationMethod] = None):
        """
        Initialize noise reducer effect.

        Args:
            method: Noise cancellation method, or None for auto-selection
        """
        self._reducer = NoiseReducer(method=method)
        self._name = f"noise_reduction_{self._reducer.method.value}"

    @property
    def name(self) -> str:
        """Get effect name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        return self._reducer.enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        self._reducer.enabled = value

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Process audio through noise reducer.

        Args:
            audio: Audio data
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio
        """
        return self._reducer.process(audio, sample_rate)

    def get_latency_ms(self) -> float:
        """
        Get latency of noise reducer.

        Returns:
            Latency in milliseconds
        """
        return self._reducer.latency_ms

    @property
    def reducer(self) -> NoiseReducer:
        """Get underlying NoiseReducer instance for advanced control."""
        return self._reducer
