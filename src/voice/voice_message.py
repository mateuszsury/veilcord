"""
Voice message recording and playback.

Provides VoiceMessageRecorder for capturing audio to Opus-encoded .ogg files
and VoiceMessagePlayer for playing back voice messages.

Uses PyOgg's libopusenc bindings for streaming Opus encoding directly to disk,
avoiding memory bloat for long recordings (up to 5 minutes).
"""

import asyncio
import ctypes
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from pyogg.opus import (
    ope_encoder_create_file,
    ope_encoder_write_float,
    ope_encoder_drain,
    ope_encoder_destroy,
    ope_comments_create,
    ope_comments_destroy,
    OPE_OK,
    c_int,
    c_float_p,
    POINTER,
    c_float,
)
from pyogg import OpusFile

from src.voice.models import VoiceMessageMetadata
from src.storage.paths import get_voice_messages_dir
from src.effects.audio.voice_message_effects import VoiceMessageEffects, VoiceMessageEffectMetadata
from src.effects.audio import AudioEffectChain

logger = logging.getLogger(__name__)


class VoiceMessageRecorder:
    """
    Records voice messages to Opus-encoded .ogg files.

    Uses PyOgg's libopusenc for streaming Opus encoding directly to disk.
    Supports configurable device selection and enforces a 5-minute maximum
    duration to prevent excessively large files.

    Example:
        recorder = VoiceMessageRecorder()
        path = await recorder.start_recording()
        await asyncio.sleep(5)  # Record for 5 seconds
        metadata = await recorder.stop_recording()
        print(f"Recorded {metadata.duration_seconds}s to {metadata.file_path}")
    """

    MAX_DURATION = 300  # 5 minutes in seconds
    MIN_DURATION = 0.5  # Minimum valid recording duration

    def __init__(self, device_id: Optional[int] = None, sample_rate: int = 48000):
        """
        Initialize voice message recorder.

        Args:
            device_id: Input device ID (None for default device).
            sample_rate: Sample rate in Hz (48000 is Opus standard).
        """
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.channels = 1  # Mono for voice

        self._stream: Optional[sd.InputStream] = None
        self._encoder = None  # OggOpusEnc pointer
        self._comments = None  # OpeComments pointer
        self._recording = False
        self._start_time: Optional[float] = None
        self._output_path: Optional[Path] = None
        self._stop_flag = False  # Signal to stop from callback
        self._lock = threading.Lock()

        # Effect metadata for recording
        self._effect_chain: Optional[AudioEffectChain] = None
        self._effect_metadata: Optional[VoiceMessageEffectMetadata] = None

        # Callbacks for UI updates
        self.on_duration_update: Optional[Callable[[float], None]] = None
        self.on_max_duration_reached: Optional[Callable[[], None]] = None

    def _audio_callback(self, indata: np.ndarray, frames: int,
                        time_info: dict, status: sd.CallbackFlags) -> None:
        """
        Audio callback - streams audio to Opus encoder.

        Called from sounddevice thread. Kept minimal per research pitfall #5.
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        if not self._recording:
            return

        # Check duration limit
        elapsed = time.time() - self._start_time
        if elapsed >= self.MAX_DURATION:
            self._stop_flag = True
            if self.on_max_duration_reached:
                try:
                    self.on_max_duration_reached()
                except Exception as e:
                    logger.error(f"Error in max duration callback: {e}")
            return

        # Encode and write to file
        with self._lock:
            if self._encoder is None:
                return

            # Convert to contiguous float32 array
            audio_data = np.ascontiguousarray(indata.flatten(), dtype=np.float32)

            # Create ctypes pointer to audio data
            audio_ptr = audio_data.ctypes.data_as(POINTER(c_float))

            # Write to encoder (handles both encoding and Ogg muxing)
            result = ope_encoder_write_float(
                self._encoder,
                audio_ptr,
                frames
            )

            if result != OPE_OK:
                logger.error(f"Error encoding audio: {result}")

    def set_recording_effects(self, chain: AudioEffectChain, preset_name: str = "custom") -> None:
        """
        Set effect chain to apply to recording.

        Note: Per design, effects are applied during playback (non-destructive),
        but this method allows storing effect metadata with the recording for
        automatic application during playback.

        Args:
            chain: AudioEffectChain to store as metadata
            preset_name: Name of preset used, or "custom" for manual chains
        """
        self._effect_chain = chain
        self._effect_metadata = VoiceMessageEffectMetadata(
            effect_preset=preset_name,
            effect_chain=chain.to_dict()["effects"],
            applied_during="playback"
        )
        logger.info(f"Set recording effect metadata: {preset_name}")

    async def start_recording(self) -> Path:
        """
        Start recording voice message.

        Returns:
            Path where recording will be saved.

        Raises:
            RuntimeError: If already recording.
        """
        if self._recording:
            raise RuntimeError("Already recording")

        # Create output directory if needed
        output_dir = get_voice_messages_dir()

        # Generate unique filename
        filename = f"voice_{uuid.uuid4().hex}.ogg"
        self._output_path = output_dir / filename

        # Create comments (required for Ogg metadata)
        self._comments = ope_comments_create()
        if self._comments is None:
            raise RuntimeError("Failed to create Opus comments")

        # Create encoder - writes directly to file
        error_code = c_int()
        self._encoder = ope_encoder_create_file(
            str(self._output_path).encode('utf-8'),
            self._comments,
            self.sample_rate,
            self.channels,
            0,  # family (0 = mono/stereo)
            ctypes.byref(error_code)
        )

        if self._encoder is None or error_code.value != OPE_OK:
            if self._comments:
                ope_comments_destroy(self._comments)
                self._comments = None
            raise RuntimeError(f"Failed to create Opus encoder: error {error_code.value}")

        # Calculate frame size for 20ms chunks (Opus standard)
        blocksize = int(self.sample_rate * 0.020)  # 20ms

        # Create input stream
        self._stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            callback=self._audio_callback,
            blocksize=blocksize
        )

        # Start recording
        self._recording = True
        self._stop_flag = False
        self._start_time = time.time()
        self._stream.start()

        logger.info(f"Started recording to {self._output_path}")
        return self._output_path

    async def stop_recording(self) -> Optional[VoiceMessageMetadata]:
        """
        Stop recording and finalize file.

        Returns:
            VoiceMessageMetadata with duration and path, or None if nothing
            recorded (e.g., too short).
        """
        if not self._recording:
            return None

        self._recording = False

        # Stop and close stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Calculate duration before closing encoder
        duration = time.time() - self._start_time if self._start_time else 0

        # Drain and close encoder
        with self._lock:
            if self._encoder:
                ope_encoder_drain(self._encoder)
                ope_encoder_destroy(self._encoder)
                self._encoder = None

            if self._comments:
                ope_comments_destroy(self._comments)
                self._comments = None

        logger.info(f"Stopped recording, duration: {duration:.1f}s")

        # Check minimum duration
        if duration < self.MIN_DURATION:
            logger.info("Recording too short, deleting")
            if self._output_path and self._output_path.exists():
                self._output_path.unlink()
            self._output_path = None
            self._start_time = None
            return None

        # Create metadata with effect information if available
        effects_dict = None
        if self._effect_metadata:
            effects_dict = self._effect_metadata.to_dict()

        metadata = VoiceMessageMetadata.create(
            duration_seconds=duration,
            file_path=str(self._output_path),
            effects=effects_dict
        )

        self._output_path = None
        self._start_time = None

        return metadata

    def get_duration(self) -> float:
        """Get current recording duration in seconds."""
        if not self._recording or self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    async def cancel(self) -> None:
        """Cancel recording and delete partial file."""
        was_recording = self._recording
        self._recording = False

        # Stop stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Close encoder without draining (discard data)
        with self._lock:
            if self._encoder:
                ope_encoder_destroy(self._encoder)
                self._encoder = None

            if self._comments:
                ope_comments_destroy(self._comments)
                self._comments = None

        # Delete partial file
        if self._output_path and self._output_path.exists():
            self._output_path.unlink()
            logger.info(f"Cancelled recording, deleted {self._output_path}")

        self._output_path = None
        self._start_time = None


class VoiceMessagePlayer:
    """
    Plays back voice messages from .ogg files.

    Uses PyOgg's OpusFile for decoding and sounddevice for playback.
    Supports pause/resume and seeking.

    Example:
        player = VoiceMessagePlayer()
        duration = await player.load(Path("voice.ogg"))
        await player.play()
        await asyncio.sleep(duration)
    """

    def __init__(self, device_id: Optional[int] = None):
        """
        Initialize voice message player.

        Args:
            device_id: Output device ID (None for default device).
        """
        self.device_id = device_id

        self._stream: Optional[sd.OutputStream] = None
        self._playing = False
        self._paused = False
        self._current_file: Optional[Path] = None
        self._duration = 0.0
        self._sample_rate = 48000  # Opus standard
        self._channels = 1

        # Audio data buffer (decoded PCM)
        self._audio_data: Optional[np.ndarray] = None
        self._raw_audio_data: Optional[np.ndarray] = None  # Original unprocessed audio
        self._sample_index = 0
        self._playback_complete = False
        self._lock = threading.Lock()

        # Audio effects
        self._effects: Optional[VoiceMessageEffects] = None
        self._effect_metadata: Optional[VoiceMessageEffectMetadata] = None
        self.effects_enabled: bool = False

        # Callbacks for UI updates
        self.on_position_update: Optional[Callable[[float], None]] = None
        self.on_playback_complete: Optional[Callable[[], None]] = None

    def set_effects(self, effects: VoiceMessageEffects) -> None:
        """
        Set effect processor for playback.

        Effects will be applied during playback if effects_enabled is True.
        Can be called before or during playback.

        Args:
            effects: VoiceMessageEffects instance with configured effect chain
        """
        self._effects = effects
        logger.info("Set voice message effects")

        # If audio is loaded and effects are enabled, reprocess it
        if self._raw_audio_data is not None and self.effects_enabled:
            self._apply_effects_to_loaded_audio()

    def set_effect_chain(self, chain: AudioEffectChain) -> None:
        """
        Convenience method to set effect chain directly.

        Creates VoiceMessageEffects instance internally.

        Args:
            chain: AudioEffectChain to apply
        """
        self._effects = VoiceMessageEffects(chain)
        logger.info("Set voice message effect chain")

        # If audio is loaded and effects are enabled, reprocess it
        if self._raw_audio_data is not None and self.effects_enabled:
            self._apply_effects_to_loaded_audio()

    def get_effect_metadata(self) -> Optional[VoiceMessageEffectMetadata]:
        """
        Get current effect settings as metadata.

        Returns:
            VoiceMessageEffectMetadata if effects are set, None otherwise
        """
        if self._effect_metadata:
            return self._effect_metadata

        if self._effects:
            # Create metadata from current effect chain
            return VoiceMessageEffectMetadata(
                effect_preset="custom",
                effect_chain=self._effects.effect_chain.to_dict()["effects"],
                applied_during="playback"
            )

        return None

    def _apply_effects_to_loaded_audio(self) -> None:
        """
        Apply current effects to loaded audio data.

        Internal method called when effects change or are enabled.
        """
        if self._raw_audio_data is None or self._effects is None:
            return

        try:
            # Process raw audio through effects
            self._audio_data = self._effects.process_audio(
                self._raw_audio_data,
                self._sample_rate
            )
            logger.debug("Applied effects to loaded audio")
        except Exception as e:
            logger.error(f"Error applying effects to audio: {e}")
            # Fall back to raw audio on error
            self._audio_data = self._raw_audio_data.copy()

    async def preview_with_effects(self, duration: float = 3.0) -> None:
        """
        Play first N seconds with current effects as preview.

        Allows user to hear how message will sound with effects
        before committing to full playback.

        Args:
            duration: Preview duration in seconds (default: 3.0)

        Raises:
            RuntimeError: If no file is loaded or no effects set
        """
        if self._raw_audio_data is None:
            raise RuntimeError("No file loaded")

        if self._effects is None:
            raise RuntimeError("No effects set")

        # Create preview
        preview_audio = self._effects.create_preview(
            self._raw_audio_data,
            self._sample_rate,
            duration
        )

        # Temporarily swap audio data for preview
        original_audio = self._audio_data
        original_index = self._sample_index
        original_enabled = self.effects_enabled

        try:
            self._audio_data = preview_audio
            self._sample_index = 0
            self.effects_enabled = True

            # Play preview
            await self.play()

            # Wait for preview to complete (or duration)
            preview_samples = len(preview_audio)
            preview_duration = preview_samples / self._sample_rate
            await asyncio.sleep(preview_duration + 0.1)  # Small buffer

        finally:
            # Restore original state
            await self.stop()
            self._audio_data = original_audio
            self._sample_index = original_index
            self.effects_enabled = original_enabled

    def _playback_callback(self, outdata: np.ndarray, frames: int,
                           time_info: dict, status: sd.CallbackFlags) -> None:
        """Audio callback for playback."""
        if status:
            logger.warning(f"Playback callback status: {status}")

        with self._lock:
            if self._paused or not self._playing or self._audio_data is None:
                outdata.fill(0)
                return

            # Calculate how many samples to copy
            remaining = len(self._audio_data) - self._sample_index
            to_copy = min(frames, remaining)

            if to_copy > 0:
                # Copy audio data to output buffer
                outdata[:to_copy, 0] = self._audio_data[self._sample_index:self._sample_index + to_copy]
                self._sample_index += to_copy

            # Fill remaining with silence
            if to_copy < frames:
                outdata[to_copy:].fill(0)
                self._playback_complete = True

    async def load(self, file_path: Path, metadata: Optional[VoiceMessageMetadata] = None) -> float:
        """
        Load voice message file for playback.

        If metadata with effects is provided, those effects will be automatically
        applied during playback (if effects_enabled is True).

        Args:
            file_path: Path to .ogg voice message file.
            metadata: Optional metadata with effect information

        Returns:
            Duration in seconds.

        Raises:
            FileNotFoundError: If file doesn't exist.
            RuntimeError: If file can't be decoded.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Voice message not found: {file_path}")

        # Load effect metadata if provided
        if metadata and metadata.effects:
            try:
                self._effect_metadata = VoiceMessageEffectMetadata.from_dict(metadata.effects)
                # If effects are enabled and we don't have effects set, create from metadata
                # (User can override by calling set_effects/set_effect_chain)
                if self.effects_enabled and self._effects is None:
                    # Note: Would need effect registry to fully reconstruct chain
                    # For now, just store the metadata
                    logger.info("Loaded effect metadata from voice message")
            except Exception as e:
                logger.warning(f"Failed to load effect metadata: {e}")

        # Stop any current playback
        await self.stop()

        # Decode the entire file (voice messages are max 5 min = ~5MB decoded)
        try:
            opus_file = OpusFile(str(file_path))

            self._sample_rate = opus_file.frequency
            self._channels = opus_file.channels
            samples = opus_file.buffer_length

            # Convert ctypes pointer to numpy array
            # OpusFile.buffer is LP_c_short (ctypes pointer to int16 array)
            audio_int16 = np.ctypeslib.as_array(opus_file.buffer, shape=(samples,))

            # Convert to float32 normalized [-1.0, 1.0]
            audio_float = audio_int16.astype(np.float32) / 32768.0

            # If stereo, convert to mono for consistency
            if self._channels > 1:
                # Reshape and average channels
                audio_float = audio_float.reshape(-1, self._channels).mean(axis=1)
                samples = samples // self._channels

            # Store raw audio (unprocessed)
            self._raw_audio_data = audio_float.copy()

            # Apply effects if enabled
            if self.effects_enabled and self._effects is not None:
                self._audio_data = self._effects.process_audio(
                    self._raw_audio_data,
                    self._sample_rate
                )
                logger.debug("Applied effects during load")
            else:
                # Use raw audio for playback
                self._audio_data = self._raw_audio_data.copy()

            self._duration = samples / self._sample_rate
            self._current_file = file_path
            self._sample_index = 0
            self._playback_complete = False

            logger.info(f"Loaded {file_path}: {self._duration:.1f}s at {self._sample_rate}Hz")

            return self._duration

        except Exception as e:
            logger.error(f"Failed to load voice message: {e}")
            raise RuntimeError(f"Failed to decode voice message: {e}") from e

    async def play(self) -> None:
        """
        Start or resume playback.

        Raises:
            RuntimeError: If no file is loaded.
        """
        if self._audio_data is None:
            raise RuntimeError("No file loaded")

        if self._playing:
            if self._paused:
                self._paused = False
            return

        # Create output stream
        self._stream = sd.OutputStream(
            device=self.device_id,
            samplerate=self._sample_rate,
            channels=1,  # Always output mono
            dtype=np.float32,
            callback=self._playback_callback,
            blocksize=int(self._sample_rate * 0.020)  # 20ms
        )

        self._playing = True
        self._paused = False
        self._playback_complete = False
        self._stream.start()

        # Start background task to monitor playback completion
        asyncio.create_task(self._monitor_playback())

        logger.info("Started playback")

    async def _monitor_playback(self) -> None:
        """Monitor playback and fire completion callback."""
        while self._playing and not self._playback_complete:
            await asyncio.sleep(0.05)  # Check every 50ms

        if self._playback_complete and self._playing:
            await self.stop()
            if self.on_playback_complete:
                try:
                    self.on_playback_complete()
                except Exception as e:
                    logger.error(f"Error in playback complete callback: {e}")

    def pause(self) -> None:
        """Pause playback."""
        self._paused = True
        logger.info("Paused playback")

    def resume(self) -> None:
        """Resume paused playback."""
        self._paused = False
        logger.info("Resumed playback")

    async def stop(self) -> None:
        """Stop playback and reset position."""
        self._playing = False
        self._paused = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            self._sample_index = 0

        logger.info("Stopped playback")

    def seek(self, position_seconds: float) -> None:
        """
        Seek to position in seconds.

        Args:
            position_seconds: Target position in seconds.
        """
        if self._audio_data is None:
            return

        # Clamp to valid range
        position_seconds = max(0, min(position_seconds, self._duration))

        with self._lock:
            self._sample_index = int(position_seconds * self._sample_rate)

        logger.info(f"Seeked to {position_seconds:.1f}s")

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        with self._lock:
            return self._sample_index / self._sample_rate if self._sample_rate > 0 else 0.0

    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self._duration

    def is_playing(self) -> bool:
        """Check if currently playing (not paused)."""
        return self._playing and not self._paused

    @staticmethod
    def get_file_duration(file_path: Path) -> float:
        """
        Get duration of voice message file without loading for playback.

        Args:
            file_path: Path to .ogg voice message file.

        Returns:
            Duration in seconds.

        Raises:
            FileNotFoundError: If file doesn't exist.
            RuntimeError: If file can't be decoded.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Voice message not found: {file_path}")

        try:
            opus_file = OpusFile(str(file_path))
            # buffer_length gives total samples (already accounts for structure)
            samples = opus_file.buffer_length
            if opus_file.channels > 1:
                samples = samples // opus_file.channels
            duration = samples / opus_file.frequency
            return duration
        except Exception as e:
            raise RuntimeError(f"Failed to get duration: {e}") from e
