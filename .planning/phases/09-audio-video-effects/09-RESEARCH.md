# Phase 9: Audio & Video Effects - Research

**Researched:** 2026-02-02
**Domain:** Real-time audio/video processing with AI noise cancellation, DSP effects, virtual backgrounds, beauty filters, and AR overlays
**Confidence:** HIGH

## Summary

Phase 9 adds professional audio and video effects to the existing aiortc-based WebRTC infrastructure (Phases 5-6). The standard approach uses AI-based noise cancellation (DeepFilterNet3 primary, RNNoise fallback), Spotify's Pedalboard for audio effects, MediaPipe for face tracking and background segmentation, and OpenCV for video filters. All processing runs locally with GPU acceleration when available and CPU fallback for compatibility.

**Key findings:**
- DeepFilterNet3 provides superior audio quality (PESQ 3.5-4.0+) with acceptable latency (~50-100ms) on modern hardware, while RNNoise offers ultra-low latency (10-20ms) for CPU-only fallback
- Pedalboard (by Spotify) is the production-ready solution for real-time audio effects with VST3 plugin support
- MediaPipe offers both face landmarks (478 points) and selfie segmentation with sub-35ms latency on mobile GPUs, perfect for AR filters and virtual backgrounds
- OpenCV with threading can achieve 30-60 FPS for real-time video processing, sufficient for beauty filters and creative effects
- aiortc's decoupled architecture makes it trivial to insert audio/video processing pipelines between capture and transmission

**Primary recommendation:** Use DeepFilterNet3 for noise cancellation with RNNoise CPU fallback, Pedalboard for all audio effects (pitch shift, reverb, compression, EQ), MediaPipe for face tracking and background segmentation, and OpenCV for video filters. Integrate via aiortc's MediaStreamTrack custom track pattern.

## Standard Stack

The established libraries for real-time audio/video effects in Python (2026):

### Core Audio Processing

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **DeepFilterNet** | 0.5.6 | AI-based noise suppression | State-of-the-art quality (PESQ 3.5-4.0+), handles non-stationary noise, production-ready PyPI package. Used by professional audio tools. |
| **pyrnnoise** | 0.4.3 | Lightweight noise cancellation | Ultra-low latency (10-20ms), minimal CPU usage, perfect for CPU-only fallback. Mozilla's proven RNN implementation. |
| **Pedalboard** | 0.9.21 | Audio effects (DSP) | Spotify's production library. Built-in pitch shift, reverb, compressor, EQ, de-esser. Real-time streaming via AudioStream. VST3 plugin support. |
| **sounddevice** | 0.5.5 | Audio I/O with NumPy | Industry standard for low-latency audio callbacks. NumPy integration, PortAudio wrapper, optimal for blocksize=0 adaptive buffering. |

### Core Video Processing

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **MediaPipe** | 0.10.32 | Face landmarks & segmentation | Google's production ML solution. 478 face landmarks + 52 blendshapes. Selfie segmentation <35ms latency. Runs on CPU/GPU. |
| **OpenCV** | Latest (cv2) | Video filters & processing | Universal computer vision library. LUT-based color grading, bilateral filtering for beauty effects, cartoon filters. GPU acceleration via OpenCL/CUDA. |
| **NumPy** | Latest | Array processing | Foundation for all numerical processing. Required by sounddevice, used for audio/video frame manipulation. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **psutil** | Latest | CPU/memory monitoring | Optional resource monitoring indicator (user-toggleable in settings) |
| **GPUtil** | Latest | NVIDIA GPU monitoring | Detect GPU availability, monitor GPU usage if NVIDIA hardware present |
| **pyopencl** | 2026.1.2 | OpenCL GPU acceleration | Detect OpenCL devices (AMD/Intel GPUs), fallback if CUDA unavailable |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| DeepFilterNet | noisereduce | noisereduce uses spectral gating (simpler), but DeepFilterNet has superior quality for speech |
| Pedalboard | pysndfx | pysndfx is lighter but requires SoX installation, Pedalboard is self-contained |
| MediaPipe Selfie Segmentation | Custom U-Net model | Custom models require training data and maintenance, MediaPipe is production-ready |
| sounddevice | PyAudio | PyAudio is lower-level, sounddevice has better NumPy integration and simpler API |

**Installation:**

```bash
# Audio processing
pip install deepfilternet==0.5.6 pyrnnoise==0.4.3 pedalboard==0.9.21
pip install sounddevice==0.5.5 numpy

# Video processing
pip install mediapipe==0.10.32 opencv-python

# Optional: GPU/monitoring
pip install psutil GPUtil pyopencl

# Note: DeepFilterNet also requires PyTorch
pip install torch torchaudio  # Use appropriate CUDA version or CPU-only
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── audio/
│   ├── effects/
│   │   ├── noise_cancellation.py    # DeepFilterNet3 + RNNoise fallback
│   │   ├── voice_effects.py         # Pitch shift, voice changer (Pedalboard)
│   │   ├── enhancement.py           # Compression, EQ, de-esser (Pedalboard)
│   │   └── effect_chain.py          # Chain multiple effects together
│   ├── processors/
│   │   ├── audio_track.py           # Custom aiortc MediaStreamTrack for audio
│   │   └── stream_processor.py      # Real-time audio processing callback
│   └── presets/
│       └── preset_manager.py        # Save/load user effect presets (JSON)
├── video/
│   ├── effects/
│   │   ├── background.py            # Virtual backgrounds (MediaPipe segmentation)
│   │   ├── beauty_filters.py        # Skin smoothing, lighting (OpenCV bilateral)
│   │   ├── creative_filters.py      # Vintage, cartoon, color effects (OpenCV LUT)
│   │   └── ar_overlays.py           # Face filters, masks (MediaPipe landmarks)
│   ├── processors/
│   │   ├── video_track.py           # Custom aiortc MediaStreamTrack for video
│   │   ├── face_tracker.py          # MediaPipe Face Landmarker wrapper
│   │   └── segmentation.py          # MediaPipe Selfie Segmenter wrapper
│   └── presets/
│       └── preset_manager.py        # Save/load video effect presets (JSON)
├── hardware/
│   ├── gpu_detector.py              # Detect CUDA/OpenCL/CPU capabilities
│   ├── quality_adapter.py           # Auto-select quality based on hardware
│   └── resource_monitor.py          # CPU/GPU usage tracking (optional)
└── ui/
    ├── effects_panel.py             # Full effects control panel
    ├── quick_toggle_bar.py          # Favorite effects quick access
    └── preset_selector.py           # User preset dropdown
```

### Pattern 1: Custom aiortc MediaStreamTrack with Effects Pipeline

**What:** Extend aiortc's MediaStreamTrack to insert audio/video processing between capture and transmission

**When to use:** Always — this is the standard pattern for adding effects to WebRTC streams in aiortc

**Example:**

```python
# Source: aiortc documentation + WebRTC best practices
from aiortc import MediaStreamTrack
from av import VideoFrame, AudioFrame
import numpy as np

class AudioEffectsTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track, effect_chain):
        super().__init__()
        self.track = track
        self.effect_chain = effect_chain  # List of audio effects

    async def recv(self):
        frame = await self.track.recv()

        # Convert to NumPy for processing
        audio_data = frame.to_ndarray()

        # Apply effects chain
        for effect in self.effect_chain:
            audio_data = effect.process(audio_data, frame.sample_rate)

        # Convert back to AudioFrame
        new_frame = AudioFrame.from_ndarray(
            audio_data,
            format=frame.format.name,
            layout=frame.layout.name
        )
        new_frame.sample_rate = frame.sample_rate
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame

class VideoEffectsTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track, effect_pipeline):
        super().__init__()
        self.track = track
        self.effect_pipeline = effect_pipeline

    async def recv(self):
        frame = await self.track.recv()

        # Convert to NumPy/OpenCV format
        img = frame.to_ndarray(format="bgr24")

        # Apply video effects
        processed_img = await self.effect_pipeline.process(img)

        # Convert back to VideoFrame
        new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame
```

### Pattern 2: Hardware-Adaptive Processing with GPU Fallback

**What:** Auto-detect GPU capabilities and select appropriate processing path (CUDA > OpenCL > CPU)

**When to use:** Always — ensures maximum performance while maintaining compatibility

**Example:**

```python
# Source: PyTorch CUDA detection + OpenCV GPU module patterns
import torch
import cv2

class HardwareDetector:
    def __init__(self):
        self.has_cuda = torch.cuda.is_available()
        self.has_opencl = cv2.ocl.haveOpenCL()
        self.device = self._select_device()

    def _select_device(self):
        if self.has_cuda:
            return "cuda"
        elif self.has_opencl:
            cv2.ocl.setUseOpenCL(True)
            return "opencl"
        else:
            return "cpu"

    def get_quality_preset(self):
        """Auto-select quality based on hardware"""
        if self.has_cuda:
            return "ultra"  # DeepFilterNet3, high-res segmentation
        elif self.has_opencl:
            return "high"   # RNNoise, medium-res segmentation
        else:
            return "medium" # RNNoise only, low-res segmentation

class NoiseReducer:
    def __init__(self, hardware_detector):
        self.hw = hardware_detector

        if self.hw.device in ["cuda", "opencl"]:
            # Use DeepFilterNet3 for GPU
            from df import enhance, init_df
            self.model, self.df_state, _ = init_df()
            self.method = "deepfilter"
        else:
            # Use RNNoise for CPU
            import rnnoise
            self.denoiser = rnnoise.RNNoise()
            self.method = "rnnoise"

    def process(self, audio_chunk, sample_rate):
        if self.method == "deepfilter":
            # DeepFilterNet processing
            enhanced = enhance(self.model, self.df_state, audio_chunk)
            return enhanced
        else:
            # RNNoise processing (ultra-low latency)
            return self.denoiser.process(audio_chunk)
```

### Pattern 3: Effect Chain with Correct Signal Order

**What:** Chain audio effects in optimal order to avoid artifacts and maximize quality

**When to use:** Always — incorrect order causes harsh sibilance, pumping compression, or muddy EQ

**Example:**

```python
# Source: Professional audio engineering best practices
# Order: Gate → De-esser → Corrective EQ → Compressor → Creative EQ → Effects (reverb/delay)

from pedalboard import (
    Pedalboard, NoiseGate, Compressor,
    HighpassFilter, LowShelfFilter, Reverb, PitchShift
)

class VoiceEffectChain:
    def __init__(self, preset="default"):
        self.preset = preset
        self.board = self._build_chain()

    def _build_chain(self):
        if self.preset == "professional_voice":
            # Full professional voice processing chain
            return Pedalboard([
                NoiseGate(threshold_db=-40, ratio=4),         # Remove background noise
                # De-esser (use compressor on 4-8kHz band)
                HighpassFilter(cutoff_frequency_hz=80),       # Remove rumble
                Compressor(threshold_db=-20, ratio=3),        # Even out levels
                LowShelfFilter(cutoff_frequency_hz=200, gain_db=-3),  # Reduce muddiness
                # Creative effects come last
            ])

        elif self.preset == "robot":
            return Pedalboard([
                PitchShift(semitones=-5),                     # Lower pitch
                # Add ring modulation or vocoder here
            ])

        elif self.preset == "helium":
            return Pedalboard([
                PitchShift(semitones=7),                      # Raise pitch significantly
            ])

        return Pedalboard([])  # No effects

    def process(self, audio_chunk, sample_rate):
        return self.board(audio_chunk, sample_rate)
```

### Pattern 4: Real-Time Video Processing with Threading

**What:** Use threading to decouple video capture from processing to maintain high FPS

**When to use:** Always for real-time video — blocking I/O in main thread kills frame rate

**Example:**

```python
# Source: PyImageSearch threading optimization patterns
import cv2
import threading
import queue

class ThreadedVideoProcessor:
    def __init__(self, effect_pipeline):
        self.effect_pipeline = effect_pipeline
        self.frame_queue = queue.Queue(maxsize=2)  # Small buffer to reduce latency
        self.processed_queue = queue.Queue(maxsize=2)
        self.stopped = False

        # Start processing thread
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()

    def _process_loop(self):
        while not self.stopped:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()

                # Apply effects (can be slow)
                processed = self.effect_pipeline.process(frame)

                # Put in output queue
                if not self.processed_queue.full():
                    self.processed_queue.put(processed)

    def process_frame(self, frame):
        """Non-blocking: queues frame for processing"""
        if not self.frame_queue.full():
            self.frame_queue.put(frame)

    def get_processed_frame(self):
        """Non-blocking: returns latest processed frame or None"""
        if not self.processed_queue.empty():
            return self.processed_queue.get()
        return None

    def stop(self):
        self.stopped = True
        self.thread.join()
```

### Pattern 5: MediaPipe Face Landmarks for AR Overlays

**What:** Use MediaPipe's 478 face landmarks to anchor virtual objects (glasses, hats, masks)

**When to use:** For all AR face filter effects (Snapchat/Instagram style)

**Example:**

```python
# Source: MediaPipe official documentation
import mediapipe as mp
import cv2

class ARFaceFilter:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,  # Get iris landmarks too
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def apply_glasses(self, image, glasses_img):
        """Apply virtual glasses using face landmarks"""
        results = self.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return image  # No face detected

        landmarks = results.multi_face_landmarks[0]
        h, w, _ = image.shape

        # Key landmarks for glasses positioning
        # Left eye: landmark 33, Right eye: landmark 263
        left_eye = landmarks.landmark[33]
        right_eye = landmarks.landmark[263]

        # Calculate glasses position and size
        left_x, left_y = int(left_eye.x * w), int(left_eye.y * h)
        right_x, right_y = int(right_eye.x * w), int(right_eye.y * h)

        eye_distance = ((right_x - left_x)**2 + (right_y - left_y)**2)**0.5
        glasses_width = int(eye_distance * 2.5)

        # Resize and overlay glasses
        glasses_resized = cv2.resize(glasses_img, (glasses_width, glasses_width // 2))

        # Calculate center position
        center_x = (left_x + right_x) // 2
        center_y = (left_y + right_y) // 2

        # Overlay with alpha blending
        overlay = image.copy()
        y_offset = center_y - glasses_resized.shape[0] // 2
        x_offset = center_x - glasses_resized.shape[1] // 2

        # Alpha blend the glasses
        # (simplified - real implementation handles alpha channel)
        image[y_offset:y_offset+glasses_resized.shape[0],
              x_offset:x_offset+glasses_resized.shape[1]] = glasses_resized

        return image
```

### Anti-Patterns to Avoid

- **Blocking video I/O in main thread:** Always use threading or async processing to avoid FPS drops
- **Applying compression before de-essing:** De-esser must come first, or compression amplifies sibilance
- **Large audio buffer sizes for low latency:** Use `blocksize=0` (adaptive) in sounddevice for optimal latency
- **Processing every video frame:** If processing is slow, skip frames rather than dropping FPS
- **Not handling MediaPipe "no face detected":** Always check if landmarks exist before accessing them
- **Storing effects as class state without presets:** Users expect to save/load effect combinations
- **GPU-only code paths:** Always provide CPU fallback — many users don't have CUDA GPUs
- **Synchronous processing in aiortc recv():** Keep processing fast or use frame buffering

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Audio pitch shifting | FFT-based pitch shifter | Pedalboard.PitchShift (uses Rubber Band Library) | Rubber Band is state-of-the-art, avoids phase artifacts and formant issues |
| Noise cancellation | Spectral gating | DeepFilterNet3 or RNNoise | AI models handle non-stationary noise (keyboard typing, fans) far better |
| Face detection | Custom Haar cascades | MediaPipe Face Mesh | MediaPipe runs 10x faster and provides 478 landmarks vs 68 from dlib |
| Background segmentation | Threshold-based matting | MediaPipe Selfie Segmentation | Deep learning handles hair, transparency, and motion blur correctly |
| Audio compressor | Manual gain reduction | Pedalboard.Compressor | Professional compressors have attack/release envelopes, lookahead, sidechain |
| De-esser | Fixed frequency notch filter | Pedalboard multi-band compressor | Sibilance frequency varies per voice, needs dynamic processing |
| Reverb | Delay-based "echo" | Pedalboard.Reverb or Convolution | Real reverb requires complex reflection modeling |
| LUT color grading | Manual RGB adjustment | OpenCV cv2.LUT with .cube files | Industry-standard 3D LUTs handle complex color transforms |

**Key insight:** Real-time audio/video processing has decades of research and production-tested libraries. Custom implementations will be slower, lower quality, and harder to maintain. Use Pedalboard/MediaPipe/OpenCV and focus on integration, not reinventing algorithms.

## Common Pitfalls

### Pitfall 1: Latency Accumulation (Audio)

**What goes wrong:** Adding multiple audio effects creates cumulative latency that makes conversation feel laggy

**Why it happens:** Each effect adds processing time. DeepFilterNet (~50ms) + Pedalboard effects (~20ms) + network (~50ms) = 120ms total, which starts to feel delayed

**How to avoid:**
- Use `blocksize=0` in sounddevice for adaptive buffering (reduces latency by 30-50%)
- Switch to RNNoise (10-20ms) on low-power mode or high-latency connections
- Apply effects in a single pass through Pedalboard chain rather than multiple passes
- Monitor total latency and disable effects if it exceeds 150ms (noticeable delay threshold)

**Warning signs:**
- Users report "talking over each other" more than usual
- Echo/feedback issues during calls
- Audio processing callback takes >30ms (check with profiling)

### Pitfall 2: Face Tracking Loss During Fast Motion

**What goes wrong:** AR overlays (glasses, masks) jump around or disappear when user moves head quickly

**Why it happens:** MediaPipe's tracking can lag or lose faces during rapid motion, causing landmarks to update slowly or fail

**How to avoid:**
- Set `min_tracking_confidence=0.5` (lower) to maintain tracking during motion
- Use `refine_landmarks=False` if extra precision isn't needed (faster processing)
- Implement temporal smoothing: blend current landmarks with previous 2-3 frames to reduce jitter
- Add "last known good" fallback: if tracking fails, keep using previous frame's landmarks for 3-5 frames

**Warning signs:**
- Glasses/masks "float" away from face during head turns
- AR overlays flicker on/off rapidly
- Landmarks jump discontinuously between frames

### Pitfall 3: GPU Memory Exhaustion with Multiple Models

**What goes wrong:** Loading DeepFilterNet + MediaPipe models simultaneously causes out-of-memory errors on lower-end GPUs

**Why it happens:** DeepFilterNet (PyTorch) + MediaPipe (TFLite) both allocate VRAM. On 4GB GPUs, this can exceed available memory

**How to avoid:**
- Use `torch.cuda.set_per_process_memory_fraction(0.5)` to limit PyTorch VRAM usage
- Load models lazily — only load when user enables that effect category
- Offer "Low VRAM Mode" that uses RNNoise (CPU) instead of DeepFilterNet
- Monitor GPU memory with GPUtil and warn user if usage exceeds 90%

**Warning signs:**
- CUDA out-of-memory errors when enabling multiple effect categories
- System becomes unresponsive when video effects are enabled
- GPU memory usage climbs above 3.5GB on a 4GB card

### Pitfall 4: Color Space Mismatches (Video)

**What goes wrong:** Video appears with wrong colors (greenish skin tones, oversaturated) after processing

**Why it happens:** aiortc uses YUV/I420, MediaPipe expects RGB, OpenCV uses BGR by default. Forgetting conversions causes color corruption

**How to avoid:**
- Always convert to RGB before MediaPipe: `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`
- Convert back to BGR for OpenCV operations: `cv2.cvtColor(result, cv2.COLOR_RGB2BGR)`
- Use `VideoFrame.to_ndarray(format="bgr24")` for aiortc frame extraction
- Test with color checker image to verify color fidelity

**Warning signs:**
- Skin tones look green or purple
- Colors are overly saturated or desaturated
- Video looks correct in local preview but wrong in received stream

### Pitfall 5: Effect Order Causes Audio Artifacts

**What goes wrong:** Compression creates pumping/breathing, EQ sounds harsh, sibilance is overwhelming

**Why it happens:** Applying compression before de-essing amplifies "s" sounds. EQ before compression triggers compressor on unwanted frequencies

**How to avoid:**
- Follow professional chain order: Gate → De-esser → Corrective EQ → Compressor → Creative EQ → Effects
- De-esser MUST come before main compressor
- High-pass filter (remove low rumble) before compression to avoid triggering on non-voice frequencies
- Creative effects (reverb, delay) always come last

**Warning signs:**
- Sibilance (harsh "s" sounds) is louder than speech
- Compressor "pumps" (volume breathes up and down)
- Voice sounds hollow or thin after EQ

### Pitfall 6: Preset Management Without Validation

**What goes wrong:** Loading a saved preset crashes the app or applies incompatible settings

**Why it happens:** User saves preset on GPU system with DeepFilterNet, loads on CPU-only system where it's unavailable

**How to avoid:**
- Store hardware requirements in preset metadata: `{"requires_gpu": true, "min_vram_mb": 2048}`
- Validate preset compatibility before loading: check if required effects/models are available
- Provide graceful degradation: substitute RNNoise if DeepFilterNet unavailable
- Version presets: `{"preset_version": "1.0"}` to handle future format changes

**Warning signs:**
- App crashes when loading presets from other users
- Effects don't apply but no error message
- Preset loads but performance is terrible (quality mismatch)

## Code Examples

Verified patterns from official sources:

### Real-Time Audio Processing with sounddevice

```python
# Source: sounddevice official documentation
import sounddevice as sd
import numpy as np

class RealtimeAudioProcessor:
    def __init__(self, effect_chain, sample_rate=48000):
        self.effect_chain = effect_chain
        self.sample_rate = sample_rate
        self.stream = None

    def start(self):
        """Start real-time processing stream"""
        self.stream = sd.Stream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=0,  # Adaptive block size for minimal latency
            callback=self.audio_callback
        )
        self.stream.start()

    def audio_callback(self, indata, outdata, frames, time, status):
        """Process audio in real-time (runs in separate thread)"""
        if status:
            print(f"Audio callback status: {status}")

        # Apply effects chain
        processed = self.effect_chain.process(indata[:, 0], self.sample_rate)

        # Write to output
        outdata[:, 0] = processed

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
```

### MediaPipe Background Blur/Replacement

```python
# Source: MediaPipe Selfie Segmentation documentation
import mediapipe as mp
import cv2
import numpy as np

class VirtualBackground:
    def __init__(self, mode="blur", background_image=None):
        self.mode = mode
        self.background_image = background_image

        self.mp_selfie_segmentation = mp.solutions.mediapipe.python.solutions.selfie_segmentation
        self.segmenter = self.mp_selfie_segmentation.SelfieSegmentation(
            model_selection=1  # 0=general (256x256), 1=landscape (144x256)
        )

    def process_frame(self, frame):
        """Apply background blur or replacement"""
        # Process with MediaPipe
        results = self.segmenter.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Get segmentation mask
        mask = results.segmentation_mask

        # Threshold mask (person = 1, background = 0)
        condition = mask > 0.5

        if self.mode == "blur":
            # Blur background
            blurred = cv2.GaussianBlur(frame, (55, 55), 0)
            output = np.where(condition[..., None], frame, blurred)

        elif self.mode == "replace" and self.background_image is not None:
            # Replace with custom background
            bg = cv2.resize(self.background_image, (frame.shape[1], frame.shape[0]))
            output = np.where(condition[..., None], frame, bg)

        else:
            output = frame

        return output.astype(np.uint8)
```

### Beauty Filter with OpenCV Bilateral Filter

```python
# Source: OpenCV beauty filter tutorials (Medium, LearnOpenCV)
import cv2
import numpy as np

class BeautyFilter:
    def __init__(self, intensity=50):
        """
        intensity: 0-100, controls strength of skin smoothing
        """
        self.intensity = np.clip(intensity, 0, 100) / 100.0

    def smooth_skin(self, frame):
        """Apply skin smoothing beauty filter"""
        # Convert to LAB color space (better for skin tones)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply bilateral filter to L channel (preserves edges)
        # Bilateral filter parameters scale with intensity
        d = int(9 * self.intensity)  # Diameter (0-9)
        sigma_color = int(75 * self.intensity)  # Color similarity
        sigma_space = int(75 * self.intensity)  # Spatial distance

        l_smooth = cv2.bilateralFilter(l, d, sigma_color, sigma_space)

        # Blend original and smoothed based on intensity
        l_blended = cv2.addWeighted(l, 1 - self.intensity, l_smooth, self.intensity, 0)

        # Merge back and convert to BGR
        lab_smooth = cv2.merge([l_blended, a, b])
        result = cv2.cvtColor(lab_smooth, cv2.COLOR_LAB2BGR)

        return result

    def enhance_lighting(self, frame):
        """Subtle lighting correction for better appearance"""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to V channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        v_enhanced = clahe.apply(v)

        # Merge and convert back
        hsv_enhanced = cv2.merge([h, s, v_enhanced])
        result = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)

        return result

    def apply(self, frame):
        """Apply full beauty filter"""
        frame = self.smooth_skin(frame)
        frame = self.enhance_lighting(frame)
        return frame
```

### LUT-based Color Grading (Vintage/Creative Filters)

```python
# Source: OpenCV LUT documentation and color grading tutorials
import cv2
import numpy as np

class ColorGrading:
    @staticmethod
    def load_lut_from_cube(cube_file_path):
        """Load 3D LUT from .cube file (industry standard)"""
        # Simplified - real implementation parses .cube format
        # Returns 3D LUT array (e.g., 64x64x64x3)
        pass

    @staticmethod
    def create_vintage_lut():
        """Create vintage/sepia LUT"""
        # Create lookup table for sepia effect
        lut = np.zeros((256, 1, 3), dtype=np.uint8)

        for i in range(256):
            # Sepia transformation matrix
            lut[i, 0, 0] = min(255, int(i * 0.272 + 255 * 0.534 + 255 * 0.131))  # B
            lut[i, 0, 1] = min(255, int(i * 0.349 + 255 * 0.686 + 255 * 0.168))  # G
            lut[i, 0, 2] = min(255, int(i * 0.393 + 255 * 0.769 + 255 * 0.189))  # R

        return lut

    @staticmethod
    def create_warm_lut():
        """Warming filter (increase red, decrease blue)"""
        lut = np.arange(256, dtype=np.uint8).reshape(256, 1, 3)
        lut = np.repeat(lut, 3, axis=2)

        # Increase red channel
        lut[:, :, 2] = np.clip(lut[:, :, 2] * 1.15, 0, 255).astype(np.uint8)
        # Decrease blue channel
        lut[:, :, 0] = np.clip(lut[:, :, 0] * 0.85, 0, 255).astype(np.uint8)

        return lut

    @staticmethod
    def apply_lut(frame, lut):
        """Apply LUT to frame"""
        return cv2.LUT(frame, lut)
```

### Preset Save/Load with JSON

```python
# Source: Standard Python JSON patterns + EasyEffects preset format
import json
from pathlib import Path

class EffectPresetManager:
    def __init__(self, presets_dir="~/.discordopus/presets"):
        self.presets_dir = Path(presets_dir).expanduser()
        self.presets_dir.mkdir(parents=True, exist_ok=True)

    def save_preset(self, name, audio_effects, video_effects, hardware_reqs=None):
        """Save effect preset to JSON"""
        preset = {
            "version": "1.0",
            "name": name,
            "audio": {
                "noise_cancellation": audio_effects.get("noise_cancel", "none"),
                "voice_effects": audio_effects.get("voice_effects", []),
                "enhancement": audio_effects.get("enhancement", {}),
            },
            "video": {
                "background": video_effects.get("background", "none"),
                "beauty_filter": video_effects.get("beauty", 0),
                "creative_filter": video_effects.get("creative", "none"),
                "ar_overlay": video_effects.get("ar", "none"),
            },
            "hardware": hardware_reqs or {"requires_gpu": False, "min_vram_mb": 0}
        }

        preset_file = self.presets_dir / f"{name}.json"
        with open(preset_file, "w") as f:
            json.dump(preset, f, indent=2)

        return preset_file

    def load_preset(self, name, hardware_detector):
        """Load preset with hardware validation"""
        preset_file = self.presets_dir / f"{name}.json"

        if not preset_file.exists():
            raise FileNotFoundError(f"Preset '{name}' not found")

        with open(preset_file) as f:
            preset = json.load(f)

        # Validate hardware requirements
        hw_reqs = preset.get("hardware", {})
        if hw_reqs.get("requires_gpu") and hardware_detector.device == "cpu":
            # Provide fallback or warn user
            print(f"Warning: Preset '{name}' requires GPU, substituting CPU alternatives")
            preset = self._substitute_cpu_alternatives(preset)

        return preset

    def _substitute_cpu_alternatives(self, preset):
        """Replace GPU effects with CPU alternatives"""
        # Substitute DeepFilterNet with RNNoise
        if preset["audio"]["noise_cancellation"] == "deepfilternet":
            preset["audio"]["noise_cancellation"] = "rnnoise"

        # Reduce video processing quality
        if preset["video"]["background"] in ["replace", "virtual_room"]:
            preset["video"]["background"] = "blur"  # Simpler processing

        return preset

    def list_presets(self):
        """List all available presets"""
        return [p.stem for p in self.presets_dir.glob("*.json")]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Spectral gating noise reduction | AI-based (DeepFilterNet3, RNNoise) | 2020-2022 | 2-3x better quality on non-stationary noise (typing, fans) |
| Custom U-Net segmentation models | MediaPipe Selfie Segmentation | 2021 | Pre-trained production model, 10x faster, no training needed |
| dlib 68-point face landmarks | MediaPipe 478-point face mesh | 2020 | 7x more detail, enables realistic AR overlays |
| FFT pitch shift | Rubber Band Library (via Pedalboard) | Industry standard since 2010 | Formant preservation, no "chipmunk" artifacts |
| Manual audio effect chains | Pedalboard (Spotify) | Released 2021, matured 2023-2026 | Professional VST3-quality effects, real-time streaming |
| PyAudio for audio I/O | sounddevice with NumPy | Preferred since 2018 | Better NumPy integration, simpler API |

**Deprecated/outdated:**
- **noisereduce (spectral gating):** Still maintained but DeepFilterNet/RNNoise provide superior speech quality
- **dlib face landmarks:** Slower and less detailed than MediaPipe Face Mesh
- **librosa for real-time:** Not designed for real-time, use Pedalboard instead (librosa is for analysis)
- **PyAudio:** Still works but sounddevice is now preferred for new projects

## Open Questions

Things that couldn't be fully resolved:

1. **DeepFilterNet PyTorch dependency size**
   - What we know: DeepFilterNet requires PyTorch (~800MB), significantly increasing package size
   - What's unclear: Whether PyTorch Lite or ONNX export could reduce size while maintaining quality
   - Recommendation: Start with full PyTorch, investigate ONNX export if package size becomes critical (>2GB total)

2. **MediaPipe model updates**
   - What we know: MediaPipe 0.10.32 is latest (Jan 2026), uses older face mesh models
   - What's unclear: Google's roadmap for model updates or newer alternatives
   - Recommendation: Use current MediaPipe, monitor for announcements of improved models

3. **Voice effect quality on recorded messages**
   - What we know: Voice effects work on live calls AND recordings (per requirements)
   - What's unclear: Whether to apply effects during recording or playback (UX decision)
   - Recommendation: Apply during playback (non-destructive), store original + effect metadata

4. **Screen sharing overlay performance**
   - What we know: Basic overlays (watermark, border, cursor highlight) are required
   - What's unclear: Performance impact on high-resolution screen sharing (1440p/4K)
   - Recommendation: Test at 1080p first, add quality degradation for higher resolutions if needed

5. **Effect persistence across app restarts**
   - What we know: Effects persist until user changes them (per requirements)
   - What's unclear: Whether to persist to disk or keep in memory (session-only)
   - Recommendation: Persist to local settings file, load on startup for seamless UX

## Sources

### Primary (HIGH confidence)

- [DeepFilterNet on PyPI](https://pypi.org/project/deepfilternet/) - Version 0.5.6, installation requirements
- [pyrnnoise on PyPI](https://pypi.org/project/pyrnnoise/) - Version 0.4.3, actively maintained (Jan 2026)
- [Pedalboard on PyPI](https://pypi.org/project/pedalboard/) - Version 0.9.21 (Jan 2026), Python 3.10-3.14
- [MediaPipe on PyPI](https://pypi.org/project/mediapipe/) - Version 0.10.32 (Jan 2026)
- [MediaPipe Face Landmarker Guide](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker) - 478 landmarks, performance specs
- [MediaPipe Image Segmenter](https://ai.google.dev/edge/mediapipe/solutions/vision/image_segmenter) - <35ms latency on Pixel 6
- [sounddevice documentation](https://python-sounddevice.readthedocs.io/) - Version 0.5.5 (Jan 2026)
- [aiortc on PyPI](https://pypi.org/project/aiortc/) - WebRTC integration patterns

### Secondary (MEDIUM confidence)

- [DeepFilterNet vs RNNoise comparison](https://noisereducerai.com/deepfilternet-ai-noise-reduction/) - Quality metrics (PESQ 3.5-4.0+ vs 3.88)
- [Performance of speech enhancement models (ResearchGate)](https://www.researchgate.net/publication/392780104_Performance_of_speech_enhancement_models_in_video_conferences_DeepFilterNet3_and_RNNoise) - Latency comparison
- [Faster video FPS with threading (PyImageSearch)](https://pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/) - 379% FPS increase with threading
- [Creating beauty filters (Medium)](https://medium.com/swlh/how-i-implemented-my-own-augmented-reality-beauty-mode-3bf3b74e5507) - Bilateral filtering, frequency separation
- [Audio effect chain order (iZotope)](https://www.izotope.com/en/learn/signal-chain-order-of-operations.html) - Professional audio engineering best practices
- [OpenCV LUT filters (DEV Community)](https://dev.to/ethand91/creating-various-filters-with-opencvpython-3077) - LUT-based color grading
- [PSOLA pitch shifting (Cornell)](https://courses.ece.cornell.edu/ece5990/ECE5725_Fall2023_Projects/2%20Wednesday%20December%206/4%20Voice%20Changer/W_wf223_kx74/index.html) - Real-time voice effects
- [GPU acceleration in Python (NVIDIA)](https://developer.nvidia.com/how-to-cuda-python) - CUDA detection patterns
- [Real-time performance monitoring (GitHub: nvitop)](https://github.com/XuehaiPan/nvitop) - GPU usage tracking

### Tertiary (LOW confidence - verify during implementation)

- [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) - WebRTC pitfalls (threading, STUN/TURN)
- [VidGear adaptive streaming](https://github.com/abhiTronix/vidgear) - Adaptive quality patterns
- [EasyEffects presets](https://github.com/Digitalone1/EasyEffects-Presets) - JSON preset format examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified from PyPI with recent 2026 releases
- Architecture: HIGH - Patterns from official docs (aiortc, MediaPipe, sounddevice)
- Pitfalls: MEDIUM-HIGH - Based on WebRTC integration challenges and audio engineering best practices
- Code examples: HIGH - Sourced from official documentation and verified tutorials

**Research date:** 2026-02-02
**Valid until:** 2026-04-02 (60 days - stable domain with mature libraries)
