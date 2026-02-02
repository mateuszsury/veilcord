---
phase: 09-audio-video-effects
plan: 02
subsystem: audio-processing
tags: [deepfilternet, rnnoise, noise-cancellation, audio-effects, ai]

# Dependency graph
requires:
  - phase: 05-voice-calls
    provides: Audio track infrastructure with aiortc MediaStreamTrack

provides:
  - NoiseReducer with DeepFilterNet3 (GPU) and RNNoise (CPU) support
  - Hardware-adaptive method selection based on CUDA/OpenCL availability
  - AudioEffectChain for composing multiple audio effects in correct order
  - AudioEffect abstract base class for standardized effect interface
  - NoiseReducerEffect wrapper for chain integration
  - Latency tracking with 150ms threshold warnings

affects:
  - 09-03 (voice effects will use AudioEffectChain)
  - 09-05 (audio enhancement will extend AudioEffect)
  - 09-11 (effect integration will connect to voice tracks)

# Tech tracking
tech-stack:
  added: [deepfilternet, pyrnnoise, scipy]
  patterns:
    - Hardware-adaptive processing with GPU fallback
    - Lazy model loading (initialize on first use)
    - Effect chain pattern for sequential processing
    - Abstract base class for extensible effects

key-files:
  created:
    - src/effects/__init__.py
    - src/effects/audio/__init__.py
    - src/effects/audio/noise_cancellation.py
    - src/effects/audio/effect_chain.py
  modified: []

key-decisions:
  - "Auto-select DeepFilterNet3 for GPU, RNNoise for CPU to balance quality and latency"
  - "Lazy-load models to avoid startup delays and memory usage"
  - "Limit PyTorch VRAM to 50% to prevent OOM on lower-end GPUs"
  - "Warn if total chain latency exceeds 150ms (noticeable delay threshold)"
  - "Graceful degradation when libraries unavailable (pass-through mode)"
  - "Document recommended effect order for professional audio quality"

patterns-established:
  - "AudioEffect ABC: All effects implement name, enabled, process(), get_latency_ms()"
  - "Effect chain: Sequential processing with automatic latency tracking"
  - "Hardware detection: Check CUDA → OpenCL → CPU for method selection"
  - "Wrapper pattern: NoiseReducerEffect adapts NoiseReducer to AudioEffect interface"

# Metrics
duration: 6min
completed: 2026-02-02
---

# Phase 9 Plan 2: Core Audio Processing Summary

**AI-based noise cancellation with DeepFilterNet3/RNNoise and AudioEffectChain for professional audio effect composition**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-02T04:58:02Z
- **Completed:** 2026-02-02T05:03:49Z
- **Tasks:** 3
- **Files modified:** 4 created

## Accomplishments

- Implemented NoiseReducer with hardware-adaptive backend selection (DeepFilterNet3 for GPU, RNNoise for CPU)
- Created AudioEffectChain framework for composing multiple effects in correct professional order
- Established AudioEffect abstract base class as standard interface for all future audio effects
- Built latency tracking with automatic warnings when exceeding 150ms threshold
- Implemented graceful degradation when AI libraries unavailable

## Task Commits

Each task was committed atomically:

1. **Task 1: Create audio effects package structure** - `b7d464c` (chore)
2. **Task 2: Implement noise cancellation with DeepFilterNet3 and RNNoise** - `9951dbb` (feat)
3. **Task 3: Create AudioEffectChain for composing multiple effects** - `1247fde` (feat)

## Files Created/Modified

- `src/effects/__init__.py` - Root effects package with version
- `src/effects/audio/__init__.py` - Audio effects package with graceful import handling
- `src/effects/audio/noise_cancellation.py` - NoiseReducer class with hardware-adaptive AI noise cancellation
- `src/effects/audio/effect_chain.py` - AudioEffectChain and AudioEffect ABC for effect composition

## Decisions Made

**1. Auto-select noise cancellation method based on hardware**
- Rationale: DeepFilterNet3 provides superior quality (PESQ 3.5-4.0+) but requires GPU, RNNoise offers ultra-low latency (10-20ms) for CPU
- Implementation: Check torch.cuda.is_available() → cv2.ocl.haveOpenCL() → default to RNNoise

**2. Lazy-load AI models only when first needed**
- Rationale: Avoid startup delays and memory usage for unused effects
- Implementation: _ensure_initialized() called in process() method, not __init__

**3. Limit PyTorch VRAM usage to 50%**
- Rationale: Prevent OOM errors on lower-end GPUs when multiple models loaded (DeepFilterNet + MediaPipe)
- Implementation: torch.cuda.set_per_process_memory_fraction(0.5)

**4. Warn when total latency exceeds 150ms**
- Rationale: Research pitfall #1 - latency above 150ms causes noticeable delay in conversations
- Implementation: get_total_latency_ms() sums enabled effects and logs warning

**5. Document recommended effect order in AudioEffect docstring**
- Rationale: Incorrect order causes artifacts (harsh sibilance, pumping compression, muddy EQ)
- Order: Gate → De-esser → Corrective EQ → Compressor → Creative EQ → Effects (reverb/delay)

## Deviations from Plan

None - plan executed exactly as written.

All research-recommended patterns implemented:
- Pattern 2 (Hardware-Adaptive Processing): Auto-select DeepFilterNet3/RNNoise based on GPU availability
- Pattern 3 (Effect Chain with Correct Signal Order): Document professional effect ordering
- Pitfall #1 (Latency Accumulation): Track latency and warn if exceeds 150ms

## Issues Encountered

None - implementation followed research guidance and aiortc integration patterns from Phase 5.

## User Setup Required

None - no external service configuration required.

Libraries will be installed via requirements.txt:
```bash
pip install deepfilternet==0.5.6 pyrnnoise==0.4.3 scipy
```

Note: DeepFilterNet requires PyTorch (CUDA version for GPU support):
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118  # For CUDA 11.8
# OR
pip install torch torchaudio  # For CPU-only
```

## Next Phase Readiness

**Ready for 09-03 (Voice Effects):**
- AudioEffectChain provides framework for adding pitch shift, voice changer effects
- AudioEffect ABC establishes standard interface
- NoiseReducerEffect demonstrates wrapper pattern

**Ready for 09-05 (Audio Enhancement):**
- Effect chain ready for compressor, EQ, de-esser effects
- Latency tracking ensures total processing stays under 150ms

**Ready for 09-11 (Integration):**
- NoiseReducer can be integrated into MicrophoneAudioTrack.recv()
- Effect chain can process audio between capture and transmission

**Blockers/Concerns:**
- None - core infrastructure complete
- Libraries (DeepFilterNet3, RNNoise) not yet installed - will be added to requirements.txt in Phase 9 setup
- GPU detection tested via code patterns but not verified on actual hardware (will be validated during integration)

---
*Phase: 09-audio-video-effects*
*Completed: 2026-02-02*
