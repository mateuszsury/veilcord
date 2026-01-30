---
phase: 05
plan: 03
subsystem: voice
tags: [webrtc, voip, state-machine, signaling]
dependencies:
  requires: ["05-01", "05-02"]
  provides: ["voice-call-service", "call-lifecycle-management"]
  affects: ["05-05", "05-06"]
tech-stack:
  added: []
  patterns: ["state-machine", "callback-based-events", "async-signaling"]
key-files:
  created:
    - src/voice/call_service.py
  modified:
    - src/voice/__init__.py
decisions:
  - key: "separate-pc-for-voice"
    choice: "Separate RTCPeerConnection for voice calls"
    rationale: "Voice calls use different peer connection than data channels to allow media renegotiation"
metrics:
  duration: "3m"
  completed: "2026-01-30"
---

# Phase 5 Plan 03: VoiceCallService Summary

**One-liner:** Voice call lifecycle orchestration with WebRTC peer connections, state machine, and signaling integration.

## What Was Built

### VoiceCallService (src/voice/call_service.py)

Core voice calling engine that manages the complete call lifecycle:

1. **Call State Machine**
   - 7 states: IDLE, RINGING_OUTGOING, RINGING_INCOMING, CONNECTING, ACTIVE, RECONNECTING, ENDED
   - Proper transitions with validation
   - State change callbacks for UI updates

2. **Outgoing Calls**
   - `start_call(contact_id, contact_public_key)` creates WebRTC offer
   - Creates MicrophoneAudioTrack and adds to peer connection
   - Waits for ICE gathering before sending offer
   - Starts 30-second ring timeout

3. **Incoming Calls**
   - `handle_call_offer(event)` stores offer and triggers ringing UI
   - `accept_call()` creates answer with mic track
   - `reject_call()` sends rejection and ends call

4. **Call Management**
   - `end_call(reason)` cleans up resources and notifies remote
   - `set_muted(muted)` mutes mic without stopping track
   - `attempt_reconnect()` handles network changes
   - `get_call_duration()` returns seconds since connection

5. **Signaling Integration**
   - Callback-based: `send_signaling`, `on_state_change`, `on_call_event`
   - Handles: offer, answer, reject, end, mute events
   - Uses CallEvent for serialization

## Key Implementation Details

### Separate Peer Connection Pattern
Voice calls use their own RTCPeerConnection (not the data channel PC) to:
- Allow independent media renegotiation
- Isolate call state from messaging
- Support call-specific ICE handling

### Ring Timeout
- 30-second default timeout for unanswered calls
- Automatically ends with NO_ANSWER reason
- Cancelled when call is answered or rejected

### Reconnection Support
Per research, aiortc doesn't support ICE restart:
- On disconnect, transitions to RECONNECTING state
- Creates entirely new peer connection
- Outgoing caller re-initiates with same call_id

### Thread Safety
- Uses asyncio.Lock for state mutations
- Handles both sync and async signaling callbacks
- Fire-and-forget for mute status updates

## Verification Results

All criteria verified:
1. VoiceCallService manages complete call lifecycle
2. Can start outgoing calls (creates offer with audio track)
3. Can handle incoming calls (receives offer, sends answer)
4. Ring timeout auto-ends unanswered calls after 30 seconds
5. Mute/unmute works without stopping audio track
6. Clean resource cleanup on call end (mic, playback, PC)

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| src/voice/call_service.py | Created | Voice call lifecycle management |
| src/voice/__init__.py | Modified | Export VoiceCallService |

## Commits

| Hash | Message |
|------|---------|
| 04d932b | feat(05-03): add VoiceCallService core |
| e85cc53 | feat(05-03): add disconnected state handling |
| 86b992a | feat(05-03): export VoiceCallService from voice package |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Ready for:
- **05-05:** Call UI (incoming call modal, active call controls)
- **05-06:** Network integration (hook VoiceCallService to NetworkService)

Integration notes:
- NetworkService should set `send_signaling` callback
- NetworkService should call `set_local_public_key()`
- NetworkService should route call signaling events to handler methods
