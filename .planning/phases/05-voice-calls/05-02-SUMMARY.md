---
phase: 05-voice-calls
plan: 02
subsystem: voice
tags: [aiortc, sounddevice, webrtc, audio, av, numpy]

# Dependency graph
requires:
  - phase: 05-01
    provides: AudioDeviceManager, CallState models, sounddevice dependency
provides:
  - MicrophoneAudioTrack for capturing audio from microphone
  - AudioPlaybackTrack for playing received audio
  - WebRTC-compatible AudioFrame production at 48kHz/20ms
affects: [05-03, 05-04, 05-05, 05-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Queue-based audio buffering between callback thread and asyncio
    - Minimal callback implementation (just copy to queue)

key-files:
  created:
    - src/voice/audio_track.py
  modified:
    - src/voice/__init__.py

key-decisions:
  - "Thread-safe async queue bridging sounddevice callback and asyncio"
  - "Silence on mute (zeros) instead of stopping capture"
  - "Drop frames when queue full to prevent memory bloat"
  - "List-based buffer for playback callback simplicity"

patterns-established:
  - "Callback thread to asyncio: loop.call_soon_threadsafe() with put_nowait"
  - "Audio frame format: s16, mono, 48kHz, 960 samples (20ms)"
  - "Mute by returning zeros instead of stopping stream"

# Metrics
duration: 4min
completed: 2026-01-30
---

# Phase 5 Plan 2: Audio Tracks Summary

**Custom AudioStreamTrack classes using sounddevice for cross-platform WebRTC audio capture and playback**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-30
- **Completed:** 2026-01-30
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- MicrophoneAudioTrack captures audio via sounddevice and produces av.AudioFrame for WebRTC
- AudioPlaybackTrack receives frames from remote peer and plays through speakers
- Proper 20ms frame timing at 48kHz (960 samples) for Opus codec compatibility
- Thread-safe buffer bridging sounddevice callback to asyncio event loop
- Mute support that returns silence without stopping capture

## Task Commits

Each task was committed atomically:

1. **Task 1 & 2: MicrophoneAudioTrack and AudioPlaybackTrack** - `0074a19` (feat)
2. **Task 3: Update voice package exports** - `70f9869` (chore)

## Files Created/Modified
- `src/voice/audio_track.py` - MicrophoneAudioTrack and AudioPlaybackTrack classes
- `src/voice/__init__.py` - Added audio track exports to __all__

## Decisions Made
- **Thread-safe queue bridging**: Used `loop.call_soon_threadsafe()` to safely pass audio data from sounddevice callback thread to asyncio queue
- **Mute returns silence**: When muted, track still captures but returns zero-filled frames - allows unmute without restart
- **Drop on queue full**: Prevents memory bloat by dropping oldest frames when buffer exceeds 100 frames
- **Simple list buffer for playback**: Used list with pop(0) for playback callback - sufficient for audio timing requirements

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - aiortc and av dependencies already installed from Phase 3 WebRTC work.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Audio tracks ready for RTCPeerConnection integration
- Plan 05-03 can add tracks to peer connection for voice calls
- Device selection flows through device_id parameter (from 05-01)

---
*Phase: 05-voice-calls*
*Completed: 2026-01-30*
