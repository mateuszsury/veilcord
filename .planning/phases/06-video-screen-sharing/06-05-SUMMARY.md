---
phase: 06-video-screen-sharing
plan: 05
subsystem: frontend-video
tags: [video, ui, canvas, polling, react]
dependency_graph:
  requires:
    - 06-02 # Video track management with get_local/remote_video_frame methods
    - 06-03 # Video signaling and API bridge methods
  provides:
    - video-playback-ui # VideoPlayer component for frame rendering
    - local-preview # LocalPreview for camera/screen PiP
    - video-controls # Camera and screen share buttons in call overlay
  affects:
    - 06-06 # Integration testing
tech_stack:
  added: []
  patterns:
    - canvas-frame-polling # 30 FPS polling for video frames
    - base64-jpeg-transmission # Backend sends base64 JPEG frames
    - pip-overlay # Picture-in-picture style local preview
key_files:
  created:
    - frontend/src/components/call/VideoPlayer.tsx
    - frontend/src/components/call/LocalPreview.tsx
  modified:
    - src/api/bridge.py
    - src/network/service.py
    - frontend/src/components/call/ActiveCallOverlay.tsx
decisions:
  - key: frame-polling-rate
    choice: 30 FPS (33ms interval)
    rationale: Standard video rate, balances smoothness with CPU usage
  - key: video-encoding
    choice: JPEG at 70% quality
    rationale: Good compression for real-time transmission, acceptable quality
  - key: overlay-layout
    choice: Expandable overlay
    rationale: Compact for audio-only, expands to 480x380 for video
metrics:
  duration: 3m
  completed: 2026-01-31
---

# Phase 6 Plan 5: Video Display Components Summary

**One-liner:** Canvas-based video playback with 30 FPS frame polling, local preview overlay, and video control buttons in call UI.

## What Was Built

### 1. Video Frame API (Task 1)
Extended NetworkService and API bridge with video frame retrieval methods:
- `get_local_video_frame()` - Returns base64 JPEG of local camera/screen
- `get_remote_video_frame()` - Returns base64 JPEG of remote video
- JPEG encoding at 70% quality for efficient transmission
- BGR to JPEG conversion using OpenCV

### 2. VideoPlayer Component (Task 2)
Created `VideoPlayer.tsx` (88 lines) for rendering video frames:
- Polls backend at 30 FPS (33ms interval)
- Draws frames to HTML5 canvas element
- Auto-resizes canvas to match frame dimensions
- Shows "No video" placeholder when inactive
- Supports both local and remote video types
- Cleanup on unmount prevents memory leaks

### 3. LocalPreview Component (Task 3)
Created `LocalPreview.tsx` (32 lines) for picture-in-picture preview:
- Small overlay (192x144px) positioned bottom-right
- Uses VideoPlayer internally for local video
- Shows label indicating "Camera" or "Screen" source
- Only renders when video is enabled
- Dark border and shadow for visibility

### 4. ActiveCallOverlay Video Integration (Task 4)
Extended `ActiveCallOverlay.tsx` with video features:
- Expandable layout: compact for audio, 480x380px for video
- Remote video display via VideoPlayer when active
- LocalPreview overlay for self-view
- Camera toggle button (indigo highlight when active)
- Screen share button (green highlight when active)
- ScreenPicker dialog integration for monitor selection
- Smooth transition between compact and expanded modes

## Commits

| Hash | Message | Files |
|------|---------|-------|
| 6a5905f | feat(06-05): add video frame API endpoints | bridge.py, service.py |
| 33eed46 | feat(06-05): create VideoPlayer component | VideoPlayer.tsx |
| c0fa8ac | feat(06-05): create LocalPreview component | LocalPreview.tsx |
| d8c79ce | feat(06-05): add video controls and display to ActiveCallOverlay | ActiveCallOverlay.tsx |

## Technical Details

### Frame Polling Architecture
```
Frontend (30 FPS)  →  API Bridge  →  NetworkService  →  VoiceCallService
     ↓                    ↓               ↓                   ↓
 setInterval        get_*_video_frame   JPEG encode      Track.last_frame
     ↓                    ↓               ↓                   ↓
 drawFrame()       base64 response   cv2.imencode     BGR frame buffer
```

### Video Display Flow
1. VideoPlayer polls backend every 33ms
2. Backend gets frame from video track buffer
3. Frame converted to JPEG, base64 encoded
4. Frontend decodes base64, creates Image
5. Image drawn to canvas on load

### Overlay Layout States
- **Audio-only:** 280px min-width, avatar + name + controls
- **Video active:** 480px width, 380px height, video area + controls bar

## Deviations from Plan

None - plan executed exactly as written. Tasks 1-3 were previously committed by another execution session; Task 4 completed in this session.

## Verification Results

- [x] Video frame API returns base64 JPEG frames
- [x] VideoPlayer component draws frames to canvas
- [x] LocalPreview shows small camera preview
- [x] ActiveCallOverlay displays remote video when active
- [x] Camera and screen share buttons work
- [x] ScreenPicker opens when clicking screen share
- [x] Frontend builds without errors

## Next Phase Readiness

**Ready for:** Plan 06-06 (Integration Testing)

**Dependencies satisfied:**
- Video tracks can capture camera/screen (06-01, 06-02)
- Video signaling enables renegotiation (06-03)
- UI components ready for video calls (06-04, 06-05)

**No blockers identified.**
