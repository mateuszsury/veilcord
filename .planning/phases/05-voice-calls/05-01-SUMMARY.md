---
phase: 05-voice-calls
plan: 01
subsystem: voice
tags: [audio, sounddevice, state-machine, models]
requires: []
provides:
  - Audio device enumeration
  - Call state machine
  - Voice call data models
affects:
  - 05-02 (audio tracks)
  - 05-03 (call service)
  - 05-04 (call UI)
tech-stack:
  added: [sounddevice, numpy]
  patterns: [device-manager, state-machine, dataclass-models]
key-files:
  created:
    - src/voice/__init__.py
    - src/voice/device_manager.py
    - src/voice/models.py
  modified:
    - requirements.txt
decisions:
  - sounddevice for audio device access (auto-installs PortAudio on Windows)
  - numpy for audio array processing
  - 7-state CallState enum for call lifecycle
  - Dataclass-based models with factory methods
metrics:
  duration: 4m 27s
  completed: 2026-01-30
---

# Phase 5 Plan 1: Audio Device Foundation Summary

**One-liner:** AudioDeviceManager for input/output enumeration with sounddevice, plus CallState/VoiceCall/CallEvent models for call lifecycle.

## What Was Built

### Audio Device Manager (`src/voice/device_manager.py`)
- `AudioDeviceManager` class with static methods for device operations
- `get_input_devices()` - enumerate microphones with id/name/channels
- `get_output_devices()` - enumerate speakers with id/name/channels
- `get_default_input/output()` - get system default device IDs
- `test_device()` - validate device works with brief record/playback test
- Module-level convenience functions for direct access

### Call State Models (`src/voice/models.py`)
- `CallState` enum: IDLE, RINGING_OUTGOING, RINGING_INCOMING, CONNECTING, ACTIVE, RECONNECTING, ENDED
- `CallEndReason` enum: COMPLETED, REJECTED, NO_ANSWER, FAILED, CANCELLED
- `VoiceCall` dataclass with lifecycle timestamps, state transitions, and duration calculation
- `VoiceMessageMetadata` dataclass for voice message storage
- `CallEvent` dataclass for signaling with factory methods and serialization

### Dependencies Added
- sounddevice>=0.5.0 - audio device enumeration and recording/playback
- numpy>=2.0.0 - required by sounddevice for audio arrays

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| sounddevice over PyAudio | Simpler API, auto-installs PortAudio on Windows, no manual setup |
| Static methods on AudioDeviceManager | No instance state needed, simpler API |
| 7-state CallState | Covers full call lifecycle including reconnection handling |
| Factory methods on models | `VoiceCall.create_outgoing()` clearer than raw constructor |
| CallEvent serialization | `to_dict()`/`from_dict()` for signaling over WebSocket |

## Verification Results

```
Input devices found: 14 (microphones)
Output devices found: 45 (speakers/outputs)
sounddevice version: 0.5.5
All model state transitions work correctly
CallEvent round-trip serialization verified
```

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 17adb80 | feat | create audio device manager |
| 43d5480 | feat | create call state models |
| d51cdef | chore | add sounddevice dependency |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for 05-02 (Audio Track Manager):**
- Device IDs from AudioDeviceManager available for track configuration
- CallState.ACTIVE indicates when audio should flow

**Ready for 05-03 (Call Service):**
- VoiceCall model ready for call lifecycle management
- CallEvent ready for signaling protocol

## Files Created

- `src/voice/__init__.py` - Package exports
- `src/voice/device_manager.py` - Audio device enumeration
- `src/voice/models.py` - Call state machine and data models

## Files Modified

- `requirements.txt` - Added sounddevice and numpy dependencies
