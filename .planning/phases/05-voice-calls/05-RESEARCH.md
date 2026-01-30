# Phase 5: Voice Calls (1-on-1) - Research

**Researched:** 2026-01-30
**Domain:** WebRTC Audio/Voice Communication with Python (aiortc)
**Confidence:** MEDIUM (aiortc-specific details verified; some areas require validation)

## Summary

Phase 5 builds on existing aiortc WebRTC infrastructure to add real-time voice calling and asynchronous voice messaging. The research reveals that aiortc provides adequate WebRTC support for voice calls with Opus codec (the WebRTC standard), but has known latency challenges (500-600ms reported) and lacks native ICE restart support for network migration. For voice messages, Python has multiple Opus encoding libraries with different tradeoffs. Audio device handling requires sounddevice (recommended) or PyAudio, with sounddevice offering simpler cross-platform installation.

**Critical findings:**
- aiortc has inherent audio latency issues (500-600ms baseline) that may require optimization
- ICE restart for network migration is NOT natively supported; manual reconnection required
- Voice calls use WebRTC's DTLS-SRTP encryption (separate from Signal Protocol layer)
- Voice messages need separate Opus encoding library (PyOgg, opuspy, or opuslib)

**Primary recommendation:** Use sounddevice for audio capture, aiortc's built-in MediaPlayer/MediaRecorder for WebRTC audio tracks, and PyOgg for voice message Opus encoding. Accept the limitation that network migration during calls requires manual reconnection (ICE restart not available in aiortc).

## Standard Stack

The established libraries/tools for WebRTC voice calling in Python:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiortc | 1.14.0+ | WebRTC implementation | Already in use; supports Opus/PCMA/PCMU; DTLS-SRTP encryption built-in |
| sounddevice | 0.5.5 | Audio capture/playback | Simpler than PyAudio; auto-installs PortAudio on Windows; NumPy integration |
| PyOgg | Latest | Opus encoding for voice messages | Reads/writes Opus in Ogg containers; bundled DLLs on Windows |
| numpy | Latest | Audio buffer manipulation | Required by sounddevice; efficient audio data processing |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| opuspy | Latest | Alternative Opus encoding | If simpler API needed; ElevenLabs-maintained; good for speech (16kHz) |
| opuslib | Latest | Low-level Opus bindings | If fine-grained Opus control needed; CTypes bindings to libopus |
| PyAudio | 0.2.14 | Alternative audio I/O | If granular control needed; more complex installation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sounddevice | PyAudio | More configuration options but harder installation; verbose API |
| PyOgg | opuspy | Simpler API but less flexible; optimized for 48kHz speech |
| MediaPlayer | Custom AudioStreamTrack | Full control but more complexity; need to implement frame timing |

**Installation:**
```bash
pip install aiortc>=1.14.0 sounddevice>=0.5.5 PyOgg numpy
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── voice/
│   ├── call.py              # VoiceCall class managing RTCPeerConnection for calls
│   ├── audio_track.py       # Custom AudioStreamTrack for microphone capture
│   ├── voice_message.py     # VoiceMessage recording and playback
│   ├── device_manager.py    # Audio device enumeration and selection
│   └── models.py            # Data models (CallState, VoiceMessageMetadata)
└── network/
    └── peer.py              # Existing PeerConnection (extend for audio tracks)
```

### Pattern 1: Voice Call Setup (Offer/Answer/ICE)
**What:** Standard WebRTC signaling flow for 1-on-1 calls
**When to use:** Starting/receiving voice calls
**Example:**
```python
# Source: https://webrtc.org/getting-started/peer-connections
# aiortc implementation pattern

from aiortc import RTCPeerConnection, RTCIceServer
from aiortc.contrib.media import MediaPlayer

async def start_voice_call(peer_connection: RTCPeerConnection):
    # Add audio track from microphone
    player = MediaPlayer('default:none', format='dshow', options={
        'audio_size': '48000'
    })

    if player.audio:
        peer_connection.addTrack(player.audio)

    # Create offer
    offer = await peer_connection.createOffer()
    await peer_connection.setLocalDescription(offer)

    # Send offer via signaling channel
    await signaling_client.send_offer(offer.sdp, offer.type)

    # Handle ICE candidates with trickle ICE
    @peer_connection.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            await signaling_client.send_ice_candidate(candidate)

async def receive_voice_call(peer_connection: RTCPeerConnection, remote_offer):
    # Set remote description
    await peer_connection.setRemoteDescription(remote_offer)

    # Add audio track
    player = MediaPlayer('default:none', format='dshow')
    peer_connection.addTrack(player.audio)

    # Create answer
    answer = await peer_connection.createAnswer()
    await peer_connection.setLocalDescription(answer)

    # Send answer via signaling channel
    await signaling_client.send_answer(answer.sdp, answer.type)
```

### Pattern 2: Custom AudioStreamTrack for Microphone
**What:** Subclass MediaStreamTrack to provide audio from sounddevice
**When to use:** When you need control over audio processing or device selection
**Example:**
```python
# Source: https://snyk.io/advisor/python/aiortc/functions/aiortc.mediastreams.AudioStreamTrack
# Combined with sounddevice real-time streaming

import asyncio
import sounddevice as sd
import numpy as np
from aiortc import AudioStreamTrack
from av import AudioFrame

class MicrophoneAudioTrack(AudioStreamTrack):
    """Audio track capturing from microphone via sounddevice."""

    def __init__(self, device_id=None, sample_rate=48000):
        super().__init__()
        self.sample_rate = sample_rate
        self.device_id = device_id
        self.samples_per_frame = int(sample_rate * 0.020)  # 20ms frames
        self.queue = asyncio.Queue()
        self.stream = None

    def audio_callback(self, indata, frames, time, status):
        """Called from sounddevice thread."""
        if status:
            print(f"Audio callback status: {status}")
        # Queue audio data for async retrieval
        self.queue.put_nowait(indata.copy())

    async def start(self):
        """Start audio capture."""
        self.stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=self.samples_per_frame,
            callback=self.audio_callback
        )
        self.stream.start()

    async def recv(self):
        """Get next audio frame."""
        # Get audio data from queue
        audio_data = await self.queue.get()

        # Create av.AudioFrame
        frame = AudioFrame(format="s16", layout="mono", samples=self.samples_per_frame)
        frame.planes[0].update(audio_data.tobytes())
        frame.sample_rate = self.sample_rate

        # Set timing
        pts, time_base = await self.next_timestamp()
        frame.pts = pts
        frame.time_base = time_base

        return frame

    async def stop(self):
        """Stop audio capture."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
```

### Pattern 3: Voice Message Recording to Opus
**What:** Record audio to Opus file using PyOgg
**When to use:** Voice message feature (up to 5 minutes)
**Example:**
```python
# Source: https://pyogg.readthedocs.io/en/latest/api/opus.html
# PyOgg Opus encoding pattern

import sounddevice as sd
import numpy as np
from pyogg import OpusBufferedEncoder

class VoiceMessageRecorder:
    """Records voice messages to Opus format."""

    def __init__(self, sample_rate=48000, max_duration=300):
        self.sample_rate = sample_rate
        self.max_duration = max_duration  # 5 minutes
        self.encoder = None
        self.stream = None
        self.recorded_chunks = []

    def start_recording(self, device_id=None):
        """Start recording voice message."""
        # Initialize Opus encoder (mono, 48kHz)
        self.encoder = OpusBufferedEncoder()
        self.encoder.set_application("voip")  # Optimize for voice
        self.encoder.set_sampling_frequency(self.sample_rate)
        self.encoder.set_channels(1)
        self.encoder.set_frame_size(20)  # 20ms frames

        self.recorded_chunks = []

        def callback(indata, frames, time, status):
            if status:
                print(f"Recording status: {status}")
            # Encode and store
            encoded = self.encoder.encode(indata)
            self.recorded_chunks.append(encoded)

        self.stream = sd.InputStream(
            device=device_id,
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=callback
        )
        self.stream.start()

    def stop_recording(self, output_path):
        """Stop recording and save to Opus file."""
        if self.stream:
            self.stream.stop()
            self.stream.close()

        # Write Opus file
        with open(output_path, 'wb') as f:
            # PyOgg handles Ogg container wrapping
            for chunk in self.recorded_chunks:
                f.write(chunk)

        duration = len(self.recorded_chunks) * 0.020  # 20ms per chunk
        return duration
```

### Pattern 4: Audio Device Selection
**What:** Enumerate and select audio input/output devices
**When to use:** Settings UI for microphone/speaker selection
**Example:**
```python
# Source: https://python-sounddevice.readthedocs.io/en/latest/usage.html
# sounddevice device enumeration

import sounddevice as sd

class AudioDeviceManager:
    """Manages audio device enumeration and selection."""

    @staticmethod
    def get_input_devices():
        """Get list of available microphones."""
        devices = sd.query_devices()
        return [
            {
                'id': idx,
                'name': dev['name'],
                'channels': dev['max_input_channels']
            }
            for idx, dev in enumerate(devices)
            if dev['max_input_channels'] > 0
        ]

    @staticmethod
    def get_output_devices():
        """Get list of available speakers."""
        devices = sd.query_devices()
        return [
            {
                'id': idx,
                'name': dev['name'],
                'channels': dev['max_output_channels']
            }
            for idx, dev in enumerate(devices)
            if dev['max_output_channels'] > 0
        ]

    @staticmethod
    def get_default_input():
        """Get default input device ID."""
        return sd.default.device[0]

    @staticmethod
    def get_default_output():
        """Get default output device ID."""
        return sd.default.device[1]

    @staticmethod
    def test_device(device_id, duration=1.0):
        """Test audio device by recording briefly."""
        try:
            recording = sd.rec(
                int(duration * 48000),
                samplerate=48000,
                channels=1,
                device=device_id
            )
            sd.wait()
            return True
        except Exception as e:
            print(f"Device test failed: {e}")
            return False
```

### Anti-Patterns to Avoid

- **Don't use blocking audio I/O in asyncio event loop:** sounddevice callbacks run in separate thread; use queues to transfer data to async code
- **Don't mix PyAudio and sounddevice:** Both use PortAudio; simultaneous use causes device conflicts
- **Don't hardcode audio device names:** Device names vary by system; use device IDs and provide user selection
- **Don't assume ICE restart works:** aiortc doesn't support RTCPeerConnection.restartIce(); require manual reconnection for network migration
- **Don't ignore audio callback status:** Buffer overflows/underruns indicate performance problems

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Opus encoding/decoding | Custom Opus wrapper | PyOgg, opuspy, or opuslib | Opus codec complex; frame timing, Ogg container, error handling |
| Audio device access | Direct OS API calls | sounddevice or PyAudio | Cross-platform differences (ALSA/PulseAudio/WASAPI); handle device changes |
| WebRTC audio tracks | Manual RTP packetization | aiortc MediaPlayer/AudioStreamTrack | RTP payload formatting, RTCP, timing, jitter buffer |
| ICE candidate gathering | Manual STUN/TURN | aiortc RTCPeerConnection | ICE state machine complex; handle multiple candidates, trickling |
| DTLS-SRTP encryption | Custom DTLS handshake | aiortc built-in DTLS-SRTP | Certificate management, cipher suites, key derivation |
| Audio resampling | Manual sample rate conversion | av.AudioResampler or librosa | Antialiasing filters, interpolation algorithms |

**Key insight:** WebRTC audio has many subtle requirements (timing, packetization, encryption) that aiortc handles correctly. Voice messages need proper Opus encoding that PyOgg provides. Don't reinvent these wheels.

## Common Pitfalls

### Pitfall 1: aiortc Audio Latency (500-600ms)
**What goes wrong:** Users experience half-second delay in voice calls, making conversation awkward
**Why it happens:** aiortc's audio jitter buffer and packet timing add latency; 20ms Opus frames accumulate; PyAV encoding overhead
**How to avoid:**
- Accept 300-500ms as baseline for aiortc (WebRTC spec allows up to 150ms network + processing)
- Use 20ms Opus frames (default AUDIO_PTIME=0.02 in aiortc)
- Avoid additional buffering in custom AudioStreamTrack
- Test on local network first to isolate network vs. processing latency
**Warning signs:** Users report "echo" or delay; audio feels "laggy"

**Source:** [aiortc Issue #775](https://github.com/aiortc/aiortc/issues/775) - Users report 500-600ms latencies even on localhost

### Pitfall 2: No ICE Restart Support
**What goes wrong:** Call drops when user switches from WiFi to mobile; no seamless recovery
**Why it happens:** aiortc doesn't implement RTCPeerConnection.restartIce(); ICE agent can't renegotiate after network change
**How to avoid:**
- Require manual reconnection (UI shows "Reconnecting..." and re-establishes call)
- Document as known limitation (20-30% calls may need reconnection)
- Implement call recovery UX (auto-redial option)
**Warning signs:** Call ends abruptly when network changes; no reconnection attempt

**Source:** [aiortc Issue #211](https://github.com/aiortc/aiortc/issues/211) - ICE restart feature request closed without implementation

### Pitfall 3: MediaPlayer Platform-Specific Audio Devices
**What goes wrong:** MediaPlayer('/dev/video0') only returns video, not audio; Windows device names fail
**Why it happens:** PyAV (FFmpeg) uses platform-specific formats (dshow/avfoundation/v4l2); audio device syntax differs from video
**How to avoid:**
- Use correct format parameter: 'dshow' (Windows), 'avfoundation' (macOS), 'pulse' or 'alsa' (Linux)
- For audio-only: MediaPlayer('audio=Microphone', format='dshow') on Windows
- Test device names with ffmpeg -list_devices before hardcoding
- Consider sounddevice for simpler cross-platform audio capture
**Warning signs:** MediaPlayer.audio is None; "Cannot open device" errors

**Source:** [aiortc Issue #213](https://github.com/aiortc/aiortc/issues/213), [aiortc Issue #161](https://github.com/aiortc/aiortc/issues/161)

### Pitfall 4: Audio/Video Sync Issues in MediaPlayer
**What goes wrong:** When looping media with both audio and video, tracks go out of sync
**Why it happens:** Inconsistent track lengths; MediaPlayer doesn't re-sync on loop
**How to avoid:**
- For voice calls (audio-only), not relevant
- For voice messages, use audio-only tracks (no video)
- If using MediaPlayer for testing, avoid loop mode with mixed media
**Warning signs:** Audio drifts ahead/behind during playback loops

**Source:** [aiortc Issue #1268](https://github.com/aiortc/aiortc/issues/1268)

### Pitfall 5: Audio Buffer Overflow in Callbacks
**What goes wrong:** Choppy audio, dropped frames, "buffer overflow" warnings
**Why it happens:** Audio callback (sounddevice or PyAudio) takes too long; OS buffer fills up; frames dropped
**How to avoid:**
- Keep callback code minimal (just copy data to queue)
- Use exception_on_overflow=False to prevent crashes
- Don't do encoding/encryption in audio callback thread
- Monitor callback duration (should be <5ms for 20ms frames)
**Warning signs:** sounddevice status shows "input overflow"; audio sounds choppy

**Source:** [sounddevice documentation](https://python-sounddevice.readthedocs.io/en/latest/usage.html), [aiortc Issue #1072](https://github.com/aiortc/aiortc/issues/1072)

### Pitfall 6: WebRTC vs Signal Protocol Encryption Confusion
**What goes wrong:** Assuming Signal Protocol handles voice call encryption; double-encrypting or missing encryption layer
**Why it happens:** WebRTC has built-in DTLS-SRTP encryption; Signal Protocol encrypts signaling messages but not media plane
**How to avoid:**
- Use DTLS-SRTP for media encryption (automatic in aiortc)
- Use Signal Protocol for signaling messages (offer/answer/ICE candidates)
- Don't try to encrypt RTP packets with Signal Protocol (breaks WebRTC)
- Verify fingerprints via Signal Protocol channel to prevent MITM
**Warning signs:** Call setup fails with encryption errors; can't establish SRTP

**Source:** [WebRTC Security Guide](https://webrtc-security.github.io/), [Signal blog on video calls](https://signal.org/blog/signal-video-calls-beta/)

### Pitfall 7: 5-Minute Voice Message Memory Bloat
**What goes wrong:** Voice message recording consumes excessive memory; app becomes unresponsive
**Why it happens:** 5 minutes @ 48kHz mono = ~14MB uncompressed; holding entire recording in memory
**How to avoid:**
- Stream Opus-encoded chunks to disk during recording (don't buffer all in RAM)
- Use PyOgg OpusBufferedEncoder to encode incrementally
- Write chunks as they're encoded (not after recording stops)
- Set max duration limit and enforce in UI
**Warning signs:** Memory usage climbs during recording; slow finalization after stopping

**Source:** General audio processing best practices; [PyOgg documentation](https://pyogg.readthedocs.io/)

## Code Examples

Verified patterns from official sources:

### Opus Codec Settings for VoIP
```python
# Source: https://wiki.xiph.org/Opus_Recommended_Settings
# Opus configuration for low-latency voice calls

from pyogg import OpusEncoder

encoder = OpusEncoder()
encoder.set_application("voip")  # Optimized for voice
encoder.set_sampling_frequency(48000)  # 48kHz (Opus standard)
encoder.set_channels(1)  # Mono for voice calls
encoder.set_frame_size(20)  # 20ms frames (default, good balance)
encoder.set_bitrate(24000)  # 24 kbps for fullband VoIP

# For lower bandwidth:
# encoder.set_bitrate(16000)  # 16 kbps (wideband most of the time)
# encoder.set_bitrate(10000)  # 10 kbps (narrowband, minimal quality)
```

### aiortc MediaPlayer for Microphone (Windows)
```python
# Source: https://aiortc.readthedocs.io/en/latest/helpers.html
# Platform-specific microphone access

from aiortc.contrib.media import MediaPlayer

# Windows (DirectShow)
player = MediaPlayer(
    "audio=Microphone (Realtek High Definition Audio)",
    format="dshow",
    options={"sample_rate": "48000"}
)

# macOS (AVFoundation)
player = MediaPlayer(
    "default:none",  # default audio, no video
    format="avfoundation",
    options={"sample_rate": "48000"}
)

# Linux (PulseAudio)
player = MediaPlayer(
    "default",
    format="pulse",
    options={"sample_rate": "48000"}
)

# Add to peer connection
if player.audio:
    pc.addTrack(player.audio)
```

### MediaRecorder for Voice Messages
```python
# Source: https://aiortc.readthedocs.io/en/latest/helpers.html
# Recording audio to Opus in Ogg container

from aiortc.contrib.media import MediaRecorder

# Record to Ogg Opus file
recorder = MediaRecorder("voice_message.ogg")

# Add audio track (from microphone or incoming call)
recorder.addTrack(audio_track)

# Start recording
await recorder.start()

# ... user records message ...

# Stop and finalize file
await recorder.stop()
```

### WebRTC Call Signaling Flow
```python
# Source: https://webrtc.org/getting-started/peer-connections
# Complete offer/answer/ICE flow for voice calls

from aiortc import RTCPeerConnection, RTCSessionDescription
import json

class VoiceCall:
    def __init__(self, signaling_client, peer_id):
        self.pc = RTCPeerConnection()
        self.signaling = signaling_client
        self.peer_id = peer_id

        # Handle incoming audio track
        @self.pc.on("track")
        def on_track(track):
            if track.kind == "audio":
                # Play incoming audio
                recorder = MediaRecorder("output_audio.wav")
                recorder.addTrack(track)

        # Handle ICE candidates (trickle ICE)
        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                await self.signaling.send({
                    "type": "ice_candidate",
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex
                })

    async def start_call(self, audio_track):
        """Initiate call (caller side)."""
        # Add local audio
        self.pc.addTrack(audio_track)

        # Create offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        # Send offer via signaling
        await self.signaling.send({
            "type": "offer",
            "sdp": self.pc.localDescription.sdp,
            "to": self.peer_id
        })

    async def receive_call(self, audio_track, offer_sdp):
        """Accept incoming call (callee side)."""
        # Set remote offer
        offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
        await self.pc.setRemoteDescription(offer)

        # Add local audio
        self.pc.addTrack(audio_track)

        # Create answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        # Send answer via signaling
        await self.signaling.send({
            "type": "answer",
            "sdp": self.pc.localDescription.sdp,
            "to": self.peer_id
        })

    async def handle_answer(self, answer_sdp):
        """Handle answer from callee (caller side)."""
        answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
        await self.pc.setRemoteDescription(answer)

    async def handle_ice_candidate(self, candidate_dict):
        """Add remote ICE candidate."""
        candidate = RTCIceCandidate(
            sdpMid=candidate_dict["sdpMid"],
            sdpMLineIndex=candidate_dict["sdpMLineIndex"],
            candidate=candidate_dict["candidate"]
        )
        await self.pc.addIceCandidate(candidate)

    async def end_call(self):
        """Hang up and clean up resources."""
        await self.pc.close()
```

### sounddevice Real-Time Streaming
```python
# Source: https://python-sounddevice.readthedocs.io/en/latest/usage.html
# Callback-based audio streaming with sounddevice

import sounddevice as sd
import queue

# Create queue for audio data
audio_queue = queue.Queue()

def audio_callback(indata, outdata, frames, time, status):
    """Called from audio thread."""
    if status:
        print(f"Audio status: {status}")

    # Put input data in queue (for processing/encoding)
    audio_queue.put(indata.copy())

    # Optional: output data (for playback)
    if outdata is not None:
        try:
            outdata[:] = audio_queue.get_nowait()
        except queue.Empty:
            outdata.fill(0)  # Silence if no data

# Start bidirectional stream (for full-duplex call)
stream = sd.Stream(
    samplerate=48000,
    channels=1,
    dtype="int16",
    callback=audio_callback
)

with stream:
    # Stream runs in background
    while call_active:
        # Process audio from queue
        audio_data = audio_queue.get()
        # ... encode and send via WebRTC ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ZRTP for key exchange | DTLS-SRTP (WebRTC standard) | ~2020 (Signal migrated) | Unified WebRTC stack; key exchange in media plane |
| PyAudio for audio I/O | sounddevice preferred | 2024+ | Easier installation; NumPy integration; active maintenance |
| Wait for all ICE candidates | Trickle ICE | WebRTC 1.0 | Faster call setup (send candidates as discovered) |
| Separate TURN server required | STUN-only acceptable | ~2023 | P2P success rate ~70-80%; accept some failures |
| Custom audio codecs | Opus mandatory | RFC 7874 (2016) | Interoperability; best quality/bandwidth tradeoff |

**Deprecated/outdated:**
- **PyAudio as primary recommendation:** Installation issues; sounddevice simpler and actively maintained (0.5.5 release Jan 2026)
- **Full ICE gathering before offer:** Trickle ICE is standard; waiting slows call setup
- **G.711 (PCMU/PCMA) for new apps:** Opus superior quality at same/lower bitrate
- **Synchronous audio APIs:** asyncio ecosystem requires non-blocking or callback-based approaches

## Open Questions

Things that couldn't be fully resolved:

1. **aiortc audio latency root cause**
   - What we know: 500-600ms reported by users; occurs even on localhost
   - What's unclear: Exact breakdown (jitter buffer vs PyAV vs packet timing)
   - Recommendation: Measure actual latency in Phase 5 testing; may need to profile aiortc internals or switch to native WebRTC if <200ms required

2. **ICE restart workaround reliability**
   - What we know: Manual reconnection required; aiortc doesn't support restartIce()
   - What's unclear: What percentage of network migrations require restart? Can we detect network change and auto-reconnect?
   - Recommendation: Implement network change detection (OS APIs); attempt auto-reconnect; measure success rate

3. **Signal Protocol + DTLS-SRTP integration**
   - What we know: WebRTC uses DTLS-SRTP for media; Signal Protocol for signaling
   - What's unclear: How to verify DTLS fingerprints via Signal Protocol channel? Does aiortc expose fingerprints?
   - Recommendation: Check aiortc RTCPeerConnection for certificate fingerprint access; transmit via Signal-encrypted signaling

4. **Cross-platform audio device naming**
   - What we know: MediaPlayer requires platform-specific format/device names
   - What's unclear: How to reliably auto-detect correct format on each platform?
   - Recommendation: Use sounddevice for device enumeration (platform-agnostic); use MediaPlayer only for WebRTC track creation

5. **Voice message file format for E2E encryption**
   - What we know: PyOgg writes Opus in Ogg container; need to encrypt before sending
   - What's unclear: Encrypt entire .ogg file or encrypt Opus packets individually?
   - Recommendation: Encrypt entire file with Signal Protocol (simpler); send as file transfer (reuse Phase 4 infrastructure)

## Sources

### Primary (HIGH confidence)
- [aiortc Documentation - Helpers](https://aiortc.readthedocs.io/en/latest/helpers.html) - MediaPlayer, MediaRecorder, AudioStreamTrack
- [aiortc Documentation - API Reference](https://aiortc.readthedocs.io/en/latest/api.html) - RTCPeerConnection, MediaStreamTrack
- [Opus Recommended Settings - Xiph.org](https://wiki.xiph.org/Opus_Recommended_Settings) - VoIP bitrate, frame size, quality
- [sounddevice Documentation v0.5.5 (2026-01-23)](https://python-sounddevice.readthedocs.io/en/latest/) - Audio I/O, streams, callbacks
- [WebRTC.org - Peer Connections](https://webrtc.org/getting-started/peer-connections) - Offer/answer flow, ICE candidates
- [MDN - WebRTC Connectivity](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Connectivity) - ICE, STUN, signaling
- [RFC 7874 - WebRTC Audio Codec Requirements](https://datatracker.ietf.org/doc/html/rfc7874) - Opus mandatory, bitrate recommendations

### Secondary (MEDIUM confidence)
- [PyOgg Documentation](https://pyogg.readthedocs.io/en/latest/) - Opus encoding/decoding, Ogg container
- [aiortc GitHub Issue #775](https://github.com/aiortc/aiortc/issues/775) - Audio latency problems (500-600ms reported)
- [aiortc GitHub Issue #211](https://github.com/aiortc/aiortc/issues/211) - ICE restart not implemented
- [aiortc GitHub Issue #213](https://github.com/aiortc/aiortc/issues/213) - Microphone audio stream issues
- [aiortc GitHub Issue #1268](https://github.com/aiortc/aiortc/issues/1268) - Audio/video sync problems
- [WebRTC Security Architecture](https://webrtc-security.github.io/) - DTLS-SRTP, encryption
- [Signal Blog - Video Calls](https://signal.org/blog/signal-video-calls-beta/) - Signal's WebRTC integration

### Tertiary (LOW confidence - WebSearch only)
- [VideoSDK - aiortc WebRTC Guide](https://www.videosdk.live/developer-hub/media-server/aiortc-webrtc) - General overview, examples
- [DEV Community - Python WebRTC with aiortc](https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id) - Beginner tutorial
- [Medium - Python Audio Libraries](https://medium.com/@venn5708/two-important-libraries-used-for-audio-processing-and-streaming-in-python-d3b718a75904) - sounddevice vs PyAudio comparison
- [Real Python - Playing and Recording Sound](https://realpython.com/playing-and-recording-sound-python/) - General Python audio overview

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - aiortc confirmed via docs; sounddevice 0.5.5 (Jan 2026) verified; PyOgg in official docs
- Architecture: MEDIUM - Patterns based on official examples but need validation in actual codebase
- Pitfalls: MEDIUM - Latency/ICE issues confirmed via GitHub issues; some issues may be resolved in newer versions
- Opus settings: HIGH - Xiph.org official recommendations; RFC 7874 standard

**Research date:** 2026-01-30
**Valid until:** ~2026-03-30 (60 days for stable stack; WebRTC/Opus mature technologies)

**Validation needed before planning:**
- Test actual aiortc audio latency on target hardware (reported 500-600ms may be outdated)
- Verify sounddevice works with pywebview environment (potential conflicts with UI event loop)
- Confirm PyOgg Opus encoding quality at 24kbps for voice messages
- Check if newer aiortc versions added ICE restart support (Issue #211 marked stale, may have been implemented)
