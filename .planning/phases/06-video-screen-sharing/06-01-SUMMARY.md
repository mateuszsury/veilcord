---
phase: 06-video-screen-sharing
plan: 01
subsystem: video
tags: [webrtc, video, opencv, mss, camera, screen-sharing]

dependency-graph:
  requires:
    - "Phase 5 complete - aiortc and WebRTC infrastructure"
  provides:
    - "CameraVideoTrack for camera capture"
    - "ScreenShareTrack for screen sharing"
    - "Camera and monitor enumeration API"
  affects:
    - "06-02: Video call signaling will use these tracks"
    - "06-03: Video call service will manage track lifecycle"

tech-stack:
  added:
    - "opencv-python>=4.0 - camera capture via cv2.VideoCapture"
    - "mss>=9.0 - cross-platform screen capture"
    - "cv2-enumerate-cameras>=1.3.3 - camera enumeration with names"
  patterns:
    - "VideoStreamTrack subclassing (same pattern as MicrophoneAudioTrack)"
    - "Frame buffer for API access to latest capture"
    - "Black frame fallback for errors/mute state"

key-files:
  created:
    - "src/voice/video_track.py"
  modified:
    - "requirements.txt"
    - "src/voice/device_manager.py"
    - "src/voice/__init__.py"

decisions:
  - id: "mss-package-name"
    choice: "Use 'mss' not 'python-mss'"
    rationale: "PyPI package name is 'mss', not 'python-mss'"
  - id: "15fps-screen-share"
    choice: "15 FPS default for screen sharing"
    rationale: "Screen sharing is less demanding, reduces bandwidth"
  - id: "last-frame-buffer"
    choice: "Store last_frame property for API access"
    rationale: "Enables API layer to retrieve recent frame without blocking WebRTC pipeline"

metrics:
  duration: "5 minutes"
  completed: "2026-01-31"
---

# Phase 6 Plan 1: Video Track Infrastructure Summary

**One-liner:** VideoStreamTrack subclasses for camera (30fps) and screen (15fps) capture with cv2-enumerate-cameras for device discovery.

## What Was Built

### Video Track Classes (src/voice/video_track.py - 293 lines)

**CameraVideoTrack:**
- Subclasses aiortc.VideoStreamTrack
- Captures camera via cv2.VideoCapture at 640x480@30fps (configurable)
- Converts BGR to RGB for VideoFrame.from_ndarray()
- Uses next_timestamp() for proper WebRTC timing
- Muted property returns black frames (instant mute/unmute)
- last_frame property for API access to most recent capture
- Graceful error handling with black frame fallback

**ScreenShareTrack:**
- Subclasses aiortc.VideoStreamTrack
- Captures screen via mss at 15fps (configurable)
- Converts BGRA to RGB for VideoFrame.from_ndarray()
- Monitor selection: 0=all screens, 1=primary, 2+=additional
- Same mute/last_frame/error handling patterns as camera

### Device Enumeration (src/voice/device_manager.py)

**get_available_cameras():**
- Uses cv2-enumerate-cameras for detailed info (name, backend, path)
- Falls back to index probing if library unavailable
- Returns: `[{index, name, backend, path}, ...]`

**get_available_monitors():**
- Uses mss.monitors for cross-platform enumeration
- Returns: `[{index, width, height, left, top}, ...]`
- Index 0 = combined virtual monitor, 1+ = physical monitors

**test_camera(camera_index, backend):**
- Opens camera, reads one frame, returns success/failure
- Always releases VideoCapture after test

## Task Completion

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install video dependencies | eae4ea7 | requirements.txt |
| 2 | Implement CameraVideoTrack and ScreenShareTrack | 1b55753 | src/voice/video_track.py |
| 3 | Add camera enumeration to device_manager | bd236d5 | src/voice/device_manager.py, src/voice/__init__.py |

## Decisions Made

1. **Package name correction:** Plan specified `python-mss` but PyPI package is `mss` - corrected in requirements.txt

2. **Frame buffer pattern:** Added `_last_frame` instance variable and `last_frame` property to both tracks for API access without blocking the WebRTC pipeline

3. **Black frame fallback:** When muted or on capture error, return black frames instead of raising exceptions - keeps WebRTC stream alive

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected package name mss**
- **Found during:** Task 1
- **Issue:** Plan specified `python-mss>=9.0` but actual PyPI package is `mss`
- **Fix:** Updated requirements.txt to use `mss>=9.0`
- **Files modified:** requirements.txt
- **Commit:** eae4ea7

## Verification Results

All verification criteria passed:
- pip install -r requirements.txt succeeds
- CameraVideoTrack and ScreenShareTrack instantiate correctly
- Both tracks return VideoFrame with pts/time_base
- get_available_cameras() returns list of camera dicts
- get_available_monitors() returns list of monitor dicts
- All new classes exported from src/voice/__init__.py

## Test Output

```
Screen frame: 1920x1080, pts=0, time_base=1/90000
Camera frame: 640x480 (when camera available)
Found 1 cameras: OBS Virtual Camera
Found 4 monitors: combined + 3 physical
```

## Next Phase Readiness

Ready for 06-02 (Video Call Signaling):
- CameraVideoTrack ready to add to RTCPeerConnection
- ScreenShareTrack ready for screen sharing feature
- Device enumeration enables camera/monitor selection UI
- Pattern matches audio tracks from Phase 5 for consistency
