"""
Effects tracks package for real-time audio/video effect processing.

Provides MediaStreamTrack wrappers that apply effects during WebRTC calls.
"""

from .audio_effects_track import AudioEffectsTrack
from .video_effects_track import VideoEffectsTrack, VideoEffectsPipeline

__all__ = [
    "AudioEffectsTrack",
    "VideoEffectsTrack",
    "VideoEffectsPipeline",
]
