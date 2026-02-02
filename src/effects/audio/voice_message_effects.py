"""
Voice message audio effects processing.

Provides VoiceMessageEffects for applying audio effects to voice message
recordings and playback. Designed for non-destructive processing where
effects are applied during playback while preserving the original recording.

Examples:
    # Create effect processor with robot voice
    effects = VoiceMessageEffects(
        create_preset_chain("robot")
    )

    # Process audio data
    processed = effects.process_audio(audio_data, 48000)

    # Process entire file (for pre-send processing)
    output_path = effects.process_file(
        Path("voice.ogg"),
        Path("voice_robot.ogg")
    )

    # Create preview (first 3 seconds)
    preview = effects.create_preview(audio_data, 48000, duration=3.0)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
from pyogg import OpusFile

from .effect_chain import AudioEffectChain

logger = logging.getLogger(__name__)


@dataclass
class VoiceMessageEffectMetadata:
    """
    Metadata describing effects applied to a voice message.

    Used to store effect configuration alongside voice messages,
    enabling consistent playback across devices and allowing
    users to change effects after recording.

    Attributes:
        effect_preset: Name of preset used, or "custom" for manual chains
        effect_chain: Serialized effect settings (from AudioEffectChain.to_dict())
        applied_during: When effects were/will be applied ("playback" or "recording")
    """
    effect_preset: str
    effect_chain: List[Dict[str, Any]]
    applied_during: str = "playback"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for storage.

        Returns:
            Dictionary representation for JSON serialization
        """
        return {
            "effect_preset": self.effect_preset,
            "effect_chain": self.effect_chain,
            "applied_during": self.applied_during
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceMessageEffectMetadata":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            VoiceMessageEffectMetadata instance
        """
        return cls(
            effect_preset=data.get("effect_preset", "none"),
            effect_chain=data.get("effect_chain", []),
            applied_during=data.get("applied_during", "playback")
        )


class VoiceMessageEffects:
    """
    Applies audio effects to voice message recordings.

    Designed for non-destructive processing where the original recording
    is preserved and effects are applied during playback. This allows
    users to change or remove effects after recording.

    The processor can also be used to pre-process recordings before sending,
    creating a new file with effects baked in (though non-destructive
    playback-time processing is recommended).

    Examples:
        # Create with effect chain
        from src.effects.audio import create_preset_chain

        effects = VoiceMessageEffects(
            create_preset_chain("robot")
        )

        # Process audio data
        processed_audio = effects.process_audio(
            audio_data,
            sample_rate=48000
        )

        # Process entire file
        output_path = effects.process_file(
            input_path=Path("recording.ogg"),
            output_path=Path("recording_robot.ogg")
        )

        # Create preview for UI
        preview_audio = effects.create_preview(
            audio_data,
            sample_rate=48000,
            duration=3.0
        )

        # Change effect chain
        effects.effect_chain = create_preset_chain("helium")

        # Get metadata for storage
        metadata = VoiceMessageEffectMetadata(
            effect_preset="robot",
            effect_chain=effects.effect_chain.to_dict()["effects"],
            applied_during="playback"
        )
    """

    def __init__(self, effect_chain: Optional[AudioEffectChain] = None):
        """
        Initialize voice message effects processor.

        Args:
            effect_chain: Effect chain to apply, or None for empty chain
        """
        self._effect_chain = effect_chain or AudioEffectChain()

    @property
    def effect_chain(self) -> AudioEffectChain:
        """Get current effect chain."""
        return self._effect_chain

    @effect_chain.setter
    def effect_chain(self, chain: AudioEffectChain) -> None:
        """
        Set effect chain.

        Args:
            chain: New effect chain to use
        """
        self._effect_chain = chain
        logger.debug("Updated effect chain")

    def process_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply effect chain to audio data.

        Args:
            audio_data: Audio data as numpy array (float32, mono)
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio with same shape as input
        """
        if len(self._effect_chain.effects) == 0:
            # No effects, return original
            return audio_data

        try:
            processed = self._effect_chain.process(audio_data, sample_rate)

            # Ensure output has same shape as input
            if processed.shape != audio_data.shape:
                logger.warning(
                    f"Effect chain changed audio shape from {audio_data.shape} "
                    f"to {processed.shape}, clipping/padding"
                )
                if len(processed) > len(audio_data):
                    processed = processed[:len(audio_data)]
                else:
                    processed = np.pad(
                        processed,
                        (0, len(audio_data) - len(processed)),
                        mode='constant'
                    )

            return processed

        except Exception as e:
            logger.error(f"Error processing audio with effects: {e}")
            # Return original audio on error
            return audio_data

    def process_file(self, input_path: Path, output_path: Path) -> Path:
        """
        Process voice message file and save to new file.

        Loads Opus/Ogg file, applies effects, and saves result as WAV.
        Useful for pre-processing before sending if user wants
        effects "baked in" rather than applied during playback.

        Note: Output is WAV format since encoding back to Opus would require
        libopusenc integration. For production use, consider using
        VoiceMessageRecorder's encoding pipeline after processing.

        Args:
            input_path: Path to input .ogg file
            output_path: Path to output file (will be .wav)

        Returns:
            Path to output file (with .wav extension)

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If processing fails
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            # Decode input file
            opus_file = OpusFile(str(input_path))
            sample_rate = opus_file.frequency
            samples = opus_file.buffer_length

            # Convert to float32 numpy array
            audio_int16 = np.ctypeslib.as_array(opus_file.buffer, shape=(samples,))
            audio_float = audio_int16.astype(np.float32) / 32768.0

            # Convert to mono if stereo
            if opus_file.channels > 1:
                audio_float = audio_float.reshape(-1, opus_file.channels).mean(axis=1)

            # Apply effects
            processed = self.process_audio(audio_float, sample_rate)

            # Save as WAV (simple format, no external dependencies)
            # Convert back to int16 for WAV
            processed_int16 = (processed * 32767).astype(np.int16)

            # Change extension to .wav
            output_path = output_path.with_suffix('.wav')

            # Write simple WAV file using wave module (stdlib)
            import wave
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(processed_int16.tobytes())

            logger.info(f"Processed voice message: {input_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to process voice message file: {e}")
            raise RuntimeError(f"Failed to process voice message: {e}") from e

    def create_preview(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        duration: float = 3.0
    ) -> np.ndarray:
        """
        Process first N seconds of audio as preview.

        Allows user to hear how effects will sound before committing
        to full playback or sending with effects baked in.

        Args:
            audio_data: Full audio data
            sample_rate: Sample rate in Hz
            duration: Preview duration in seconds (default: 3.0)

        Returns:
            Processed preview audio (may be shorter than duration if audio is short)
        """
        # Calculate sample count for preview duration
        preview_samples = int(duration * sample_rate)

        # Clamp to available audio
        preview_samples = min(preview_samples, len(audio_data))

        # Extract preview segment
        preview_audio = audio_data[:preview_samples]

        # Apply effects
        processed_preview = self.process_audio(preview_audio, sample_rate)

        logger.debug(f"Created {duration}s preview with effects")
        return processed_preview
