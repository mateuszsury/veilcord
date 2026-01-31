---
phase: 07-group-features
plan: 05
subsystem: group-calls
tags: [webrtc, mesh-topology, voice, aiortc, peer-connection]
depends_on:
  requires:
    - 07-01  # Group storage schema
    - 05-02  # Audio tracks (MicrophoneAudioTrack)
  provides:
    - GroupCallMesh for mesh voice calls
    - Bandwidth estimation with participant limits
    - Polite/impolite peer pattern for signaling
  affects:
    - 07-06  # Group UI (will use GroupCallMesh)
    - 07-07  # Group API (will expose call methods)
tech-stack:
  added: []
  patterns:
    - WebRTC mesh topology
    - Polite/impolite peer pattern
    - Async state machine
key-files:
  created:
    - src/groups/call_mesh.py
  modified:
    - src/groups/__init__.py
decisions:
  - "Mesh topology: Each participant maintains N-1 peer connections"
  - "Polite/impolite pattern: Higher public key initiates connection"
  - "Soft limit: 4 participants (warning above)"
  - "Hard limit: 8 participants (refuse above)"
  - "Audio bitrate: 50 kbps per stream"
  - "ICE gathering timeout: 30 seconds"
  - "Shared MicrophoneAudioTrack across all peer connections"
metrics:
  duration: 4m 9s
  completed: 2026-01-31
---

# Phase 07 Plan 05: WebRTC Mesh Topology Summary

**One-liner:** GroupCallMesh managing N-1 WebRTC peer connections per participant with polite/impolite signaling pattern for group voice calls.

## What Was Built

### GroupCallMesh Class (547 lines)
Full-mesh WebRTC topology manager for group voice calls:

- **Peer Connection Management:** Creates and maintains RTCPeerConnection for each peer
- **Polite/Impolite Pattern:** Connection initiation based on public key ordering
- **Bandwidth Estimation:** Static method calculating upload/download requirements
- **State Machine:** IDLE -> JOINING -> ACTIVE -> LEAVING -> ENDED
- **Signaling Handlers:** offer, answer, participant join/leave
- **Mute Control:** Via MicrophoneAudioTrack integration

### Key Components

```python
class GroupCallState(Enum):
    IDLE = "idle"
    JOINING = "joining"
    ACTIVE = "active"
    LEAVING = "leaving"
    ENDED = "ended"

class GroupCallMesh:
    async def start_call(call_id, participants) -> BandwidthEstimate
    async def join_call(call_id, participants) -> BandwidthEstimate
    async def leave_call() -> None
    async def handle_offer(peer_key, sdp, sdp_type) -> None
    async def handle_answer(peer_key, sdp, sdp_type) -> None

class BandwidthEstimate:
    upload_kbps: int
    download_kbps: int
    total_kbps: int
    participant_count: int
    warning: bool
    message: Optional[str]
```

### Constants
- `SOFT_LIMIT = 4` - Warning above this
- `HARD_LIMIT = 8` - Refuse above this
- `AUDIO_BITRATE_KBPS = 50` - Per stream

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Mesh topology | Best latency/quality for 2-4 participants, no SFU required |
| Public key ordering for polite/impolite | Deterministic, no coordination needed |
| 4 participant soft limit | 300 kbps total bandwidth is reasonable |
| 8 participant hard limit | 700 kbps total, mesh becomes impractical above |
| Shared MicrophoneAudioTrack | Single audio capture, multiple connections |
| 30s ICE timeout | Consistent with 1:1 call service |

## Bandwidth Calculations

| Participants | Upload | Download | Total | Warning |
|--------------|--------|----------|-------|---------|
| 2 | 50 kbps | 50 kbps | 100 kbps | No |
| 3 | 100 kbps | 100 kbps | 200 kbps | No |
| 4 | 150 kbps | 150 kbps | 300 kbps | No |
| 5 | 200 kbps | 200 kbps | 400 kbps | Yes |
| 8 | 350 kbps | 350 kbps | 700 kbps | Yes |

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Commit | Description |
|--------|-------------|
| 4123707 | feat(07-05): implement GroupCallMesh for WebRTC mesh topology |
| db2fd12 | feat(07-05): export GroupCallMesh from groups module |

## Files Changed

| File | Change |
|------|--------|
| src/groups/call_mesh.py | Created (547 lines) |
| src/groups/__init__.py | Added call mesh exports |

## Testing Notes

Structure and bandwidth estimation verified via unit tests. Full WebRTC testing requires:
- Audio devices
- Network connectivity
- Multiple peer instances

## Next Phase Readiness

### Ready for 07-06 (Group UI)
- GroupCallMesh provides call state and participant tracking
- BandwidthEstimate can drive UI warnings
- Callbacks enable reactive UI updates

### Ready for 07-07 (Group API)
- All methods are async and return appropriate types
- State machine is well-defined
- Cleanup handles all resources

## Success Criteria Met

- [x] GroupCallMesh manages N-1 peer connections
- [x] Bandwidth estimation with participant warnings
- [x] Polite/impolite peer pattern for connection negotiation
- [x] Call state machine (IDLE, JOINING, ACTIVE, LEAVING, ENDED)
- [x] Signaling message handlers (offer, answer, join, leave)
- [x] Mute/unmute control
- [x] Resource cleanup on call end
