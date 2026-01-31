---
phase: 06
plan: 02
status: complete
subsystem: voice
tags: [video, webrtc, renegotiation, call-service]
dependency_graph:
  requires: ["06-01"]
  provides: ["video-call-service"]
  affects: ["06-03", "06-04", "06-05"]
tech_stack:
  added: []
  patterns: ["video track management", "SDP renegotiation", "remote video handler"]
key_files:
  created: []
  modified:
    - src/voice/models.py
    - src/voice/call_service.py
decisions:
  - key: "RemoteVideoHandler as separate class"
    choice: "Dedicated class for remote video frame handling"
    reason: "Clean separation from VoiceCallService, reusable pattern"
  - key: "BGR output for video frames"
    choice: "Convert to BGR for get_local/remote_video_frame methods"
    reason: "OpenCV uses BGR, ready for JPEG encoding without additional conversion"
  - key: "Renegotiation via new offer"
    choice: "Create new SDP offer for video enable/disable"
    reason: "aiortc doesn't support removeTrack, renegotiation via new offer works"
metrics:
  duration: 5m
  completed: 2026-01-31
---

# Phase 6 Plan 2: Video Track Management Summary

**One-liner:** VoiceCallService extended with enable_video/disable_video methods for camera and screen sharing with SDP renegotiation support.

## What Was Built

### 1. Video State in VoiceCall Model (Task 1)

Extended the VoiceCall dataclass with video state tracking:

```python
# New fields in VoiceCall
video_enabled: bool = False  # Local video is on/off
video_source: Optional[str] = None  # "camera" or "screen"
remote_video: bool = False  # Remote party has video
camera_device_id: Optional[int] = None  # Selected camera index
```

Extended CallEvent with video renegotiation support:

```python
# New fields in CallEvent
video_enabled: Optional[bool] = None
video_source: Optional[str] = None

# New class method
@classmethod
def create_video_renegotiate(cls, call_id, from_key, to_key, sdp, video_enabled, video_source):
    """Create a video renegotiation event for SDP updates."""
```

### 2. Video Track Management in VoiceCallService (Task 2)

Added RemoteVideoHandler class for incoming video:

```python
class RemoteVideoHandler:
    """Handles incoming video track and stores frames."""
    async def handle_track(self, track): ...
    async def stop(self): ...
    @property
    def last_frame(self) -> Optional[np.ndarray]: ...
```

Extended VoiceCallService with video methods:

| Method | Purpose |
|--------|---------|
| `enable_video(source)` | Start camera or screen share video |
| `disable_video()` | Stop local video track |
| `set_camera_device(id)` | Set camera device for video |
| `set_screen_monitor(index)` | Set monitor for screen sharing |
| `get_local_video_frame()` | Get last captured local frame |
| `get_remote_video_frame()` | Get last received remote frame |
| `handle_video_renegotiate(event)` | Handle remote video SDP update |

Added callback for remote video state:

```python
self.on_remote_video: Optional[Callable[[bool, Any], None]] = None
```

## Task Completion

| Task | Name | Commit | Files Modified |
|------|------|--------|----------------|
| 1 | Add video state to VoiceCall model | 1ca2b09 | src/voice/models.py |
| 2 | Add video track management to VoiceCallService | 5f5e5be | src/voice/call_service.py |

## Technical Details

### Video Enable Flow

1. Check call is ACTIVE or CONNECTING state
2. If switching sources, disable current video first
3. Create CameraVideoTrack or ScreenShareTrack
4. Add track to RTCPeerConnection via `addTrack()`
5. Create new SDP offer via `createOffer()`
6. Wait for ICE gathering to complete
7. Send `call_video_renegotiate` event via signaling
8. Update VoiceCall state (video_enabled, video_source)

### Remote Video Handling

The on_track handler in _create_peer_connection now handles video:

```python
elif track.kind == "video":
    self._remote_video_handler = RemoteVideoHandler()
    asyncio.create_task(self._remote_video_handler.handle_track(track))
    self._current_call.remote_video = True
    if self.on_remote_video:
        self.on_remote_video(True, track)
```

### Cleanup Enhancement

The _cleanup method now handles video resources:

```python
if self._video_track:
    await self._video_track.stop()
    self._video_track = None

if self._remote_video_handler:
    await self._remote_video_handler.stop()
    self._remote_video_handler = None
```

## Deviations from Plan

None - plan executed exactly as written.

## Integration Points

- **From 06-01:** Uses CameraVideoTrack and ScreenShareTrack classes
- **To 06-03:** API layer will call enable_video/disable_video
- **To 06-04:** Frontend will use get_local/remote_video_frame for display
- **To 06-05:** UI components will trigger video enable/disable

## Next Phase Readiness

**Ready for:** 06-03 (Video API Layer)

**Blockers:** None

**Prerequisites met:**
- VoiceCall tracks video state
- CallEvent supports video renegotiation
- VoiceCallService can enable/disable video
- Frame access methods available for API
