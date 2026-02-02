"""
Audio enhancement effects for professional voice quality.

Provides noise gate, de-esser, compressor, and equalizer effects
following professional audio engineering best practices.

Signal chain order (per research):
1. NoiseGate - Remove background noise
2. DeEsser - Reduce sibilance (BEFORE compressor)
3. Equalizer (corrective) - Fix frequency problems
4. Compressor - Even out levels
5. Equalizer (creative) - Enhance tone
"""

import logging
from enum import Enum
from typing import Optional

import numpy as np

from .effect_chain import AudioEffect

logger = logging.getLogger(__name__)


class EQPreset(Enum):
    """Equalizer presets for common use cases."""
    CLARITY = "clarity"  # Boost 2-4kHz, cut low mud
    WARMTH = "warmth"  # Boost low-mids, reduce harshness
    PRESENCE = "presence"  # Boost upper-mids for voice cut-through
    CUSTOM = "custom"  # User-adjustable bands


class NoiseGateEffect(AudioEffect):
    """
    Noise gate effect using Pedalboard.

    Gates quiet background noise below threshold, letting only
    louder voice signals through. Essential first step in
    professional vocal chain.

    Examples:
        # Standard noise gate
        gate = NoiseGateEffect()

        # More aggressive gating
        gate = NoiseGateEffect(threshold_db=-50, ratio=6)
    """

    def __init__(self, threshold_db: float = -40.0, ratio: float = 4.0):
        """
        Initialize noise gate.

        Args:
            threshold_db: Gate threshold in dB (-60 to -20)
            ratio: Gate ratio (2 to 10)
        """
        self._enabled = True
        self.threshold_db = max(-60.0, min(-20.0, threshold_db))
        self.ratio = max(2.0, min(10.0, ratio))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, NoiseGateEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "noise_gate"

    @property
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        self._enabled = value

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply noise gate."""
        if not self._enabled or not self._pedalboard_available:
            return audio

        try:
            from pedalboard import Pedalboard, NoiseGate

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Apply noise gate
            board = Pedalboard([NoiseGate(threshold_db=self.threshold_db, ratio=self.ratio)])
            processed = board(audio_float, sample_rate)

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying noise gate: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        return 5.0  # Very low latency


class DeEsserEffect(AudioEffect):
    """
    De-esser effect using multi-band compression.

    Reduces harsh sibilance (harsh "s" sounds) in the 4-8kHz range.
    MUST come BEFORE main compressor to avoid amplifying sibilance.

    Examples:
        # Standard de-essing
        deesser = DeEsserEffect()

        # More aggressive sibilance reduction
        deesser = DeEsserEffect(sensitivity=80)
    """

    def __init__(self, sensitivity: float = 50.0):
        """
        Initialize de-esser.

        Args:
            sensitivity: De-essing sensitivity (0-100%)
        """
        self._enabled = True
        self.sensitivity = max(0.0, min(100.0, sensitivity))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, DeEsserEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "de_esser"

    @property
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        self._enabled = value

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply de-essing."""
        if not self._enabled or not self._pedalboard_available or self.sensitivity == 0.0:
            return audio

        try:
            from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, Compressor

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # De-essing: Compress 4-8kHz range (sibilance frequencies)
            # sensitivity maps to compression threshold (-20 to -5 dB)
            threshold_db = -20.0 + (self.sensitivity / 100.0 * 15.0)

            # Multi-band approach:
            # 1. Isolate sibilance band with filters
            # 2. Compress that band
            # 3. Mix back with original

            # Simple implementation: compress high frequencies
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=4000),
                Compressor(threshold_db=threshold_db, ratio=4.0, attack_ms=1, release_ms=50)
            ])
            compressed_highs = board(audio_float, sample_rate)

            # Isolate lows/mids (below 4kHz)
            board_lows = Pedalboard([LowpassFilter(cutoff_frequency_hz=4000)])
            lows = board_lows(audio_float, sample_rate)

            # Mix: full lows + reduced highs based on sensitivity
            mix_ratio = 1.0 - (self.sensitivity / 100.0 * 0.5)  # Reduce highs by up to 50%
            processed = lows + compressed_highs * mix_ratio

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying de-esser: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        return 10.0  # Filters + compression


class CompressorEffect(AudioEffect):
    """
    Compressor effect using Pedalboard.

    Evens out voice levels by reducing dynamic range. Makes quiet parts
    louder and loud parts quieter for consistent volume.

    Examples:
        # Standard vocal compression
        comp = CompressorEffect()

        # Heavy compression for gaming/streaming
        comp = CompressorEffect(threshold_db=-25, ratio=6, makeup_gain_db=10)

        # Gentle podcast compression
        comp = CompressorEffect(threshold_db=-20, ratio=2.5, makeup_gain_db=3)
    """

    def __init__(
        self,
        threshold_db: float = -20.0,
        ratio: float = 3.0,
        attack_ms: float = 10.0,
        release_ms: float = 100.0,
        makeup_gain_db: float = 0.0,
        intensity: float = 1.0
    ):
        """
        Initialize compressor.

        Args:
            threshold_db: Compression threshold in dB (-40 to 0)
            ratio: Compression ratio (1.5 to 10)
            attack_ms: Attack time in milliseconds (1 to 50)
            release_ms: Release time in milliseconds (50 to 500)
            makeup_gain_db: Output gain in dB (0 to 20)
            intensity: Wet/dry mix (0.0 to 1.0)
        """
        self._enabled = True
        self.threshold_db = max(-40.0, min(0.0, threshold_db))
        self.ratio = max(1.5, min(10.0, ratio))
        self.attack_ms = max(1.0, min(50.0, attack_ms))
        self.release_ms = max(50.0, min(500.0, release_ms))
        self.makeup_gain_db = max(0.0, min(20.0, makeup_gain_db))
        self.intensity = max(0.0, min(1.0, intensity))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, CompressorEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "compressor"

    @property
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        self._enabled = value

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply compression."""
        if not self._enabled or not self._pedalboard_available or self.intensity == 0.0:
            return audio

        try:
            from pedalboard import Pedalboard, Compressor, Gain

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Build effect chain
            effects = [
                Compressor(
                    threshold_db=self.threshold_db,
                    ratio=self.ratio,
                    attack_ms=self.attack_ms,
                    release_ms=self.release_ms
                )
            ]

            # Add makeup gain if specified
            if self.makeup_gain_db > 0:
                effects.append(Gain(gain_db=self.makeup_gain_db))

            board = Pedalboard(effects)
            processed = board(audio_float, sample_rate)

            # Apply intensity (wet/dry mix)
            if self.intensity < 1.0:
                processed = audio_float * (1.0 - self.intensity) + processed * self.intensity

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying compression: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        # Latency depends on attack time
        return self.attack_ms + 5.0


class EqualizerEffect(AudioEffect):
    """
    Equalizer effect using Pedalboard filters.

    Shapes frequency response for voice enhancement. Supports
    presets (clarity, warmth, presence) and custom adjustments.

    Examples:
        # Clarity preset (boost presence, cut mud)
        eq = EqualizerEffect(preset=EQPreset.CLARITY)

        # Warmth preset (boost low-mids)
        eq = EqualizerEffect(preset=EQPreset.WARMTH)

        # Custom EQ
        eq = EqualizerEffect(
            preset=EQPreset.CUSTOM,
            high_pass_hz=100,
            low_shelf_db=-2,
            high_shelf_db=3
        )
    """

    def __init__(
        self,
        preset: EQPreset = EQPreset.CLARITY,
        high_pass_hz: float = 80.0,
        low_shelf_db: float = -3.0,
        high_shelf_db: float = 2.0,
        intensity: float = 1.0
    ):
        """
        Initialize equalizer.

        Args:
            preset: EQ preset to use
            high_pass_hz: High-pass filter frequency (60-200 Hz)
            low_shelf_db: Low shelf gain in dB at 200Hz (-6 to +6)
            high_shelf_db: High shelf gain in dB at 3kHz (-6 to +6)
            intensity: Wet/dry mix (0.0 to 1.0)
        """
        self._enabled = True
        self.preset = preset
        self.high_pass_hz = max(60.0, min(200.0, high_pass_hz))
        self.low_shelf_db = max(-6.0, min(6.0, low_shelf_db))
        self.high_shelf_db = max(-6.0, min(6.0, high_shelf_db))
        self.intensity = max(0.0, min(1.0, intensity))
        self._pedalboard_available = False

        # Apply preset defaults
        self._apply_preset()

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, EqualizerEffect will be bypassed")

    def _apply_preset(self):
        """Apply preset EQ settings."""
        if self.preset == EQPreset.CLARITY:
            # Boost 2-4kHz (presence), cut low mud
            self.high_pass_hz = 80.0
            self.low_shelf_db = -3.0  # Reduce muddiness
            self.high_shelf_db = 2.0  # Add presence
        elif self.preset == EQPreset.WARMTH:
            # Boost low-mids, reduce harshness
            self.high_pass_hz = 60.0
            self.low_shelf_db = 2.0  # Add warmth
            self.high_shelf_db = -2.0  # Reduce harshness
        elif self.preset == EQPreset.PRESENCE:
            # Boost upper-mids for cut-through
            self.high_pass_hz = 100.0
            self.low_shelf_db = -4.0  # Clean low end
            self.high_shelf_db = 4.0  # Strong presence boost
        # CUSTOM: use constructor values as-is

    @property
    def name(self) -> str:
        """Get effect name."""
        return f"equalizer_{self.preset.value}"

    @property
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        self._enabled = value

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply equalization."""
        if not self._enabled or not self._pedalboard_available or self.intensity == 0.0:
            return audio

        try:
            from pedalboard import Pedalboard, HighpassFilter, LowShelfFilter, HighShelfFilter

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Build EQ chain
            effects = [
                # 1. High-pass filter to remove rumble
                HighpassFilter(cutoff_frequency_hz=self.high_pass_hz)
            ]

            # 2. Low shelf (200 Hz) for warmth/mud control
            if abs(self.low_shelf_db) > 0.1:
                effects.append(LowShelfFilter(cutoff_frequency_hz=200, gain_db=self.low_shelf_db))

            # 3. High shelf (3 kHz) for presence/brightness
            if abs(self.high_shelf_db) > 0.1:
                effects.append(HighShelfFilter(cutoff_frequency_hz=3000, gain_db=self.high_shelf_db))

            board = Pedalboard(effects)
            processed = board(audio_float, sample_rate)

            # Apply intensity (wet/dry mix)
            if self.intensity < 1.0:
                processed = audio_float * (1.0 - self.intensity) + processed * self.intensity

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying EQ: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        return 8.0  # Filter latency


# Default professional vocal chain order (per research)
DEFAULT_PROFESSIONAL_CHAIN = [
    "NoiseGateEffect",  # 1. Remove background noise
    "DeEsserEffect",  # 2. Reduce sibilance (BEFORE compressor!)
    "EqualizerEffect(corrective)",  # 3. Fix frequency problems
    "CompressorEffect",  # 4. Even out levels
    "EqualizerEffect(creative)",  # 5. Enhance tone
]
