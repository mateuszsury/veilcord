"""
Hardware capability detection for adaptive processing.

Detects CUDA, OpenCL, and CPU capabilities to enable optimal quality selection
for audio/video effects processing.
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

DeviceType = Literal["cuda", "opencl", "cpu"]


class HardwareDetector:
    """
    Singleton hardware capability detector.

    Detects available GPU acceleration (CUDA, OpenCL) and falls back to CPU
    when no GPU is available. Results are cached on first access.

    Pattern:
        Lazy initialization - torch is not loaded until first device check.
        This avoids slow imports on application startup.

    Usage:
        detector = HardwareDetector()
        if detector.has_cuda:
            # Use DeepFilterNet3 on CUDA
        elif detector.has_opencl:
            # Use DeepFilterNet3 on OpenCL
        else:
            # Fall back to RNNoise on CPU
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Ensure singleton pattern - only one detector instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize hardware detection (cached on first access)."""
        if not self._initialized:
            self._detect_hardware()
            HardwareDetector._initialized = True

    def _detect_hardware(self) -> None:
        """
        Detect available hardware capabilities.

        Detection order:
        1. Try CUDA via torch.cuda.is_available()
        2. Try OpenCL via cv2.ocl.haveOpenCL()
        3. Fall back to CPU
        """
        self._has_cuda = False
        self._has_opencl = False

        # Try CUDA detection
        try:
            import torch
            if torch.cuda.is_available():
                self._has_cuda = True
                logger.info("CUDA GPU detected: %s", torch.cuda.get_device_name(0))
            else:
                logger.info("torch available but no CUDA GPU detected")
        except ImportError:
            logger.info("torch not installed - CUDA unavailable")
        except Exception as e:
            logger.warning("CUDA detection failed: %s", e)

        # Try OpenCL detection (only if CUDA not available)
        if not self._has_cuda:
            try:
                import cv2
                if cv2.ocl.haveOpenCL():
                    self._has_opencl = True
                    logger.info("OpenCL detected via OpenCV")
                else:
                    logger.info("OpenCV available but OpenCL not detected")
            except ImportError:
                logger.info("OpenCV not installed - OpenCL check skipped")
            except Exception as e:
                logger.warning("OpenCL detection failed: %s", e)

        # Log final device selection
        if self._has_cuda:
            logger.info("Hardware detection complete: CUDA selected")
        elif self._has_opencl:
            logger.info("Hardware detection complete: OpenCL selected")
        else:
            logger.info("Hardware detection complete: CPU-only mode")

    @property
    def has_cuda(self) -> bool:
        """True if CUDA GPU is available."""
        return self._has_cuda

    @property
    def has_opencl(self) -> bool:
        """True if OpenCL is available (and CUDA is not)."""
        return self._has_opencl

    @property
    def device(self) -> DeviceType:
        """
        Current device type for processing.

        Returns:
            "cuda" if CUDA available
            "opencl" if OpenCL available (and CUDA not available)
            "cpu" otherwise
        """
        if self._has_cuda:
            return "cuda"
        elif self._has_opencl:
            return "opencl"
        else:
            return "cpu"
