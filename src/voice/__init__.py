"""
Voice and video calling package.

Provides audio/video device management, voice call data models,
and video tracks for the DiscordOpus P2P communication system.
"""

from .device_manager import (
    AudioDeviceManager,
    get_input_devices,
    get_output_devices,
    get_default_input,
    get_default_output,
    test_device,
    # Video device functions
    get_available_cameras,
    get_available_monitors,
    test_camera
)

from .models import (
    CallState,
    CallEndReason,
    VoiceCall,
    VoiceMessageMetadata,
    CallEvent
)

from .audio_track import (
    MicrophoneAudioTrack,
    AudioPlaybackTrack
)

from .video_track import (
    CameraVideoTrack,
    ScreenShareTrack
)

from .voice_message import (
    VoiceMessageRecorder,
    VoiceMessagePlayer
)

from .call_service import VoiceCallService

__all__ = [
    # Device management - audio
    'AudioDeviceManager',
    'get_input_devices',
    'get_output_devices',
    'get_default_input',
    'get_default_output',
    'test_device',
    # Device management - video
    'get_available_cameras',
    'get_available_monitors',
    'test_camera',
    # Models
    'CallState',
    'CallEndReason',
    'VoiceCall',
    'VoiceMessageMetadata',
    'CallEvent',
    # Audio tracks
    'MicrophoneAudioTrack',
    'AudioPlaybackTrack',
    # Video tracks
    'CameraVideoTrack',
    'ScreenShareTrack',
    # Voice messages
    'VoiceMessageRecorder',
    'VoiceMessagePlayer',
    # Call service
    'VoiceCallService',
]
