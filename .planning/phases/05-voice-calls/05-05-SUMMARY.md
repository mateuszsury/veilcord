---
phase: 05-voice-calls
plan: 05
subsystem: network-integration
tags: [voice, webrtc, api, network, signaling]
depends_on:
  requires: [05-01, 05-02, 05-03, 05-04]
  provides: [voice-integration, call-api, voice-message-api]
  affects: [05-06, 05-07, 05-08]
tech-stack:
  added: []
  patterns: [event-driven-signaling, callback-based-notifications]
key-files:
  created: []
  modified:
    - src/network/service.py
    - src/api/bridge.py
    - frontend/src/lib/pywebview.ts
decisions:
  - id: D05-05-01
    title: "VoiceCallService integration pattern"
    choice: "Callback-based notifications to frontend"
    rationale: "Consistent with existing messaging and file transfer patterns"
metrics:
  duration: "8m"
  completed: "2026-01-30"
---

# Phase 5 Plan 5: Voice Integration Summary

**Voice call and voice message integration into NetworkService and API bridge with TypeScript types for frontend**

## What Was Built

### 1. NetworkService Voice Integration

VoiceCallService is now fully integrated into NetworkService:

- Created in `_async_start` with callbacks for state changes and signaling
- Local public key set from identity for signaling
- Cleanup in `_async_stop` to end any active calls

### 2. Call Signaling Message Handlers

Complete handlers for all voice call signaling messages:

| Message Type | Handler | Frontend Event |
|--------------|---------|----------------|
| `call_offer` | Creates CallEvent, calls `handle_call_offer` | `discordopus:incoming_call` |
| `call_answer` | Creates CallEvent, calls `handle_call_answer` | `discordopus:call_answered` |
| `call_reject` | Creates CallEvent, calls `handle_call_reject` | `discordopus:call_rejected` |
| `call_end` | Maps reason to CallEndReason, ends call | `discordopus:call_ended` |
| `call_mute` | Creates CallEvent, handles mute status | `discordopus:remote_mute` |
| `call_ice_candidate` | Logs for future trickle ICE support | - |

### 3. NetworkService Public Methods

Voice call control methods:

```python
start_voice_call(contact_id) -> Optional[str]  # Returns call ID
accept_voice_call() -> bool
reject_voice_call() -> bool
end_voice_call() -> bool
set_call_muted(muted: bool) -> None
is_call_muted() -> bool
get_call_state() -> Optional[Dict]
```

### 4. API Bridge Methods

Voice call API (for frontend):

- `start_call(contact_id)` - Start call, returns `{callId}` or `{error}`
- `accept_call()` - Accept incoming call
- `reject_call()` - Reject incoming call
- `end_call()` - End current call
- `set_muted(muted)` - Mute/unmute microphone
- `is_muted()` - Check mute status
- `get_call_state()` - Get current call state

Voice message API:

- `start_voice_recording()` - Start recording, returns path
- `stop_voice_recording()` - Stop and get metadata
- `cancel_voice_recording()` - Cancel recording
- `get_recording_duration()` - Get current duration

Audio device API:

- `get_audio_devices()` - List input/output devices
- `set_audio_devices(input_id, output_id)` - Set devices for calls

### 5. TypeScript Type Definitions

New types in `pywebview.ts`:

```typescript
type VoiceCallState = 'idle' | 'ringing_outgoing' | 'ringing_incoming' |
                      'connecting' | 'active' | 'reconnecting' | 'ended';

interface CallState {
  callId: string;
  contactId: number;
  state: VoiceCallState;
  direction: 'outgoing' | 'incoming';
  muted: boolean;
  duration: number | null;
}

interface AudioDevice {
  id: number;
  name: string;
  channels: number;
}
```

Event payloads for frontend event listeners.

## Task Completion

| Task | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | Voice messages directory path | Skipped | Already exists from 05-04 |
| 2 | NetworkService integration | Complete | VoiceCallService, signaling, state |
| 3 | API bridge methods | Complete | Call + voice message + device APIs |

## Key Implementation Details

### Signaling Flow

```
Frontend                NetworkService              VoiceCallService
   |                         |                            |
   |-- start_call(id) ------>|                            |
   |                         |-- start_call() ----------->|
   |                         |                            |-- create offer
   |                         |                            |-- gather ICE
   |                         |<-- send_signaling(offer) --|
   |                         |-- signaling server ------->|
   |                         |                            |
   |                         |<-- call_answer ------------|
   |                         |-- handle_call_answer() --->|
   |<-- call_answered -------|                            |
   |                         |                            |
   |<-- call_state(active) --|<-- on_state_change --------|
```

### Event Notifications

All call events dispatch to frontend via `_notify_frontend()`:

- `discordopus:call_state` - State machine transitions
- `discordopus:incoming_call` - Incoming call notification
- `discordopus:call_answered` - Call connected
- `discordopus:call_rejected` - Call was rejected
- `discordopus:call_ended` - Call terminated
- `discordopus:remote_mute` - Remote mute status

### Voice Recorder Instance

Voice message recorder is stored on NetworkService as `_voice_recorder`:

- Created lazily on first `start_voice_recording()`
- Cleared after `stop_voice_recording()` or `cancel_voice_recording()`
- Uses asyncio thread-safe execution via `run_coroutine_threadsafe`

## Verification

All verifications passed:

1. NetworkService imports without errors
2. API bridge methods present and callable
3. Audio device enumeration works
4. TypeScript types compile

## Deviations from Plan

### Auto-fixed Issues

**None** - plan executed exactly as written.

### Note on Task 1

Task 1 (voice messages directory path) was skipped because the function `get_voice_messages_dir()` already existed in `src/storage/paths.py` from plan 05-04. Verified it works correctly.

## Files Changed

| File | Change |
|------|--------|
| `src/network/service.py` | +230 lines: imports, VoiceCallService integration, signaling handlers, public methods |
| `src/api/bridge.py` | +180 lines: voice call, voice message, and audio device API methods |
| `frontend/src/lib/pywebview.ts` | +60 lines: TypeScript types for calls, events, audio devices |

## Commits

- `1f179ae`: feat(05-05): integrate voice calls into NetworkService and API bridge

## Next Steps

Ready for Phase 5 Plan 6: Voice call UI components (call button, incoming call dialog, active call overlay).
