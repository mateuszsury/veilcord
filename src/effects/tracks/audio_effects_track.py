"""
Audio effects track wrapper for aiortc MediaStreamTrack.

Wraps MicrophoneAudioTrack or any AudioStreamTrack with real-time
audio effect processing via AudioEffectChain.
"""

import logging
import time
from typing import Optional

import numpy as np
from aiortc import AudioStreamTrack
from av import AudioFrame

from src.effects.audio import AudioEffectChain

logger = logging.getLogger(__name__)


class AudioEffectsTrack(AudioStreamTrack):
    """
    AudioStreamTrack wrapper that applies effects in real-time.

    Wraps a source audio track (like MicrophoneAudioTrack) and processes
    frames through an AudioEffectChain before passing them to WebRTC.

    Effects can be toggled on/off or swapped mid-call without interruption.

    Usage:
        # Wrap mic track with effects
        mic_track = MicrophoneAudioTrack()
        effects_track = AudioEffectsTrack(
            source_track=mic_track,
            effect_chain=chain
        )
        pc.addTrack(effects_track)

        # Toggle effects mid-call
        effects_track.effects_enabled = False

        # Swap effect chain mid-call
        effects_track.set_effect_chain(new_chain)
    """

    kind = "audio"

    def __init__(
        self,
        source_track: AudioStreamTrack,
        effect_chain: Optional[AudioEffectChain] = None
    ):
        """
        Initialize audio effects track.

        Args:
            source_track: Source audio track to wrap (e.g., MicrophoneAudioTrack)
            effect_chain: Effect chain to apply, or None for empty chain
        """
        super().__init__()
        self._source_track = source_track
        self._effect_chain = effect_chain if effect_chain is not None else AudioEffectChain()
        self._effects_enabled = True

        # Performance monitoring
        self._processing_times = []
        self._warning_threshold_ms = 15.0  # Half of 20ms frame time

        logger.info(f"AudioEffectsTrack initialized wrapping {type(source_track).__name__}")

    @property
    def source_track(self) -> AudioStreamTrack:
        """Get the wrapped source track."""
        return self._source_track

    @property
    def effect_chain(self) -> AudioEffectChain:
        """Get the current effect chain."""
        return self._effect_chain

    @effect_chain.setter
    def effect_chain(self, chain: AudioEffectChain):
        """
        Set new effect chain (can be changed mid-call).

        Args:
            chain: New AudioEffectChain to use
        """
        self._effect_chain = chain
        logger.info("Effect chain updated")

    def set_effect_chain(self, chain: AudioEffectChain):
        """
        Set new effect chain (convenience method).

        Args:
            chain: New AudioEffectChain to use
        """
        self.effect_chain = chain

    @property
    def effects_enabled(self) -> bool:
        """Check if effects are enabled."""
        return self._effects_enabled

    @effects_enabled.setter
    def effects_enabled(self, value: bool):
        """
        Enable or disable effects (master toggle).

        When disabled, audio passes through unprocessed.

        Args:
            value: True to enable effects, False to disable
        """
        self._effects_enabled = value
        logger.info(f"Effects {'enabled' if value else 'disabled'}")

    async def recv(self) -> AudioFrame:
        """
        Receive and process audio frame.

        Gets frame from source track, applies effects if enabled,
        and returns processed frame.

        Returns:
            Processed AudioFrame with effects applied

        Raises:
            Exception: If source track fails
        """
        # Get frame from source track
        frame = await self._source_track.recv()

        # If effects disabled or no chain, return original
        if not self._effects_enabled or not self._effect_chain or not self._effect_chain.effects:
            return frame

        try:
            # Start processing timer
            start_time = time.perf_counter()

            # Convert frame to numpy array
            audio_data = self._frame_to_numpy(frame)

            # Process through effect chain
            processed_data = self._effect_chain.process(audio_data, frame.sample_rate)

            # Convert back to AudioFrame
            processed_frame = self._numpy_to_frame(processed_data, frame)

            # Monitor processing time
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            self._monitor_performance(processing_time_ms)

            return processed_frame

        except Exception as e:
            logger.error(f"Error processing audio effects: {e}")
            # Return original frame on error
            return frame

    def _frame_to_numpy(self, frame: AudioFrame) -> np.ndarray:
        """
        Convert av.AudioFrame to numpy array.

        Handles different audio formats (s16, flt, etc.).

        Args:
            frame: Input AudioFrame

        Returns:
            Audio data as float32 numpy array (mono or stereo)
        """
        # Use av's built-in numpy conversion
        # to_ndarray() returns shape (channels, samples)
        audio_array = frame.to_ndarray()

        # Convert to float32 for processing
        if audio_array.dtype == np.int16:
            # Convert s16 to float32 [-1.0, 1.0]
            audio_array = audio_array.astype(np.float32) / 32768.0
        elif audio_array.dtype == np.float32:
            # Already float32
            pass
        else:
            # Convert other types to float32
            audio_array = audio_array.astype(np.float32)

        # Effect chain expects (samples,) or (samples, channels)
        # av.AudioFrame.to_ndarray() gives (channels, samples)
        # Transpose to (samples, channels)
        if audio_array.ndim == 2:
            audio_array = audio_array.T

        # If mono (1D array), keep as is
        return audio_array

    def _numpy_to_frame(self, audio_data: np.ndarray, template: AudioFrame) -> AudioFrame:
        """
        Create AudioFrame from numpy array.

        Preserves timing information from template frame.

        Args:
            audio_data: Processed audio as numpy array
            template: Original frame for timing metadata

        Returns:
            New AudioFrame with processed audio
        """
        # Convert back to int16 for transmission
        if audio_data.dtype == np.float32:
            # Clip to valid range and convert to int16
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_int16 = (audio_data * 32767).astype(np.int16)
        else:
            audio_int16 = audio_data.astype(np.int16)

        # AudioFrame expects (channels, samples) layout
        if audio_int16.ndim == 1:
            # Mono: reshape to (1, samples)
            audio_int16 = audio_int16.reshape(1, -1)
        elif audio_int16.ndim == 2:
            # Stereo or multi-channel: transpose from (samples, channels) to (channels, samples)
            audio_int16 = audio_int16.T

        # Create new AudioFrame
        new_frame = AudioFrame.from_ndarray(
            audio_int16,
            format='s16',
            layout=template.layout.name
        )

        # Copy timing metadata from template
        new_frame.pts = template.pts
        new_frame.time_base = template.time_base
        new_frame.sample_rate = template.sample_rate

        return new_frame

    def _monitor_performance(self, processing_time_ms: float):
        """
        Monitor processing time and warn if excessive.

        Tracks rolling average and warns if processing exceeds half
        of frame time (15ms for 20ms frames).

        Args:
            processing_time_ms: Processing time in milliseconds
        """
        self._processing_times.append(processing_time_ms)

        # Keep last 100 measurements
        if len(self._processing_times) > 100:
            self._processing_times.pop(0)

        # Warn if exceeds threshold
        if processing_time_ms > self._warning_threshold_ms:
            avg_time = sum(self._processing_times) / len(self._processing_times)
            logger.warning(
                f"Audio effect processing time ({processing_time_ms:.1f}ms) "
                f"exceeds threshold ({self._warning_threshold_ms}ms). "
                f"Average: {avg_time:.1f}ms. "
                "Consider disabling some effects to reduce latency."
            )

    async def stop(self):
        """
        Stop the effects track and source track.

        Cleans up resources and stops underlying source track.
        """
        try:
            # Stop source track
            if self._source_track:
                await self._source_track.stop()

            # Clean up effect chain resources (if needed)
            if self._effect_chain:
                # Effect chains don't currently have cleanup,
                # but this hook is here for future use
                pass

            logger.info("AudioEffectsTrack stopped")

        except Exception as e:
            logger.error(f"Error stopping AudioEffectsTrack: {e}")

    def get_average_processing_time_ms(self) -> float:
        """
        Get average processing time over recent frames.

        Returns:
            Average processing time in milliseconds
        """
        if not self._processing_times:
            return 0.0
        return sum(self._processing_times) / len(self._processing_times)
