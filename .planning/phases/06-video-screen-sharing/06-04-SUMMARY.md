---
phase: 06-video-screen-sharing
plan: 04
subsystem: video-ui
tags: [video, settings, ui, zustand, react]
completed: 2026-01-31
duration: 5m

requires:
  - 06-02: Video track management methods
  - 06-03: Video API bridge and TypeScript types

provides:
  - VideoSection: Camera selection in settings
  - ScreenPicker: Monitor selection dialog for screen sharing
  - Call store video state: videoEnabled, videoSource, remoteVideo tracking

affects:
  - 06-05: Video display will use video state from call store
  - 06-06: Integration will connect ScreenPicker to call UI

tech-stack:
  added: []
  patterns:
    - Event-driven video state synchronization
    - Modal dialog pattern for screen picker

key-files:
  created:
    - frontend/src/components/settings/VideoSection.tsx
    - frontend/src/components/call/ScreenPicker.tsx
  modified:
    - frontend/src/stores/call.ts
    - frontend/src/components/settings/SettingsPanel.tsx
    - frontend/src/components/settings/AudioSection.tsx

decisions:
  - name: Video state in call store
    rationale: Single source of truth for video-related state during calls
    impact: Enables reactive UI updates when video state changes
---

# Phase 06 Plan 04: Video Settings UI Summary

**One-liner:** Camera selection dropdown, screen picker modal, and call store video state management with event-driven updates.

## What Was Built

### 1. Call Store Video State Extension
Extended the Zustand call store with comprehensive video state tracking:
- `videoEnabled`: Whether local video is active
- `videoSource`: Current source ('camera' | 'screen' | null)
- `remoteVideo`: Whether remote party has video enabled
- `selectedCamera`: Currently selected camera device index
- `selectedMonitor`: Currently selected monitor for screen sharing (defaults to 1)

Added video actions:
- `enableVideo(source)`: Enable camera or screen sharing via API
- `disableVideo()`: Disable video via API
- `setVideoEnabled()`, `setRemoteVideo()`: State setters for event listeners
- `setSelectedCamera()`, `setSelectedMonitor()`: Device selection setters

Added event listeners:
- `discordopus:video_state`: Updates local video state
- `discordopus:remote_video_changed`: Updates remote video state

### 2. VideoSection Settings Component
Created camera selection UI matching AudioSection styling:
- Dropdown listing available cameras by name
- Loading state while fetching devices
- "No cameras detected" message when empty
- Calls `api.set_camera()` on selection change
- Inline SVG camera icon

### 3. ScreenPicker Dialog Component
Created modal dialog for monitor selection:
- Dark backdrop with blur effect
- Grid of monitor cards showing:
  - Monitor number with "Primary" label for monitor 1
  - Resolution (width x height)
  - Position coordinates for multi-monitor setups
- Selected state with highlight border and checkmark
- ESC key and backdrop click to close
- Filters out monitor 0 (all screens combined)
- Calls `api.set_screen_monitor()` on selection

### 4. SettingsPanel Integration
Added VideoSection to SettingsPanel after AudioSection for logical grouping of media device settings.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed TypeScript errors in AudioSection.tsx**
- **Found during:** Task 4 verification (npm run build)
- **Issue:** Pre-existing TypeScript errors preventing build - array element access without null checks
- **Fix:** Added explicit null checks for first element access: `const firstInput = result.inputs[0]; if (firstInput) { ... }`
- **Files modified:** frontend/src/components/settings/AudioSection.tsx
- **Commit:** 4b75d20

## Technical Details

### File Structure
```
frontend/src/
  stores/
    call.ts                    # Extended with video state
  components/
    settings/
      VideoSection.tsx         # New: Camera selection
      SettingsPanel.tsx        # Modified: Added VideoSection
      AudioSection.tsx         # Fixed: TypeScript errors
    call/
      ScreenPicker.tsx         # New: Monitor picker dialog
```

### API Methods Used
- `api.get_cameras()`: Fetch available camera devices
- `api.set_camera(index)`: Select camera by index
- `api.get_monitors()`: Fetch available monitors
- `api.set_screen_monitor(index)`: Select monitor for screen sharing
- `api.enable_video(source)`: Enable video with source
- `api.disable_video()`: Disable video

### Event Flow
```
Backend video_state event
  -> discordopus:video_state CustomEvent
  -> call store setVideoEnabled/setRemoteVideo
  -> React components re-render

User selects camera
  -> api.set_camera(index)
  -> call store setSelectedCamera(index)
  -> Backend updates track source
```

## Commits

| Hash | Description |
|------|-------------|
| f9625bd | feat(06-04): extend call store with video state |
| 758b8aa | feat(06-04): create VideoSection settings component |
| 70e87d3 | feat(06-04): create ScreenPicker dialog component |
| 4b75d20 | feat(06-04): integrate VideoSection into SettingsPanel |

## Verification

- [x] Call store has video state fields and actions
- [x] Call store listens to video events
- [x] VideoSection component renders camera dropdown
- [x] ScreenPicker component shows monitor selection
- [x] SettingsPanel includes VideoSection
- [x] Frontend builds without errors

## Next Phase Readiness

Ready for 06-05 (video display components):
- Video state tracked in call store
- Camera selection functional
- Monitor selection functional via ScreenPicker
- Events wired for state synchronization
