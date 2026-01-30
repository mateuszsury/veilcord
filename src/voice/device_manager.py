"""
Audio device management for voice calls.

Provides enumeration and testing of audio input/output devices
using the sounddevice library.
"""

from typing import Dict, List, Optional
import sounddevice as sd
import numpy as np


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
