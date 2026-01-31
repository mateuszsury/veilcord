---
phase: 08-notifications-polish
plan: 02
subsystem: updates
tags: [tufup, tuf, auto-update, cryptographic-verification, security]

# Dependency graph
requires:
  - phase: 01-cryptographic-foundation
    provides: PyInstaller packaging infrastructure for bundle detection
provides:
  - UpdateService class with check_for_updates() and download_and_install()
  - Tufup configuration (APP_NAME, CURRENT_VERSION, paths)
  - Singleton pattern via get_update_service()
  - Callback hooks for UI integration
affects: [08-03, 08-04, deployment, release]

# Tech tracking
tech-stack:
  added: [tufup>=0.10.0, tuf, bsdiff4, securesystemslib, pynacl]
  patterns: [TUF-based update verification, lazy client initialization, graceful degradation]

key-files:
  created:
    - src/updates/__init__.py
    - src/updates/service.py
    - src/updates/settings.py
  modified:
    - requirements.txt

key-decisions:
  - "Lazy tufup client initialization to avoid startup delays"
  - "Graceful degradation when root.json missing (development mode)"
  - "Singleton pattern for UpdateService matching other services"
  - "Callback hooks for UI integration (on_update_available, on_error, etc.)"

patterns-established:
  - "UpdateService singleton via get_update_service()"
  - "Frozen/unfrozen path detection via sys.frozen and sys._MEIPASS"
  - "UpdateInfo dataclass for update metadata"

# Metrics
duration: 3min
completed: 2026-01-31
---

# Phase 08 Plan 02: Auto-Update Service Summary

**Tufup-based auto-update service with TUF cryptographic verification, lazy initialization, and graceful development mode fallback**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-31T15:12:44Z
- **Completed:** 2026-01-31T15:15:50Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added tufup>=0.10.0 dependency for TUF-based secure updates
- Created UpdateService class with check_for_updates() and download_and_install()
- Configured frozen/unfrozen path detection for PyInstaller compatibility
- Implemented graceful degradation when root.json not present

## Task Commits

Each task was committed atomically:

1. **Task 1: Add tufup dependency and update settings module** - `91bac5d` (chore)
2. **Task 2: Create UpdateService with tufup Client integration** - `d4242aa` (feat)

## Files Created/Modified
- `requirements.txt` - Added tufup>=0.10.0 dependency
- `src/updates/__init__.py` - Module exports for UpdateService and settings
- `src/updates/settings.py` - APP_NAME, CURRENT_VERSION, METADATA_DIR, TARGET_DIR configuration
- `src/updates/service.py` - UpdateService class with TUF-based update checking and installation

## Decisions Made
- **Lazy tufup client initialization:** Avoid startup delays by creating client only when needed
- **Graceful degradation:** Return None from check_for_updates() when root.json missing instead of crashing
- **Callback hooks:** on_update_available, on_download_progress, on_update_ready, on_error for UI integration
- **Singleton pattern:** get_update_service() matches other service patterns in the codebase

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None - tufup installation succeeded and all verifications passed.

## User Setup Required
None - no external service configuration required.

**Production deployment note:** For production builds:
1. Initialize TUF repository with `tufup init`
2. Bundle root.json in PyInstaller .spec file datas
3. Host update metadata and targets on UPDATE_SERVER_URL
4. Sign releases with private key

## Next Phase Readiness
- UpdateService ready for UI integration in 08-03/08-04
- API layer can expose check_for_updates() and download_and_install()
- Callbacks allow reactive UI updates for update notifications

---
*Phase: 08-notifications-polish*
*Completed: 2026-01-31*
