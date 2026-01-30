# Phase 6: Video & Screen Sharing - Research

**Researched:** 2026-01-31
**Domain:** WebRTC video streaming, screen capture, camera access
**Confidence:** MEDIUM

## Summary

Phase 6 adds video calling and screen sharing capabilities to the existing voice call infrastructure (Phase 5). The research confirms that the current stack (aiortc, sounddevice, PyOgg) can be extended with video tracks following the same patterns established for audio tracks.

**Key findings:**
- aiortc supports video via `VideoStreamTrack` subclasses, paralleling the existing `MicrophoneAudioTrack` pattern
- PyAV (av) provides VideoFrame objects for WebRTC transmission, similar to AudioFrame
- Camera access via OpenCV (cv2.VideoCapture) with cv2-enumerate-cameras for device enumeration
- Screen capture via MSS (python-mss) for cross-platform support (30-60 FPS typical)
- VP8 and H.264 codecs supported natively by aiortc with automatic SRTP encryption
- Video and audio use same RTCPeerConnection with multiple tracks (no separate connection needed)
- Track management (addTrack) follows existing patterns, but removeTrack has known limitations in aiortc

**Primary recommendation:** Extend existing VoiceCallService to VideoCallService, adding VideoStreamTrack implementations for camera and screen sharing. Use MSS for screen capture (cross-platform) and OpenCV for camera access. Leverage existing peer connection infrastructure from Phase 5.

## Standard Stack

The established libraries/tools for WebRTC video in Python:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiortc | 1.14.0+ | WebRTC implementation with video support | Industry standard Python WebRTC, VP8/H.264 codecs built-in, SRTP encryption mandatory |
| PyAV (av) | 16.1.0+ | VideoFrame objects for WebRTC | FFmpeg Python bindings, standard for video frame manipulation, used by aiortc |
| opencv-python | 4.x | Camera capture | Most mature cross-platform camera access, cv2.VideoCapture widely used |
| python-mss | 9.x | Screen capture | Ultra-fast cross-platform (30-60 FPS), pure Python, no dependencies, thread-safe |
| cv2-enumerate-cameras | 1.3.3+ | Camera enumeration | OpenCV lacks device enumeration API, this fills the gap (released Jan 2026) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | 10.0+ | Image processing | Already in Phase 4 for thumbnails, can convert between PIL and VideoFrame |
| numpy | 2.0+ | Array operations | Already in Phase 5 for audio, needed for VideoFrame.from_ndarray() |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-mss | DXcam (Windows only) | DXcam achieves 240+ FPS on Windows vs MSS 30-60 FPS, but Windows-only. Use MSS for cross-platform. |
| opencv-python | python-lite-camera | Lighter weight but less mature. OpenCV is battle-tested and ubiquitous. |

**Installation:**
```bash
pip install aiortc>=1.14.0 av>=16.1.0 opencv-python>=4.0 python-mss>=9.0 cv2-enumerate-cameras>=1.3.3
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── voice/                 # Extend to video/
    ├── audio_track.py     # Existing audio implementation
    ├── video_track.py     # NEW: CameraVideoTrack, ScreenShareTrack
    ├── call_service.py    # Extend to manage video tracks
    ├── device_manager.py  # Add camera enumeration
    └── models.py          # Add video-related state models
```

### Pattern 1: Custom VideoStreamTrack with Frame Timing
**What:** Subclass aiortc's VideoStreamTrack to provide camera or screen capture frames
**When to use:** All video streaming (camera, screen sharing)
**Example:**
```python
# Source: aiortc examples and dev.to article
from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np

class CameraVideoTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, device_id=0):
        super().__init__()
        self.cap = cv2.VideoCapture(device_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    async def recv(self):
        """WebRTC calls this to get next frame."""
        # Get timing for this frame (handles FPS pacing)
        pts, time_base = await self.next_timestamp()

        # Capture frame from camera
        ret, frame_bgr = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")

        # Convert BGR to RGB (OpenCV uses BGR)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Create VideoFrame from numpy array
        video_frame = VideoFrame.from_ndarray(frame_rgb, format='rgb24')
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    async def stop(self):
        if self.cap:
            self.cap.release()
```

### Pattern 2: Screen Capture VideoStreamTrack
**What:** Use python-mss to capture screen regions and convert to VideoFrame
**When to use:** Screen sharing feature
**Example:**
```python
# Based on MSS documentation and aiortc patterns
from mss import mss
import numpy as np

class ScreenShareTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, monitor_index=1):
        super().__init__()
        self.sct = mss()
        # monitor_index: 0=all monitors, 1=primary, 2+=secondary
        self.monitor = self.sct.monitors[monitor_index]

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # Grab screenshot as raw pixels
        sct_img = self.sct.grab(self.monitor)

        # Convert to numpy array (BGRA format from MSS)
        img_np = np.array(sct_img)

        # Convert BGRA to RGB (drop alpha, swap channels)
        img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGRA2RGB)

        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(img_rgb, format='rgb24')
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    async def stop(self):
        if self.sct:
            self.sct.close()
```

### Pattern 3: Adding Video Track to Existing Peer Connection
**What:** Add video track to the same RTCPeerConnection used for audio
**When to use:** Upgrading voice call to video, or starting video call
**Example:**
```python
# Based on existing VoiceCallService and aiortc patterns
async def add_video_track(self, track_type: str):
    """Add video track to active call."""
    if not self._pc:
        raise RuntimeError("No active peer connection")

    # Create appropriate video track
    if track_type == "camera":
        video_track = CameraVideoTrack(device_id=self._camera_device_id)
    elif track_type == "screen":
        video_track = ScreenShareTrack(monitor_index=1)
    else:
        raise ValueError(f"Unknown track type: {track_type}")

    # Add track to peer connection
    self._pc.addTrack(video_track)

    # Store reference for cleanup
    self._video_track = video_track

    # Renegotiation required (create new offer/answer)
    if self._is_caller:
        offer = await self._pc.createOffer()
        await self._pc.setLocalDescription(offer)
        await self._wait_for_ice()
        # Send offer via signaling
        await self.send_signaling({
            "type": "video_renegotiate_offer",
            "sdp": self._pc.localDescription.sdp
        })
```

### Pattern 4: Receiving Remote Video Track
**What:** Handle incoming video track from remote peer
**When to use:** Displaying remote participant's video or screen share
**Example:**
```python
# Based on existing AudioPlaybackTrack pattern in call_service.py
@pc.on("track")
async def on_track(track):
    logger.info(f"Received track: {track.kind}")

    if track.kind == "audio":
        # Existing audio handling (Phase 5)
        self._playback = AudioPlaybackTrack(device_id=self._output_device_id)
        asyncio.create_task(self._playback.handle_track(track))

    elif track.kind == "video":
        # NEW: Video handling
        # Store track reference
        self._remote_video_track = track

        # Notify UI that video is available
        self._notify_video_available(track)

        # UI will call get_video_frame() to receive frames
```

### Pattern 5: Camera Enumeration
**What:** List available cameras with names and indices
**When to use:** Settings UI for camera selection
**Example:**
```python
# Source: cv2-enumerate-cameras documentation
from cv2_enumerate_cameras import enumerate_cameras

def list_cameras():
    """Get list of available cameras."""
    cameras = []
    for camera_info in enumerate_cameras():
        cameras.append({
            "index": camera_info.index,
            "name": camera_info.name,
            "backend": camera_info.backend,
            "path": camera_info.path
        })
    return cameras

# Open specific camera
def open_camera(index, backend):
    return cv2.VideoCapture(index, backend)
```

### Anti-Patterns to Avoid
- **Separate peer connection for video:** Don't create a third RTCPeerConnection for video. The same PC handles audio + video tracks (per existing VoiceCallService pattern).
- **Blocking recv() method:** The recv() method must be async and should never block. Use async I/O for camera capture if needed.
- **Missing frame timing:** Always use `await self.next_timestamp()` and set pts/time_base. Without proper timing, video will have sync issues.
- **Memory leaks from unclosed resources:** Always close cv2.VideoCapture, mss.mss(), and stop tracks in cleanup methods.
- **Testing only localhost:** WebRTC video may work locally but fail over real networks due to bandwidth constraints or NAT issues. Always test with STUN/TURN.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Screen capture | Custom WinAPI/X11/Cocoa bindings | python-mss | Cross-platform, handles multi-monitor, 30-60 FPS, zero dependencies, thread-safe |
| Camera enumeration | Loop through cv2.VideoCapture(0..10) | cv2-enumerate-cameras | Gets actual camera names/paths, supports multiple backends, handles disappeared devices |
| Video frame timing | Manual timestamp calculation | VideoStreamTrack.next_timestamp() | aiortc handles pacing, drift correction, time_base calculations automatically |
| Codec negotiation | Custom SDP parsing for codec selection | aiortc automatic negotiation | VP8/H.264 negotiated automatically, handles profile-level-id, bandwidth params |
| Video format conversion | Manual pixel format conversion | VideoFrame.from_ndarray(), cv2.cvtColor() | PyAV handles format conversion (RGB, YUV, etc.), OpenCV handles color space transforms |
| Bandwidth adaptation | Manual bitrate control based on network | WebRTC automatic adaptation | VP8/H.264 encoders adapt to network conditions automatically via RTCP feedback |

**Key insight:** WebRTC video has decades of edge cases solved by browser implementations. aiortc follows those standards. Custom video streaming would require reimplementing codec negotiation, bandwidth adaptation, packet loss recovery, jitter buffering, and sync — all of which aiortc provides for free.

## Common Pitfalls

### Pitfall 1: aiortc removeTrack Not Supported
**What goes wrong:** Attempting to remove a video track and add a new one (e.g., switching camera to screen share) fails or doesn't trigger properly.
**Why it happens:** aiortc issue #1145 (Aug 2024) documents that removeTrack is not implemented. Only addTrack is supported.
**How to avoid:**
- Stop the existing track via `track.stop()`
- Create new offer/answer to renegotiate without the stopped track
- Alternative: Replace track content (e.g., switch CameraVideoTrack source internally) instead of adding/removing tracks
**Warning signs:** Track switching doesn't work, renegotiation fails, or old video keeps transmitting.

### Pitfall 2: BGR vs RGB Color Space Confusion
**What goes wrong:** Video appears with wrong colors (blue/red swapped) when displaying or transmitting.
**Why it happens:** OpenCV uses BGR color order by default, but VideoFrame.from_ndarray() expects RGB. MSS provides BGRA.
**How to avoid:** Always use `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)` when converting from OpenCV to VideoFrame. For MSS, use `cv2.COLOR_BGRA2RGB`.
**Warning signs:** Colors look wrong, skin tones appear blue-ish, red objects appear blue.

### Pitfall 3: Renegotiation Failures
**What goes wrong:** Adding video to existing audio call causes connection to fail or new track never starts transmitting.
**Why it happens:** aiortc has known issues with renegotiation (issue #1079, 2024). Initial negotiation succeeds, but changing tracks during active connection can fail.
**How to avoid:**
- Test renegotiation early in development
- Consider requiring video to be enabled at call start rather than mid-call
- If renegotiation is required, be prepared to fall back to full reconnection
**Warning signs:** Video call works from start, but adding video mid-call hangs or errors.

### Pitfall 4: Frame Rate Performance Degradation
**What goes wrong:** Screen sharing starts at 30 FPS but drops to 5-10 FPS during use, causing choppy experience.
**Why it happens:** Screen capture + encoding + transmission is CPU-intensive. MSS performance varies by platform (3x slower on Windows than platform-specific APIs).
**How to avoid:**
- Capture specific regions (smaller area = faster)
- Reduce resolution if needed (scale down before creating VideoFrame)
- Monitor CPU usage and warn user if excessive
- Consider 15-20 FPS target for screen sharing (not 30 FPS like camera)
**Warning signs:** High CPU usage, frame drops, choppy remote video.

### Pitfall 5: Missing Track Cleanup Leads to Resource Leaks
**What goes wrong:** Camera stays active after call ends, or multiple VideoCapture instances pile up, causing slowdowns.
**Why it happens:** Tracks hold resources (camera handles, MSS instances) that must be explicitly released.
**How to avoid:**
- Implement `async def stop()` on all custom tracks
- Call `track.stop()` before closing peer connection
- Use try/finally or context managers to ensure cleanup
**Warning signs:** Camera LED stays on after call, memory usage grows, subsequent calls fail to open camera.

### Pitfall 6: Testing Only Locally (WebRTC-Specific)
**What goes wrong:** Video works perfectly on localhost but fails or has terrible quality over real networks.
**Why it happens:** Local network has unlimited bandwidth, low latency, no packet loss. Real networks have constraints.
**How to avoid:**
- Test with STUN/TURN servers from day one (already in Phase 5)
- Test on cellular connection or VPN to simulate network variance
- Monitor bandwidth usage and verify adaptive bitrate is working
**Warning signs:** Localhost works great, but remote users report black screens, frozen video, or disconnections.

### Pitfall 7: Cross-Browser SDP Incompatibility (Safari)
**What goes wrong:** Video calls work between aiortc peers but fail when connecting to Safari browser.
**Why it happens:** Safari has different SDP formatting for video codecs, especially H.264 profile-level-id.
**How to avoid:**
- Test with Safari specifically (not just Chrome/Firefox)
- Verify VP8 is available as fallback (Safari supports both)
- Check aiortc logs for SDP parsing errors
**Warning signs:** Chrome/Firefox peers work, Safari peers fail during negotiation.

## Code Examples

Verified patterns from official sources:

### Camera Video Track Implementation
```python
# Source: https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id
# and https://github.com/aiortc/aiortc/blob/main/examples/videostream-cli/cli.py
from aiortc import VideoStreamTrack
from av import VideoFrame
import cv2
import asyncio

class CameraVideoTrack(VideoStreamTrack):
    """
    VideoStreamTrack that captures from camera using OpenCV.

    Follows aiortc pattern: subclass VideoStreamTrack and implement recv().
    """
    kind = "video"

    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        super().__init__()
        self.device_id = device_id
        self.cap = cv2.VideoCapture(device_id)

        # Configure camera
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {device_id}")

    async def recv(self) -> VideoFrame:
        """
        Receive next video frame for WebRTC transmission.

        Called by aiortc when it needs the next frame to send.
        """
        # Get proper timing for this frame (aiortc handles pacing)
        pts, time_base = await self.next_timestamp()

        # Capture frame from camera (synchronous, but fast ~1ms)
        ret, frame_bgr = self.cap.read()
        if not ret:
            # Camera error - return black frame to keep connection alive
            frame_bgr = np.zeros((480, 640, 3), dtype=np.uint8)

        # Convert BGR (OpenCV default) to RGB (VideoFrame requirement)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Create VideoFrame from numpy array
        video_frame = VideoFrame.from_ndarray(frame_rgb, format='rgb24')

        # Set timing metadata (required for proper playback)
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    async def stop(self):
        """Release camera resources."""
        super().stop()
        if self.cap:
            self.cap.release()
            self.cap = None
```

### Screen Sharing Track Implementation
```python
# Source: https://python-mss.readthedocs.io and aiortc patterns
from aiortc import VideoStreamTrack
from av import VideoFrame
from mss import mss
import numpy as np
import cv2

class ScreenShareTrack(VideoStreamTrack):
    """
    VideoStreamTrack that captures screen content using python-mss.

    Cross-platform screen capture at 30-60 FPS typical.
    """
    kind = "video"

    def __init__(self, monitor_index: int = 1, fps: int = 15):
        """
        Initialize screen share track.

        Args:
            monitor_index: 0=all monitors, 1=primary, 2+=secondary
            fps: Target frame rate (15 recommended for screen sharing)
        """
        super().__init__()
        self.sct = mss()
        self.monitor = self.sct.monitors[monitor_index]
        # Lower FPS for screen sharing (less CPU, still smooth)
        self.fps = fps

    async def recv(self) -> VideoFrame:
        """Capture screen and return as VideoFrame."""
        pts, time_base = await self.next_timestamp()

        # Grab screenshot (fast, ~5-10ms for 1920x1080)
        sct_img = self.sct.grab(self.monitor)

        # Convert to numpy array (BGRA format)
        img_bgra = np.array(sct_img)

        # Convert BGRA to RGB (drop alpha channel, swap B and R)
        img_rgb = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2RGB)

        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(img_rgb, format='rgb24')
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    async def stop(self):
        """Release screen capture resources."""
        super().stop()
        if self.sct:
            self.sct.close()
            self.sct = None
```

### Adding Video Track to Peer Connection
```python
# Source: aiortc examples and existing VoiceCallService patterns
async def enable_video(self, video_source: str = "camera"):
    """
    Add video track to active call.

    Args:
        video_source: "camera" or "screen"
    """
    if not self._pc:
        raise RuntimeError("No active peer connection")

    # Create video track
    if video_source == "camera":
        self._video_track = CameraVideoTrack(device_id=self._camera_device_id)
    elif video_source == "screen":
        self._video_track = ScreenShareTrack(monitor_index=1, fps=15)
    else:
        raise ValueError(f"Unknown video source: {video_source}")

    # Add to peer connection (same PC as audio)
    self._pc.addTrack(self._video_track)

    # Renegotiation: create new offer with video
    offer = await self._pc.createOffer()
    await self._pc.setLocalDescription(offer)

    # Wait for ICE gathering (following Phase 5 pattern)
    await self._wait_for_ice()

    # Send renegotiation offer via signaling
    await self.send_signaling({
        "type": "call_renegotiate",
        "sdp": self._pc.localDescription.sdp,
        "video_enabled": True
    })

    logger.info(f"Video enabled: {video_source}")

async def disable_video(self):
    """
    Stop video transmission (keep audio active).

    NOTE: aiortc doesn't support removeTrack, so we stop the track
    and renegotiate to remove it from SDP.
    """
    if not self._video_track:
        return

    # Stop the track
    await self._video_track.stop()
    self._video_track = None

    # Renegotiate without video track
    offer = await self._pc.createOffer()
    await self._pc.setLocalDescription(offer)
    await self._wait_for_ice()

    await self.send_signaling({
        "type": "call_renegotiate",
        "sdp": self._pc.localDescription.sdp,
        "video_enabled": False
    })

    logger.info("Video disabled")
```

### Camera Enumeration
```python
# Source: https://pypi.org/project/cv2-enumerate-cameras/
from cv2_enumerate_cameras import enumerate_cameras
import cv2

def get_available_cameras():
    """
    List available cameras with names and indices.

    Returns list of dicts with camera info.
    """
    cameras = []
    for camera_info in enumerate_cameras():
        cameras.append({
            "index": camera_info.index,
            "name": camera_info.name,
            "backend": camera_info.backend,
            "path": camera_info.path
        })
    return cameras

def test_camera(camera_info):
    """
    Test if camera can be opened successfully.

    Args:
        camera_info: Dict from get_available_cameras()

    Returns:
        True if camera works, False otherwise
    """
    cap = cv2.VideoCapture(camera_info["index"], camera_info["backend"])
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        return ret
    return False
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Multiple RTCPeerConnections for audio/video/data | Single RTCPeerConnection with multiple tracks | WebRTC standard (2017+) | Simpler connection management, faster renegotiation, Phase 5 already uses this |
| Manual codec negotiation via SDP manipulation | Automatic codec negotiation by aiortc | aiortc 1.0+ (2020) | No need to parse/modify SDP for codec selection |
| PIL/Pillow for video frames | PyAV VideoFrame with FFmpeg | PyAV 8.0+ (2020) | Better performance, native WebRTC integration |
| Platform-specific screen capture (ctypes) | python-mss cross-platform | mss 3.0+ (2016) | One API for Windows/Mac/Linux |
| Browser-only WebRTC | Python WebRTC via aiortc | aiortc 1.0+ (2020) | Desktop apps can use WebRTC without Electron |

**Deprecated/outdated:**
- **MediaRecorder API for Python:** Never existed. aiortc is the standard Python WebRTC implementation.
- **SimpleWebRTC.py:** Abandoned project, use aiortc instead.
- **PyAV older than 8.0:** Breaking API changes in 8.0 (2020), use 16.1.0+ for latest FFmpeg compatibility.

## Open Questions

Things that couldn't be fully resolved:

1. **aiortc removeTrack Support**
   - What we know: Issue #1145 (Aug 2024) states removeTrack not implemented, only addTrack
   - What's unclear: Whether workaround (stop track + renegotiate) reliably removes it from SDP
   - Recommendation: Test track stop + renegotiation early. If unreliable, require video/screen choice at call start (no mid-call switching).

2. **Camera Switching During Active Call**
   - What we know: Can't removeTrack in aiortc, camera is held by VideoCapture instance
   - What's unclear: Can CameraVideoTrack.recv() internally switch cv2.VideoCapture sources, or does that break frame timing?
   - Recommendation: Prototype internal source switching. If timing breaks, fall back to stop + add new track pattern.

3. **Screen Sharing Performance on Multi-Monitor Setups**
   - What we know: MSS supports multi-monitor (monitor_index=0 captures all), 30-60 FPS typical
   - What's unclear: FPS when capturing 3840x1080 (dual 1920x1080) vs single monitor
   - Recommendation: Test multi-monitor performance early. May need resolution scaling or monitor selection UI.

4. **VP8 vs H.264 Codec Selection Strategy**
   - What we know: aiortc supports both, negotiates automatically. H.264 more efficient but licensing concerns. VP8 more compatible.
   - What's unclear: Which codec aiortc prefers by default, whether we can influence priority
   - Recommendation: Let aiortc negotiate automatically. Monitor which codec is used in testing. Only intervene if compatibility issues arise.

5. **Video Quality Settings Exposure**
   - What we know: aiortc adapts bitrate automatically via WebRTC standards. Bandwidth limits can be set via SDP modification.
   - What's unclear: Whether users expect manual quality controls (low/medium/high) or automatic is sufficient
   - Recommendation: Start with automatic adaptation. Add manual controls only if users report issues with auto-quality.

## Sources

### Primary (HIGH confidence)
- [aiortc GitHub Repository](https://github.com/aiortc/aiortc) - Official WebRTC implementation, examples reviewed
- [PyAV Video API Documentation](https://pyav.org/docs/develop/api/video.html) - VideoFrame class reference
- [python-mss GitHub Repository](https://github.com/BoboTiG/python-mss) - Screen capture library, API confirmed
- [cv2-enumerate-cameras PyPI](https://pypi.org/project/cv2-enumerate-cameras/) - Latest release Jan 16, 2026

### Secondary (MEDIUM confidence)
- [Python WebRTC basics with aiortc - DEV Community](https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id) - Practical implementation guide
- [aiortc videostream-cli example](https://github.com/aiortc/aiortc/blob/main/examples/videostream-cli/cli.py) - Official example code
- [PyAV Installation Documentation](https://pyav.org/docs/develop/overview/installation.html) - Dependency requirements
- [MDN WebRTC Codecs](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/WebRTC_codecs) - VP8/H.264 standards
- [RFC 7742: WebRTC Video Processing and Codec Requirements](https://www.rfc-editor.org/rfc/rfc7742.html) - Official codec requirements

### Tertiary (LOW confidence - flagged for validation)
- [aiortc Issue #1145](https://github.com/aiortc/aiortc/issues/1145) - removeTrack not supported (Aug 2024) - needs testing to confirm current status
- [aiortc Issue #1079](https://github.com/aiortc/aiortc/issues/1079) - Renegotiation failures (2024) - may be fixed in 1.14.0
- [WebRTC common mistakes - BlogGeek.me](https://bloggeek.me/common-beginner-mistakes-in-webrtc/) - Best practices article
- [WebRTC Security Guide - Ant Media](https://antmedia.io/webrtc-security/) - SRTP encryption overview

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - aiortc and PyAV are well-documented and stable, but specific integration patterns verified via examples rather than official docs
- Architecture: MEDIUM - Patterns based on official examples and existing Phase 5 code, but video-specific edge cases not fully tested
- Pitfalls: MEDIUM - Known issues documented in GitHub issues, but workarounds need validation. Cross-browser testing not completed.

**Research date:** 2026-01-31
**Valid until:** 2026-02-28 (30 days - stable domain, but aiortc issues may be resolved)
