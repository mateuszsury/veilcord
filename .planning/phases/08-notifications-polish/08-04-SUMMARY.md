---
phase: 08-notifications-polish
plan: 04
subsystem: ui
tags: [auto-update, tufup, react, pywebview]

# Dependency graph
requires:
  - phase: 08-02
    provides: UpdateService with tufup integration
provides:
  - Update check on app startup via background thread
  - API bridge methods for update operations
  - UpdatePrompt UI component with download/dismiss functionality
  - Frontend event handling for update_available
affects: [08-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Background thread for non-blocking update check"
    - "CustomEvent for backend-to-frontend update notification"
    - "api.call() pattern for type-safe API access"

key-files:
  created:
    - frontend/src/components/layout/UpdatePrompt.tsx
  modified:
    - src/main.py
    - src/api/bridge.py
    - frontend/src/components/layout/AppLayout.tsx
    - frontend/src/lib/pywebview.ts

key-decisions:
  - "3-second delay before update check to allow app initialization"
  - "UpdatePrompt as global component in AppLayout"
  - "Session-based dismiss (banner reappears on restart)"

patterns-established:
  - "api.call() pattern for all frontend API access (type-safe)"
  - "discordopus:* custom events for backend notifications"

# Metrics
duration: 5min
completed: 2026-01-31
---

# Phase 08 Plan 04: Update Prompt UI Summary

**Background update check on startup with UpdatePrompt banner showing version, changelog, and one-click download/install**

## Performance

- **Duration:** 5 min
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added background thread update check 3 seconds after app launch
- Created API bridge methods: get_app_version, check_for_updates, download_update, get_update_status
- Built UpdatePrompt component with version display, changelog, download button with loading state, and dismiss
- Integrated UpdatePrompt into AppLayout as global component
- Added TypeScript types for update API and events

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire UpdateService to app startup and API bridge** - `ec8b788` (feat)
2. **Task 2: Create UpdatePrompt UI component** - `0b527d0` (feat)

## Files Created/Modified

- `src/main.py` - Added background thread for update check on startup
- `src/api/bridge.py` - Added get_app_version, check_for_updates, download_update, get_update_status methods
- `frontend/src/components/layout/UpdatePrompt.tsx` - New component for update notification banner
- `frontend/src/components/layout/AppLayout.tsx` - Integrated UpdatePrompt
- `frontend/src/lib/pywebview.ts` - Added UpdateInfo, UpdateResult, UpdateStatus types and update_available event
- `frontend/src/components/settings/NotificationSection.tsx` - Fixed api.call() pattern usage (Rule 3 deviation)

## Decisions Made

- 3-second delay before update check: Allows app to fully initialize before checking updates
- UpdatePrompt in AppLayout: Global component appears regardless of active panel
- Session-based dismiss: User can dismiss banner, but it returns on next app restart if update still available
- Used api.call() pattern for all API access in UpdatePrompt (type-safe, handles pywebview undefined)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed NotificationSection.tsx api.call() pattern**
- **Found during:** Task 2 (frontend build verification)
- **Issue:** NotificationSection.tsx from 08-03 used direct window.pywebview.api calls which fail TypeScript strict mode
- **Fix:** Updated to use api.call() pattern consistent with other components
- **Files modified:** frontend/src/components/settings/NotificationSection.tsx
- **Verification:** Frontend build passes
- **Committed in:** Part of 0b527d0 (included with UpdatePrompt changes)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary fix for build to succeed. No scope creep.

## Issues Encountered

None - plan executed as written.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Update check and UI complete
- Ready for 08-05 final polish and integration verification

---
*Phase: 08-notifications-polish*
*Completed: 2026-01-31*
