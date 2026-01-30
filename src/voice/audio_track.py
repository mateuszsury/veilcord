"""
Audio track implementations for WebRTC voice calls.

Provides custom audio stream tracks for capturing microphone input
and playing back received audio via sounddevice.
"""

import asyncio
import fractions
import logging
from queue import Empty, Full
from typing import Optional

import numpy as np
import sounddevice as sd
from aiortc import AudioStreamTrack
from av import AudioFrame

logger = logging.getLogger(__name__)


class MicrophoneAudioTrack(AudioStreamTrack):
    """
    Custom AudioStreamTrack that captures audio from a microphone.

    Uses sounddevice for cross-platform audio capture and produces
    properly-timed av.AudioFrame objects for WebRTC transmission.

    Attributes:
        kind: Media track kind, always "audio" for audio tracks
    """

    kind = "audio"

    def __init__(self, device_id: Optional[int] = None, sample_rate: int = 48000):
        """
        Initialize the microphone audio track.

        Args:
            device_id: Input device ID, or None for default device
            sample_rate: Audio sample rate in Hz (default 48000 for Opus codec)
        """
        super().__init__()
        self.device_id = device_id
        self.sample_rate = sample_rate
        # 20ms frames are standard for WebRTC audio
        self.samples_per_frame = int(sample_rate * 0.020)
        # Queue for audio data from callback thread
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._stream: Optional[sd.InputStream] = None
        self._running = False
        self._pts = 0  # Presentation timestamp counter
        self._muted = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def muted(self) -> bool:
        """Check if track is muted."""
        return self._muted

    @muted.setter
    def muted(self, value: bool):
        """Set mute state."""
        self._muted = value
        logger.debug(f"Microphone mute set to: {value}")

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status):
        """
        Audio callback from sounddevice thread.

        Keep this minimal per best practices - just copy to queue.
        Called from audio thread, not asyncio event loop.

        Args:
            indata: Input audio data as numpy array
            frames: Number of frames
            time: Timing info
            status: Status flags (e.g., buffer overflow)
        """
        if status:
            logger.warning(f"Audio input status: {status}")

        try:
            # Copy data and put into thread-safe queue
            # Use call_soon_threadsafe to interact with asyncio queue from callback thread
            if self._loop and self._running:
                self._loop.call_soon_threadsafe(
                    self._put_audio_data, indata.copy()
                )
        except Exception as e:
            logger.debug(f"Failed to queue audio data: {e}")

    def _put_audio_data(self, data: np.ndarray):
        """Put audio data into queue (called from event loop thread)."""
        try:
            self._queue.put_nowait(data)
        except asyncio.QueueFull:
            # Drop frame if queue is full - prevents memory bloat
            pass

    async def start(self):
        """Start audio capture from microphone."""
        if self._running:
            return

        self._loop = asyncio.get_event_loop()

        self._stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=1,  # Mono for voice
            dtype=np.int16,  # 16-bit signed integer
            blocksize=self.samples_per_frame,
            callback=self._audio_callback
        )
        self._stream.start()
        self._running = True
        logger.info(f"Started microphone capture (device={self.device_id}, rate={self.sample_rate})")

    async def recv(self) -> AudioFrame:
        """
        Get next audio frame for WebRTC transmission.

        Called by aiortc to get audio data to send to remote peer.

        Returns:
            av.AudioFrame with properly formatted audio data
        """
        if not self._running:
            await self.start()

        # Get audio data from queue
        audio_data = await self._queue.get()

        # Create audio frame
        frame = AudioFrame(
            format="s16",
            layout="mono",
            samples=self.samples_per_frame
        )

        # Fill frame with audio data or silence if muted
        if self._muted:
            # Return silence when muted
            silent_data = np.zeros(self.samples_per_frame, dtype=np.int16)
            frame.planes[0].update(silent_data.tobytes())
        else:
            # Ensure correct shape and type
            audio_bytes = audio_data.flatten().astype(np.int16).tobytes()
            frame.planes[0].update(audio_bytes)

        # Set frame metadata
        frame.sample_rate = self.sample_rate
        frame.pts = self._pts
        frame.time_base = fractions.Fraction(1, self.sample_rate)

        # Increment presentation timestamp
        self._pts += self.samples_per_frame

        return frame

    async def stop(self):
        """Stop audio capture and clean up resources."""
        self._running = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Stopped microphone capture")

        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self._pts = 0
        self._loop = None


class AudioPlaybackTrack:
    """
    Plays audio received from remote peer via sounddevice.

    Receives audio frames from aiortc remote track and outputs
    to the selected audio device.
    """

    def __init__(self, device_id: Optional[int] = None, sample_rate: int = 48000):
        """
        Initialize the audio playback track.

        Args:
            device_id: Output device ID, or None for default device
            sample_rate: Audio sample rate in Hz (default 48000)
        """
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.samples_per_frame = int(sample_rate * 0.020)
        # Thread-safe queue for audio data
        self._queue = asyncio.Queue(maxsize=100)
        self._stream: Optional[sd.OutputStream] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # Sync queue for callback thread
        self._sync_queue: "asyncio.Queue[np.ndarray]" = asyncio.Queue(maxsize=100)
        # Use a simple list as buffer for callback (thread-safe enough for our use)
        self._buffer: list = []
        self._buffer_lock = asyncio.Lock()

    def _audio_callback(self, outdata: np.ndarray, frames: int, time, status):
        """
        Audio callback from sounddevice thread.

        Called to request audio data for playback.

        Args:
            outdata: Output buffer to fill with audio data
            frames: Number of frames requested
            time: Timing info
            status: Status flags
        """
        if status:
            logger.warning(f"Audio output status: {status}")

        try:
            # Try to get data from buffer
            if self._buffer:
                data = self._buffer.pop(0)
                # Ensure data fits the output buffer
                if len(data) >= frames:
                    outdata[:] = data[:frames].reshape(-1, 1)
                else:
                    outdata[:len(data)] = data.reshape(-1, 1)
                    outdata[len(data):] = 0
            else:
                # Fill with silence if no data available
                outdata[:] = 0
        except Exception as e:
            logger.debug(f"Playback callback error: {e}")
            outdata[:] = 0

    async def start(self):
        """Start audio playback."""
        if self._running:
            return

        self._loop = asyncio.get_event_loop()

        self._stream = sd.OutputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=self.samples_per_frame,
            callback=self._audio_callback
        )
        self._stream.start()
        self._running = True
        logger.info(f"Started audio playback (device={self.device_id}, rate={self.sample_rate})")

    async def feed(self, audio_data: bytes):
        """
        Feed audio data from remote peer for playback.

        Args:
            audio_data: Raw audio bytes to play
        """
        # Convert bytes to numpy array
        data = np.frombuffer(audio_data, dtype=np.int16)

        # Add to buffer (used by callback)
        # Limit buffer size to prevent memory issues
        if len(self._buffer) < 100:
            self._buffer.append(data)

    async def handle_track(self, track):
        """
        Handle incoming audio track from aiortc.

        Continuously receives frames from remote track and feeds
        them to the playback device.

        Args:
            track: Remote audio track from RTCPeerConnection on("track") event
        """
        await self.start()

        try:
            while self._running:
                frame = await track.recv()
                # Extract audio data and feed to playback
                audio_bytes = bytes(frame.planes[0])
                await self.feed(audio_bytes)
        except Exception as e:
            logger.debug(f"Track handling ended: {e}")

    async def stop(self):
        """Stop playback and clean up resources."""
        self._running = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Stopped audio playback")

        # Clear buffers
        self._buffer.clear()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self._loop = None
