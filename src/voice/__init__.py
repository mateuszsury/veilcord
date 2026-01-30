"""
Voice calling package.

Provides audio device management and voice call data models
for the DiscordOpus P2P voice calling system.
"""

from .device_manager import (
    AudioDeviceManager,
    get_input_devices,
    get_output_devices,
    get_default_input,
    get_default_output,
    test_device
)

from .models import (
    CallState,
    CallEndReason,
    VoiceCall,
    VoiceMessageMetadata,
    CallEvent
)

__all__ = [
    # Device management
    'AudioDeviceManager',
    'get_input_devices',
    'get_output_devices',
    'get_default_input',
    'get_default_output',
    'test_device',
    # Models
    'CallState',
    'CallEndReason',
    'VoiceCall',
    'VoiceMessageMetadata',
    'CallEvent',
]
