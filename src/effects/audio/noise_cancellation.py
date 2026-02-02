"""
Noise cancellation for audio processing.

Provides AI-based noise reduction using DeepFilterNet3 (GPU) with RNNoise fallback (CPU).
Automatically selects the best available method based on hardware capabilities.
"""

import logging
import time
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class NoiseCancellationMethod(Enum):
    """Available noise cancellation methods."""
    NONE = "none"
    RNNOISE = "rnnoise"
    DEEPFILTER = "deepfilter"


class NoiseReducer:
    """
    Adaptive noise reduction using DeepFilterNet3 or RNNoise.

    Automatically selects the best available method based on hardware:
    - GPU available: DeepFilterNet3 (superior quality, 50-100ms latency)
    - CPU only: RNNoise (ultra-low latency, 10-20ms)
    - Neither available: Pass-through (no processing)

    Examples:
        # Auto-select based on hardware
        reducer = NoiseReducer()

        # Force specific method
        reducer = NoiseReducer(method=NoiseCancellationMethod.RNNOISE)

        # Process audio
        clean_audio = reducer.process(noisy_audio, sample_rate=48000)

        # Toggle on/off during call
        reducer.enabled = False

        # Switch methods dynamically
        reducer.set_method(NoiseCancellationMethod.DEEPFILTER)
    """

    def __init__(self, method: Optional[NoiseCancellationMethod] = None):
        """
        Initialize noise reducer.

        Args:
            method: Noise cancellation method to use, or None for auto-selection
        """
        self._enabled = True
        self._method = None
        self._model = None
        self._df_state = None
        self._rnnoise_denoiser = None
        self._last_latency_ms = 0.0

        # Lazy-load models - don't initialize until first use
        if method is None:
            method = self._auto_select_method()

        self._method = method
        logger.info(f"NoiseReducer initialized with method: {self._method.value}")

    def _auto_select_method(self) -> NoiseCancellationMethod:
        """
        Auto-select noise cancellation method based on hardware.

        Returns:
            Best available method for current hardware
        """
        # Check for GPU availability (CUDA or OpenCL)
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("CUDA GPU detected, selecting DeepFilterNet3")
                return NoiseCancellationMethod.DEEPFILTER
        except ImportError:
            pass

        # Check for OpenCL (AMD/Intel GPUs)
        try:
            import cv2
            if cv2.ocl.haveOpenCL():
                logger.info("OpenCL GPU detected, selecting DeepFilterNet3")
                return NoiseCancellationMethod.DEEPFILTER
        except:
            pass

        # Default to RNNoise for CPU-only systems
        logger.info("No GPU detected, selecting RNNoise for CPU")
        return NoiseCancellationMethod.RNNOISE

    def _init_deepfilter(self):
        """Initialize DeepFilterNet3 model."""
        try:
            from df import enhance, init_df
            import torch

            # Limit VRAM usage to prevent OOM on lower-end GPUs
            if torch.cuda.is_available():
                torch.cuda.set_per_process_memory_fraction(0.5)

            self._model, self._df_state, _ = init_df()
            logger.info("DeepFilterNet3 model loaded successfully")

        except ImportError as e:
            logger.error(f"Failed to import DeepFilterNet: {e}")
            logger.warning("DeepFilterNet not available, falling back to RNNoise")
            self._method = NoiseCancellationMethod.RNNOISE
            self._init_rnnoise()
        except Exception as e:
            logger.error(f"Failed to initialize DeepFilterNet: {e}")
            logger.warning("Falling back to RNNoise")
            self._method = NoiseCancellationMethod.RNNOISE
            self._init_rnnoise()

    def _init_rnnoise(self):
        """Initialize RNNoise denoiser."""
        try:
            import rnnoise
            self._rnnoise_denoiser = rnnoise.RNNoise()
            logger.info("RNNoise denoiser loaded successfully")

        except ImportError as e:
            logger.error(f"Failed to import RNNoise: {e}")
            logger.warning("RNNoise not available, noise cancellation disabled")
            self._method = NoiseCancellationMethod.NONE
        except Exception as e:
            logger.error(f"Failed to initialize RNNoise: {e}")
            self._method = NoiseCancellationMethod.NONE

    def _ensure_initialized(self):
        """Ensure the selected method is initialized (lazy loading)."""
        if self._method == NoiseCancellationMethod.DEEPFILTER and self._model is None:
            self._init_deepfilter()
        elif self._method == NoiseCancellationMethod.RNNOISE and self._rnnoise_denoiser is None:
            self._init_rnnoise()

    def process(self, audio_chunk: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply noise cancellation to audio chunk.

        Args:
            audio_chunk: Audio data as numpy array (mono or stereo)
            sample_rate: Sample rate in Hz

        Returns:
            Processed audio with reduced noise
        """
        if not self._enabled or self._method == NoiseCancellationMethod.NONE:
            return audio_chunk

        # Ensure model is loaded
        self._ensure_initialized()

        # Track processing latency
        start_time = time.perf_counter()

        try:
            if self._method == NoiseCancellationMethod.DEEPFILTER:
                processed = self._process_deepfilter(audio_chunk, sample_rate)
            elif self._method == NoiseCancellationMethod.RNNOISE:
                processed = self._process_rnnoise(audio_chunk, sample_rate)
            else:
                processed = audio_chunk

            # Calculate latency
            self._last_latency_ms = (time.perf_counter() - start_time) * 1000

            # Warn if latency exceeds threshold (per research pitfall #1)
            if self._last_latency_ms > 150:
                logger.warning(
                    f"Noise cancellation latency ({self._last_latency_ms:.1f}ms) "
                    "exceeds 150ms threshold - consider switching to RNNoise"
                )

            return processed

        except Exception as e:
            logger.error(f"Error processing audio with {self._method.value}: {e}")
            return audio_chunk

    def _process_deepfilter(self, audio_chunk: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Process audio with DeepFilterNet3.

        Args:
            audio_chunk: Audio data
            sample_rate: Sample rate in Hz

        Returns:
            Enhanced audio
        """
        from df import enhance
        import torch

        # DeepFilterNet expects float32 audio in [-1, 1] range
        # Convert from int16 if needed
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk.astype(np.float32)

        # Ensure correct shape (1D for mono)
        if audio_float.ndim > 1:
            audio_float = audio_float.flatten()

        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_float).unsqueeze(0)

        # Apply enhancement
        enhanced = enhance(self._model, self._df_state, audio_tensor)

        # Convert back to numpy
        enhanced_np = enhanced.squeeze().numpy()

        # Convert back to int16 if input was int16
        if audio_chunk.dtype == np.int16:
            enhanced_np = (enhanced_np * 32768.0).astype(np.int16)

        return enhanced_np

    def _process_rnnoise(self, audio_chunk: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Process audio with RNNoise.

        Args:
            audio_chunk: Audio data
            sample_rate: Sample rate in Hz

        Returns:
            Denoised audio
        """
        # RNNoise expects 48kHz, 16-bit audio
        # Resample if needed
        if sample_rate != 48000:
            audio_chunk = self._resample(audio_chunk, sample_rate, 48000)

        # Convert to int16 if needed
        if audio_chunk.dtype != np.int16:
            audio_chunk = (audio_chunk * 32768.0).astype(np.int16)

        # Ensure correct shape (1D for mono)
        if audio_chunk.ndim > 1:
            audio_chunk = audio_chunk.flatten()

        # Process with RNNoise
        denoised = self._rnnoise_denoiser.process(audio_chunk)

        # Resample back to original rate if needed
        if sample_rate != 48000:
            denoised = self._resample(denoised, 48000, sample_rate)

        return denoised

    def _resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """
        Resample audio to different sample rate.

        Args:
            audio: Audio data
            from_rate: Source sample rate
            to_rate: Target sample rate

        Returns:
            Resampled audio
        """
        try:
            import scipy.signal
            num_samples = int(len(audio) * to_rate / from_rate)
            resampled = scipy.signal.resample(audio, num_samples)
            return resampled.astype(audio.dtype)
        except ImportError:
            logger.warning("scipy not available, cannot resample audio")
            return audio

    @property
    def enabled(self) -> bool:
        """Check if noise cancellation is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable noise cancellation."""
        self._enabled = value
        logger.debug(f"Noise cancellation enabled: {value}")

    @property
    def method(self) -> NoiseCancellationMethod:
        """Get current noise cancellation method."""
        return self._method

    def set_method(self, method: NoiseCancellationMethod):
        """
        Switch to different noise cancellation method.

        This will reinitialize the models. Consider the latency impact
        when switching methods during active calls.

        Args:
            method: New method to use
        """
        if method == self._method:
            return

        logger.info(f"Switching noise cancellation method from {self._method.value} to {method.value}")

        # Clean up old resources
        self._model = None
        self._df_state = None
        self._rnnoise_denoiser = None

        # Set new method
        self._method = method

        # Initialize will happen lazily on next process() call

    @property
    def latency_ms(self) -> float:
        """
        Get approximate latency in milliseconds.

        Returns actual measured latency from last process() call.
        Returns approximate values based on method if not yet measured.
        """
        if self._last_latency_ms > 0:
            return self._last_latency_ms

        # Return approximate latency based on method
        if self._method == NoiseCancellationMethod.DEEPFILTER:
            return 75.0  # Typical: 50-100ms
        elif self._method == NoiseCancellationMethod.RNNOISE:
            return 15.0  # Typical: 10-20ms
        else:
            return 0.0
