"""
Voice transformation effects using Pedalboard.

Provides professional voice effects including pitch shift, robot voice,
helium voice, echo, and reverb, all with intensity control for smooth blending.
"""

import logging
from typing import Optional

import numpy as np

from .effect_chain import AudioEffect

logger = logging.getLogger(__name__)


class BaseVoiceEffect(AudioEffect):
    """
    Base class for voice transformation effects.

    Provides common functionality:
    - Intensity control (0.0 to 1.0, maps to 0-100% slider)
    - Enabled/disabled state
    - Wet/dry blending based on intensity

    Subclasses must implement:
    - _process_effect(): Apply the actual transformation
    - name property
    - get_latency_ms()
    """

    def __init__(self, intensity: float = 1.0):
        """
        Initialize base voice effect.

        Args:
            intensity: Effect intensity (0.0 to 1.0)
        """
        self._intensity = max(0.0, min(1.0, intensity))
        self._enabled = True

    @property
    def intensity(self) -> float:
        """Get effect intensity (0.0 to 1.0)."""
        return self._intensity

    @intensity.setter
    def intensity(self, value: float):
        """Set effect intensity (0.0 to 1.0)."""
        self._intensity = max(0.0, min(1.0, value))

    @property
    def enabled(self) -> bool:
        """Check if effect is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable effect."""
        self._enabled = value

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Process audio through effect with intensity blending.

        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio with wet/dry blend based on intensity
        """
        if not self._enabled or self._intensity == 0.0:
            return audio

        # Apply the effect transformation
        wet = self._process_effect(audio, sample_rate)

        # Blend wet (processed) with dry (original) based on intensity
        if self._intensity < 1.0:
            return audio * (1.0 - self._intensity) + wet * self._intensity
        else:
            return wet

    def _process_effect(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply the actual effect transformation.

        Subclasses must implement this method.

        Args:
            audio: Audio data
            sample_rate: Sample rate in Hz

        Returns:
            Transformed audio
        """
        raise NotImplementedError("Subclasses must implement _process_effect()")


class PitchShiftEffect(BaseVoiceEffect):
    """
    Pitch shift effect using Pedalboard.

    Shifts pitch up or down by semitones while preserving tempo.
    Intensity controls blend between original and shifted audio.

    Examples:
        # Shift up 5 semitones (perfect fourth)
        effect = PitchShiftEffect(semitones=5)

        # Shift down 12 semitones (one octave)
        effect = PitchShiftEffect(semitones=-12)

        # 50% intensity for subtle shift
        effect = PitchShiftEffect(semitones=7, intensity=0.5)
    """

    def __init__(self, semitones: float = 0.0, intensity: float = 1.0):
        """
        Initialize pitch shift effect.

        Args:
            semitones: Pitch shift in semitones (-12 to +12)
            intensity: Effect intensity (0.0 to 1.0)
        """
        super().__init__(intensity)
        self.semitones = max(-12.0, min(12.0, semitones))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, PitchShiftEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "pitch_shift"

    def _process_effect(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply pitch shift."""
        if not self._pedalboard_available or self.semitones == 0.0:
            return audio

        try:
            from pedalboard import Pedalboard, PitchShift

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape (channels, samples)
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Apply pitch shift
            board = Pedalboard([PitchShift(semitones=self.semitones)])
            processed = board(audio_float, sample_rate)

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying pitch shift: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        # Pitch shifting adds ~20-50ms latency depending on buffer size
        return 35.0


class RobotVoiceEffect(BaseVoiceEffect):
    """
    Robot voice effect using pitch shift and modulation.

    Creates a characteristic robotic/metallic sound by combining
    pitch shift down with the original signal.

    Examples:
        # Standard robot voice
        effect = RobotVoiceEffect()

        # More robotic with higher intensity
        effect = RobotVoiceEffect(intensity=1.0)
    """

    def __init__(self, intensity: float = 0.8):
        """
        Initialize robot voice effect.

        Args:
            intensity: Effect intensity (0.0 to 1.0)
        """
        super().__init__(intensity)
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, RobotVoiceEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "robot_voice"

    def _process_effect(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply robot voice transformation."""
        if not self._pedalboard_available:
            return audio

        try:
            from pedalboard import Pedalboard, PitchShift, Chorus

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Robot effect: pitch down 5 semitones + chorus for metallic sound
            board = Pedalboard([
                PitchShift(semitones=-5),
                Chorus(rate_hz=1.5, depth=0.3, mix=0.5)
            ])
            processed = board(audio_float, sample_rate)

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying robot voice: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        return 40.0  # Pitch shift + chorus


class HeliumVoiceEffect(BaseVoiceEffect):
    """
    Helium voice effect using high pitch shift.

    Creates the characteristic "chipmunk" or helium-balloon voice
    by shifting pitch up significantly.

    Examples:
        # Standard helium voice
        effect = HeliumVoiceEffect()

        # More extreme pitch shift
        effect = HeliumVoiceEffect(semitones=12)
    """

    def __init__(self, semitones: float = 8.0, intensity: float = 1.0):
        """
        Initialize helium voice effect.

        Args:
            semitones: Pitch shift in semitones (7-12 recommended)
            intensity: Effect intensity (0.0 to 1.0)
        """
        super().__init__(intensity)
        self.semitones = max(7.0, min(12.0, semitones))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, HeliumVoiceEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "helium_voice"

    def _process_effect(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply helium voice transformation."""
        if not self._pedalboard_available:
            return audio

        try:
            from pedalboard import Pedalboard, PitchShift

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Apply high pitch shift
            board = Pedalboard([PitchShift(semitones=self.semitones)])
            processed = board(audio_float, sample_rate)

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying helium voice: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        return 35.0


class EchoEffect(BaseVoiceEffect):
    """
    Echo/delay effect using Pedalboard.

    Creates echo repeats with configurable delay time and feedback.
    Intensity controls the wet/dry mix.

    Examples:
        # Short slapback echo
        effect = EchoEffect(delay_ms=100, feedback=0.3)

        # Long echo with repeats
        effect = EchoEffect(delay_ms=500, feedback=0.6)
    """

    def __init__(self, delay_ms: float = 250.0, feedback: float = 0.5, intensity: float = 0.5):
        """
        Initialize echo effect.

        Args:
            delay_ms: Delay time in milliseconds (100-500)
            feedback: Echo decay/feedback (0.0 to 0.8)
            intensity: Wet/dry mix (0.0 to 1.0)
        """
        super().__init__(intensity)
        self.delay_ms = max(100.0, min(500.0, delay_ms))
        self.feedback = max(0.0, min(0.8, feedback))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, EchoEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "echo"

    def _process_effect(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply echo effect."""
        if not self._pedalboard_available:
            return audio

        try:
            from pedalboard import Pedalboard, Delay

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Apply delay
            delay_seconds = self.delay_ms / 1000.0
            board = Pedalboard([Delay(delay_seconds=delay_seconds, feedback=self.feedback, mix=1.0)])
            processed = board(audio_float, sample_rate)

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying echo: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        return self.delay_ms + 10.0  # Delay time + processing


class ReverbEffect(BaseVoiceEffect):
    """
    Reverb effect using Pedalboard.

    Adds spatial ambience and depth to voice. Configurable room size
    and damping for different acoustic environments.

    Examples:
        # Small room reverb
        effect = ReverbEffect(room_size=0.3, damping=0.5)

        # Large hall reverb
        effect = ReverbEffect(room_size=0.9, damping=0.7)
    """

    def __init__(self, room_size: float = 0.5, damping: float = 0.5, intensity: float = 0.3):
        """
        Initialize reverb effect.

        Args:
            room_size: Room size (0.0 to 1.0): small to large hall
            damping: High frequency absorption (0.0 to 1.0)
            intensity: Wet/dry mix (0.0 to 1.0)
        """
        super().__init__(intensity)
        self.room_size = max(0.0, min(1.0, room_size))
        self.damping = max(0.0, min(1.0, damping))
        self._pedalboard_available = False

        try:
            import pedalboard
            self._pedalboard_available = True
        except ImportError:
            logger.warning("Pedalboard not available, ReverbEffect will be bypassed")

    @property
    def name(self) -> str:
        """Get effect name."""
        return "reverb"

    def _process_effect(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply reverb effect."""
        if not self._pedalboard_available:
            return audio

        try:
            from pedalboard import Pedalboard, Reverb

            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio_float = audio.astype(np.float32) / 32768.0 if audio.dtype == np.int16 else audio.astype(np.float32)
            else:
                audio_float = audio

            # Ensure 2D shape
            if audio_float.ndim == 1:
                audio_float = audio_float.reshape(1, -1)

            # Apply reverb
            board = Pedalboard([Reverb(room_size=self.room_size, damping=self.damping, wet_level=1.0, dry_level=0.0)])
            processed = board(audio_float, sample_rate)

            # Convert back to original dtype
            if audio.dtype == np.int16:
                processed = (processed * 32768.0).astype(np.int16)

            # Restore original shape
            if audio.ndim == 1 and processed.ndim == 2:
                processed = processed.flatten()

            return processed

        except Exception as e:
            logger.error(f"Error applying reverb: {e}")
            return audio

    def get_latency_ms(self) -> float:
        """Get approximate latency."""
        # Reverb latency depends on room size
        return 20.0 + (self.room_size * 50.0)
