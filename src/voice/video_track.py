"""
Video track implementations for WebRTC video calls and screen sharing.

Provides custom video stream tracks for capturing camera input
and screen content via aiortc's VideoStreamTrack.
"""

import asyncio
import fractions
import logging
from typing import Optional

import cv2
import numpy as np
from aiortc import VideoStreamTrack
from av import VideoFrame
from mss import mss

logger = logging.getLogger(__name__)


class CameraVideoTrack(VideoStreamTrack):
    """
    Custom VideoStreamTrack that captures video from a camera.

    Uses OpenCV for cross-platform camera capture and produces
    properly-timed av.VideoFrame objects for WebRTC transmission.

    Attributes:
        kind: Media track kind, always "video" for video tracks
    """

    kind = "video"

    def __init__(
        self,
        device_id: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30
    ):
        """
        Initialize the camera video track.

        Args:
            device_id: Camera device ID (0 for default camera)
            width: Desired frame width in pixels
            height: Desired frame height in pixels
            fps: Target frames per second
        """
        super().__init__()
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: Optional[cv2.VideoCapture] = None
        self._pts = 0  # Presentation timestamp counter
        self._muted = False
        self._last_frame: Optional[np.ndarray] = None
        self._running = False
        self._frame_duration = fractions.Fraction(1, fps)

        # Open camera on initialization
        self._open_camera()

    def _open_camera(self):
        """Open the camera capture device."""
        try:
            self._cap = cv2.VideoCapture(self.device_id)
            if self._cap.isOpened():
                # Try to set resolution
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._cap.set(cv2.CAP_PROP_FPS, self.fps)

                # Read actual settings
                actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = int(self._cap.get(cv2.CAP_PROP_FPS))

                self._running = True
                logger.info(
                    f"Opened camera {self.device_id}: "
                    f"{actual_width}x{actual_height}@{actual_fps}fps"
                )
            else:
                logger.error(f"Failed to open camera {self.device_id}")
        except Exception as e:
            logger.error(f"Error opening camera {self.device_id}: {e}")

    @property
    def muted(self) -> bool:
        """Check if track is muted (returns black frames)."""
        return self._muted

    @muted.setter
    def muted(self, value: bool):
        """Set mute state."""
        self._muted = value
        logger.debug(f"Camera mute set to: {value}")

    @property
    def last_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recently captured frame.

        Returns:
            RGB numpy array of the last frame, or None if no frame captured yet
        """
        return self._last_frame

    def _create_black_frame(self) -> np.ndarray:
        """Create a black frame for muted state or errors."""
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)

    async def recv(self) -> VideoFrame:
        """
        Get next video frame for WebRTC transmission.

        Called by aiortc to get video data to send to remote peer.

        Returns:
            av.VideoFrame with properly formatted video data
        """
        # Use aiortc timing for proper frame pacing
        pts, time_base = await self.next_timestamp()

        if self._muted or not self._cap or not self._cap.isOpened():
            # Return black frame when muted or camera unavailable
            frame_rgb = self._create_black_frame()
        else:
            try:
                ret, frame_bgr = self._cap.read()
                if ret and frame_bgr is not None:
                    # Convert BGR (OpenCV default) to RGB
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                else:
                    # Capture failed - return black frame
                    logger.warning("Camera capture failed, returning black frame")
                    frame_rgb = self._create_black_frame()
            except Exception as e:
                logger.error(f"Error capturing frame: {e}")
                frame_rgb = self._create_black_frame()

        # Store the frame for API access
        self._last_frame = frame_rgb

        # Create VideoFrame from numpy array
        frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base

        return frame

    async def stop(self):
        """Stop video capture and release camera resources."""
        self._running = False

        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info(f"Released camera {self.device_id}")

        self._pts = 0
        self._last_frame = None


class ScreenShareTrack(VideoStreamTrack):
    """
    Custom VideoStreamTrack that captures screen content.

    Uses mss (Multiple Screen Shot) for cross-platform screen capture
    and produces properly-timed av.VideoFrame objects for WebRTC transmission.

    Attributes:
        kind: Media track kind, always "video" for video tracks
    """

    kind = "video"

    def __init__(self, monitor_index: int = 1, fps: int = 15):
        """
        Initialize the screen share track.

        Args:
            monitor_index: Monitor to capture (0=all screens combined, 1=primary, 2+=additional)
            fps: Target frames per second (15 is typical for screen sharing)
        """
        super().__init__()
        self.monitor_index = monitor_index
        self.fps = fps
        self._sct: Optional[mss] = None
        self._pts = 0
        self._running = False
        self._last_frame: Optional[np.ndarray] = None
        self._frame_duration = fractions.Fraction(1, fps)
        self._monitor: Optional[dict] = None

        # Initialize mss
        self._open_screen()

    def _open_screen(self):
        """Initialize screen capture."""
        try:
            self._sct = mss()
            monitors = self._sct.monitors

            if self.monitor_index < len(monitors):
                self._monitor = monitors[self.monitor_index]
                self._running = True
                logger.info(
                    f"Screen capture initialized: monitor {self.monitor_index} "
                    f"({self._monitor['width']}x{self._monitor['height']})"
                )
            else:
                logger.error(
                    f"Monitor index {self.monitor_index} out of range "
                    f"(available: 0-{len(monitors)-1})"
                )
                # Fall back to primary monitor
                self._monitor = monitors[1] if len(monitors) > 1 else monitors[0]
                self._running = True
        except Exception as e:
            logger.error(f"Error initializing screen capture: {e}")

    @property
    def last_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recently captured frame.

        Returns:
            RGB numpy array of the last frame, or None if no frame captured yet
        """
        return self._last_frame

    def _create_black_frame(self) -> np.ndarray:
        """Create a black frame for errors."""
        width = self._monitor['width'] if self._monitor else 1920
        height = self._monitor['height'] if self._monitor else 1080
        return np.zeros((height, width, 3), dtype=np.uint8)

    async def recv(self) -> VideoFrame:
        """
        Get next screen frame for WebRTC transmission.

        Called by aiortc to get video data to send to remote peer.

        Returns:
            av.VideoFrame with properly formatted screen capture
        """
        # Use aiortc timing for proper frame pacing
        pts, time_base = await self.next_timestamp()

        if not self._sct or not self._monitor:
            frame_rgb = self._create_black_frame()
        else:
            try:
                # Grab screenshot
                screenshot = self._sct.grab(self._monitor)

                # Convert to numpy array (BGRA format)
                img_bgra = np.array(screenshot)

                # Convert BGRA to RGB (drop alpha, swap B and R)
                img_rgb = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2RGB)

                frame_rgb = img_rgb
            except Exception as e:
                logger.error(f"Error capturing screen: {e}")
                frame_rgb = self._create_black_frame()

        # Store the frame for API access
        self._last_frame = frame_rgb

        # Create VideoFrame from numpy array
        frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base

        return frame

    async def stop(self):
        """Stop screen capture and release resources."""
        self._running = False

        if self._sct is not None:
            self._sct.close()
            self._sct = None
            logger.info("Closed screen capture")

        self._pts = 0
        self._last_frame = None
        self._monitor = None
