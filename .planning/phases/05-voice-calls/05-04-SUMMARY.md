---
phase: 05-voice-calls
plan: 04
subsystem: voice
tags: [opus, pyogg, voice-messages, audio-recording, audio-playback]

dependency-graph:
  requires: [05-01]
  provides: [voice-message-recording, voice-message-playback, opus-encoding]
  affects: [05-05, 05-06]

tech-stack:
  added: [PyOgg]
  patterns: [streaming-opus-encoding, ctypes-to-numpy-conversion]

key-files:
  created:
    - src/voice/voice_message.py
  modified:
    - requirements.txt
    - src/storage/paths.py
    - src/voice/__init__.py

decisions:
  - id: pyogg-libopusenc
    choice: "Use PyOgg libopusenc for direct Ogg file writing"
    reason: "PyOgg API differs from plan - uses low-level libopusenc bindings, not high-level OpusBufferedEncoder"
  - id: ctypes-array-conversion
    choice: "Use np.ctypeslib.as_array() for ctypes to numpy conversion"
    reason: "OpusFile.buffer returns LP_c_short (ctypes pointer), not buffer protocol object"

metrics:
  duration: 8m
  completed: 2026-01-30
---

# Phase 5 Plan 04: Voice Message Recording Summary

**One-liner:** Voice message recording and playback using PyOgg libopusenc for streaming Opus encoding to .ogg files.

## What Was Built

### VoiceMessageRecorder
- Captures audio from microphone using sounddevice InputStream
- Streams audio directly to disk via libopusenc (no memory bloat)
- Enforces 5-minute maximum duration (300 seconds)
- Supports configurable input device
- Returns VoiceMessageMetadata with duration and file path

### VoiceMessagePlayer
- Loads and decodes Opus-encoded .ogg files
- Plays back through sounddevice OutputStream
- Supports pause/resume/seek operations
- Reports playback position and duration
- Fires callbacks on playback complete

### Infrastructure
- Added `get_voice_messages_dir()` to paths.py for voice message storage
- Files stored in `%APPDATA%/DiscordOpus/voice_messages/`
- Added PyOgg>=0.6.14 to requirements.txt

## Technical Implementation

### Recording Flow
1. Create libopusenc encoder targeting output file
2. Start sounddevice InputStream with 20ms frames
3. Audio callback encodes and writes directly to Ogg file
4. On stop, drain encoder and close file

### Playback Flow
1. Load file with PyOgg OpusFile
2. Convert ctypes pointer to numpy array via `np.ctypeslib.as_array()`
3. Normalize int16 to float32 [-1.0, 1.0]
4. Stream through sounddevice OutputStream callback

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 0af80f1 | chore | Add PyOgg dependency, get_voice_messages_dir() |
| 3a9ae17 | feat | VoiceMessageRecorder and VoiceMessagePlayer |

## Deviations from Plan

### API Adaptation

**Issue:** PyOgg 0.6.14 does not have `OpusBufferedEncoder` or `OggOpusWriter` classes mentioned in the plan.

**Resolution:** Used low-level libopusenc bindings instead:
- `ope_encoder_create_file()` - creates encoder writing directly to file
- `ope_encoder_write_float()` - encodes and writes audio frames
- `ope_encoder_drain()` / `ope_encoder_destroy()` - finalize and cleanup

This achieves the same goal (streaming to disk) with different API.

### ctypes Conversion

**Issue:** `OpusFile.buffer` returns `LP_c_short` (ctypes pointer) which numpy cannot directly convert.

**Resolution:** Used `np.ctypeslib.as_array(opus_file.buffer, shape=(samples,))` to create numpy array view of ctypes buffer.

## Verification Results

- [x] Import VoiceMessageRecorder and VoiceMessagePlayer - OK
- [x] Recording for 2 seconds produces valid .ogg file (16KB) - OK
- [x] VoiceMessagePlayer loads and reports duration - OK
- [x] 5-minute maximum duration is enforced (MAX_DURATION=300) - OK
- [x] Files saved to voice messages directory - OK

## Next Phase Readiness

**Ready for:**
- 05-05: Voice call manager can use recorder for voice message feature
- 05-06: UI can integrate recording/playback controls

**Dependencies satisfied:**
- PyOgg installed and working
- Recording produces valid Opus/Ogg files
- Playback decodes and plays correctly
