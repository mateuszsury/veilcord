---
phase: 09-audio-video-effects
plan: 01
subsystem: infra
tags: [hardware-detection, gpu, cuda, opencl, quality-adaptation, resource-monitoring, psutil, torch, opencv]

# Dependency graph
requires:
  - phase: 05-voice-calls
    provides: Audio infrastructure (sounddevice, Opus encoding)
  - phase: 06-video-screen-sharing
    provides: Video infrastructure (OpenCV, camera/screen capture)
provides:
  - HardwareDetector with CUDA/OpenCL/CPU detection
  - QualityAdapter with automatic preset selection
  - ResourceMonitor for CPU/GPU/memory usage tracking
  - Phase 9 dependency baseline (deepfilternet, pyrnnoise, pedalboard, mediapipe, psutil)
affects: [09-02-noise-cancellation, 09-03-voice-effects, 09-04-video-processing, 09-05-virtual-backgrounds]

# Tech tracking
tech-stack:
  added:
    - deepfilternet>=0.5.6 (AI noise suppression)
    - pyrnnoise>=0.4.3 (CPU fallback noise cancellation)
    - pedalboard>=0.9.21 (Spotify audio effects library)
    - mediapipe>=0.10.32 (Google face landmarks/segmentation)
    - psutil>=5.9.0 (CPU/GPU/memory monitoring)
  patterns:
    - Singleton pattern for hardware detection (lazy initialization)
    - Hardware-adaptive quality presets (CUDA→ULTRA, OpenCL→HIGH, CPU→MEDIUM)
    - Async resource monitoring with optional callbacks

key-files:
  created:
    - src/effects/hardware/gpu_detector.py (HardwareDetector singleton)
    - src/effects/hardware/quality_adapter.py (QualityAdapter, QualityPreset enum)
    - src/effects/hardware/resource_monitor.py (ResourceMonitor)
    - src/effects/hardware/__init__.py (package exports)
  modified:
    - requirements.txt (Phase 9 dependencies)

key-decisions:
  - "Lazy torch import in HardwareDetector to avoid slow startup"
  - "Singleton pattern for HardwareDetector to cache detection results"
  - "QualityPreset enum with 4 levels: LOW, MEDIUM, HIGH, ULTRA"
  - "Manual override support in QualityAdapter for user control"
  - "GPUtil as optional dependency (NVIDIA only)"

patterns-established:
  - "Hardware detection with graceful degradation (CUDA → OpenCL → CPU)"
  - "Quality preset auto-selection based on hardware capabilities"
  - "Async resource monitoring with enable/disable toggle"

# Metrics
duration: 4min
completed: 2026-02-02
---

# Phase 9 Plan 1: Hardware Detection & Quality Adaptation Summary

**Hardware-adaptive processing foundation with CUDA/OpenCL/CPU detection, automatic quality preset selection, and optional resource monitoring**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-02-02T04:57:28Z
- **Completed:** 2026-02-02T05:01:22Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Hardware detection correctly identifies CUDA, OpenCL, or CPU-only mode
- Quality adapter automatically selects appropriate preset (ULTRA/HIGH/MEDIUM/LOW)
- Resource monitor provides CPU/GPU/memory usage tracking for UI indicators
- All Phase 9 dependencies added to requirements.txt

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Phase 9 dependencies to requirements.txt** - `504b1fc` (chore)
2. **Task 2: Create hardware detection module** - `95119ca` (feat)
3. **Task 3: Create quality adapter and resource monitor** - `89a834d` (feat)

## Files Created/Modified

- `requirements.txt` - Added deepfilternet, pyrnnoise, pedalboard, mediapipe, psutil
- `src/effects/__init__.py` - Effects package marker (already existed)
- `src/effects/hardware/__init__.py` - Hardware module exports
- `src/effects/hardware/gpu_detector.py` - HardwareDetector singleton with CUDA/OpenCL/CPU detection
- `src/effects/hardware/quality_adapter.py` - QualityAdapter with QualityPreset enum and auto-selection
- `src/effects/hardware/resource_monitor.py` - ResourceMonitor with async monitoring support

## Decisions Made

**Lazy torch import in HardwareDetector**
- Rationale: torch is large and slow to import; lazy loading avoids delaying app startup
- Implementation: torch imported only in `_detect_hardware()` when detector first initialized

**Singleton pattern for HardwareDetector**
- Rationale: Hardware capabilities don't change during app runtime, cache results
- Implementation: `__new__` returns single instance, `_initialized` flag prevents re-detection

**QualityPreset mapping**
- CUDA → ULTRA (DeepFilterNet3, 1080p video, high-res segmentation)
- OpenCL → HIGH (DeepFilterNet3, 720p video, medium-res segmentation)
- CPU → MEDIUM (RNNoise, 480p video, low-res segmentation)
- LOW preset available for manual override on constrained systems

**GPUtil as optional dependency**
- Rationale: Only works with NVIDIA GPUs, not all users have NVIDIA
- Implementation: ImportError handled gracefully, `get_gpu_usage()` returns None if unavailable

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all components implemented and verified successfully.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for next plans:**
- 09-02: Noise cancellation (can use HardwareDetector + QualityAdapter to select DeepFilterNet3 vs RNNoise)
- 09-03: Voice effects (can use QualityAdapter for intensity/quality balance)
- 09-04+: Video processing (can use hardware detection for GPU-accelerated filters)

**Pattern established:**
All effects modules should use `QualityAdapter.get_active_preset()` to select algorithms and parameters based on hardware capabilities.

**No blockers or concerns.**

---
*Phase: 09-audio-video-effects*
*Completed: 2026-02-02*
