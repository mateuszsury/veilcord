"""
Audio and video device management for voice/video calls.

Provides enumeration and testing of audio input/output devices
using the sounddevice library, and camera/monitor enumeration
for video calls and screen sharing.
"""

import logging
from typing import Dict, List, Optional

import cv2
import numpy as np
import sounddevice as sd
from mss import mss

logger = logging.getLogger(__name__)


class AudioDeviceManager:
    """
    Manages audio device enumeration and testing.

    Uses sounddevice library which auto-installs PortAudio on Windows.
    """

    @staticmethod
    def get_input_devices() -> List[Dict]:
        """
        Get list of available audio input devices (microphones).

        Returns:
            List of dicts with {id, name, channels} for each input device.
        """
        devices = []
        all_devices = sd.query_devices()

        for idx, dev in enumerate(all_devices):
            if dev['max_input_channels'] > 0:
                devices.append({
                    'id': idx,
                    'name': dev['name'],
                    'channels': dev['max_input_channels']
                })

        return devices

    @staticmethod
    def get_output_devices() -> List[Dict]:
        """
        Get list of available audio output devices (speakers).

        Returns:
            List of dicts with {id, name, channels} for each output device.
        """
        devices = []
        all_devices = sd.query_devices()

        for idx, dev in enumerate(all_devices):
            if dev['max_output_channels'] > 0:
                devices.append({
                    'id': idx,
                    'name': dev['name'],
                    'channels': dev['max_output_channels']
                })

        return devices

    @staticmethod
    def get_default_input() -> int:
        """
        Get the system default input device ID.

        Returns:
            Device ID of the default input device.
        """
        default = sd.query_devices(kind='input')
        # Find the index of this device in the full device list
        all_devices = sd.query_devices()
        for idx, dev in enumerate(all_devices):
            if dev['name'] == default['name'] and dev['max_input_channels'] == default['max_input_channels']:
                return idx
        return 0

    @staticmethod
    def get_default_output() -> int:
        """
        Get the system default output device ID.

        Returns:
            Device ID of the default output device.
        """
        default = sd.query_devices(kind='output')
        # Find the index of this device in the full device list
        all_devices = sd.query_devices()
        for idx, dev in enumerate(all_devices):
            if dev['name'] == default['name'] and dev['max_output_channels'] == default['max_output_channels']:
                return idx
        return 0

    @staticmethod
    def test_device(device_id: int, is_input: bool = True, duration: float = 0.5) -> bool:
        """
        Test if an audio device works by recording or playing briefly.

        Args:
            device_id: The device ID to test.
            is_input: True to test as input (microphone), False for output (speaker).
            duration: Duration in seconds for the test.

        Returns:
            True if device works, False otherwise.
        """
        try:
            sample_rate = 44100
            samples = int(duration * sample_rate)

            if is_input:
                # Test input by recording briefly
                sd.rec(
                    frames=samples,
                    samplerate=sample_rate,
                    channels=1,
                    device=device_id,
                    blocking=True
                )
            else:
                # Test output by playing silence
                silence = np.zeros((samples, 2), dtype=np.float32)
                sd.play(
                    silence,
                    samplerate=sample_rate,
                    device=device_id,
                    blocking=True
                )

            return True
        except Exception:
            return False


# Module-level convenience functions

def get_input_devices() -> List[Dict]:
    """Get list of available audio input devices (microphones)."""
    return AudioDeviceManager.get_input_devices()


def get_output_devices() -> List[Dict]:
    """Get list of available audio output devices (speakers)."""
    return AudioDeviceManager.get_output_devices()


def get_default_input() -> int:
    """Get the system default input device ID."""
    return AudioDeviceManager.get_default_input()


def get_default_output() -> int:
    """Get the system default output device ID."""
    return AudioDeviceManager.get_default_output()


def test_device(device_id: int, is_input: bool = True, duration: float = 0.5) -> bool:
    """Test if an audio device works."""
    return AudioDeviceManager.test_device(device_id, is_input, duration)


# Video device functions

def get_available_cameras() -> List[Dict]:
    """
    Get list of available camera devices.

    Uses cv2-enumerate-cameras for detailed camera information
    including device names (OpenCV alone only provides indices).

    Returns:
        List of dicts with {index, name, backend, path} for each camera.
        Returns empty list if cv2-enumerate-cameras is not available.
    """
    cameras = []

    try:
        from cv2_enumerate_cameras import enumerate_cameras

        for cam in enumerate_cameras():
            cameras.append({
                'index': cam.index,
                'name': cam.name,
                'backend': cam.backend,
                'path': getattr(cam, 'path', '')
            })

        logger.debug(f"Found {len(cameras)} cameras via cv2-enumerate-cameras")

    except ImportError:
        logger.warning("cv2-enumerate-cameras not available, camera enumeration limited")
        # Fallback: probe indices 0-9 with OpenCV
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append({
                    'index': i,
                    'name': f'Camera {i}',
                    'backend': 'opencv',
                    'path': ''
                })
                cap.release()

    except Exception as e:
        logger.error(f"Error enumerating cameras: {e}")

    return cameras


def get_available_monitors() -> List[Dict]:
    """
    Get list of available monitors for screen sharing.

    Uses mss for cross-platform monitor enumeration.

    Returns:
        List of dicts with {index, width, height, left, top} for each monitor.
        Monitor 0 = all screens combined, 1 = primary, 2+ = additional monitors.
    """
    monitors = []

    try:
        sct = mss()
        for idx, mon in enumerate(sct.monitors):
            monitors.append({
                'index': idx,
                'width': mon['width'],
                'height': mon['height'],
                'left': mon['left'],
                'top': mon['top']
            })
        sct.close()

        logger.debug(f"Found {len(monitors)} monitors")

    except Exception as e:
        logger.error(f"Error enumerating monitors: {e}")

    return monitors


def test_camera(camera_index: int, backend: Optional[int] = None) -> bool:
    """
    Test if a camera device works by trying to capture one frame.

    Args:
        camera_index: The camera index to test.
        backend: Optional OpenCV backend (e.g., cv2.CAP_DSHOW for Windows).

    Returns:
        True if camera can capture a frame, False otherwise.
    """
    cap = None
    try:
        if backend is not None:
            cap = cv2.VideoCapture(camera_index, backend)
        else:
            cap = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            return False

        ret, frame = cap.read()
        return ret and frame is not None

    except Exception as e:
        logger.debug(f"Camera test failed for index {camera_index}: {e}")
        return False

    finally:
        if cap is not None:
            cap.release()
