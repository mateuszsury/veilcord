---
phase: 11-branding-documentation-release
plan: 01
subsystem: branding
tags: [rebrand, veilcord, pyinstaller, frontend, event-system]

# Dependency graph
requires:
  - phase: 10-ui-ux-redesign
    provides: Complete UI redesign with design system foundation
provides:
  - Application rebranded from DiscordOpus to Veilcord across all user-facing touchpoints
  - Preserved cryptographic protocol identifiers for backward compatibility
  - Updated build system to produce Veilcord.exe
affects: [11-02-readme-creation, release-preparation]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Dual-identity architecture: user-facing brand vs protocol identifiers"]

key-files:
  created: []
  modified:
    - src/storage/paths.py
    - src/main.py
    - src/notifications/service.py
    - build.spec
    - frontend/package.json
    - frontend/index.html
    - frontend/src/lib/pywebview.ts
    - frontend/src/stores/*.ts (all stores)
    - frontend/src/components/layout/UpdatePrompt.tsx
    - frontend/src/components/groups/JoinGroupDialog.tsx

key-decisions:
  - "Preserved crypto protocol byte strings (b'DiscordOpus_*') to maintain backward compatibility with existing encrypted sessions"
  - "Updated all user-facing identifiers (window title, app data paths, notifications, event names) to Veilcord"
  - "Changed URL scheme from discordopus:// to veilcord:// for group invites"

patterns-established:
  - "Branding separation: UI/UX shows Veilcord, cryptographic protocols use DiscordOpus identifiers"

# Metrics
duration: 4min
completed: 2026-02-04
---

# Phase 11 Plan 01: Application Rebrand Summary

**Complete rebrand from DiscordOpus to Veilcord for all user-facing touchpoints while preserving cryptographic protocol identifiers for backward compatibility**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-04T14:16:09Z
- **Completed:** 2026-02-04T14:20:10Z
- **Tasks:** 3
- **Files modified:** 19

## Accomplishments
- All user-visible branding updated to Veilcord (window title, app data paths, notifications, events)
- Cryptographic protocol constants preserved (backward compatibility maintained)
- Build configuration updated to produce dist/Veilcord/Veilcord.exe
- Frontend event system namespace changed from 'discordopus:' to 'veilcord:'

## Task Commits

Each task was committed atomically:

1. **Task 1: Rebrand Python backend identifiers** - `a09f299` (feat)
2. **Task 2: Rebrand frontend and build configuration** - `150611c` (feat)
3. **Task 3: Update frontend event listeners** - `4e3c886` (feat)

## Files Created/Modified
- `src/storage/paths.py` - App data path changed to %APPDATA%/Veilcord/
- `src/main.py` - Window title 'Veilcord', event 'veilcord:update_available'
- `src/notifications/service.py` - AUMID changed to "Veilcord.SecureMessenger"
- `build.spec` - PyInstaller config produces Veilcord.exe in dist/Veilcord/
- `frontend/package.json` - Package name changed to "veilcord-frontend"
- `frontend/index.html` - HTML title changed to "Veilcord"
- `frontend/src/lib/pywebview.ts` - WindowEventMap types updated to 'veilcord:*' events
- `frontend/src/stores/chat.ts` - Event listeners updated to 'veilcord:p2p_state', 'veilcord:message'
- `frontend/src/stores/call.ts` - Event listeners updated to 'veilcord:call_*', 'veilcord:video_*'
- `frontend/src/stores/contacts.ts` - Event listeners updated to 'veilcord:presence', 'veilcord:open_chat'
- `frontend/src/stores/discovery.ts` - Event listener updated to 'veilcord:discovery_user'
- `frontend/src/stores/groupMessages.ts` - Event listener updated to 'veilcord:group_message'
- `frontend/src/stores/groups.ts` - Event listeners updated to 'veilcord:group_*'
- `frontend/src/stores/messages.ts` - Event listener updated to 'veilcord:message'
- `frontend/src/stores/transfers.ts` - Event listeners updated to 'veilcord:file_*', 'veilcord:transfer_*'
- `frontend/src/stores/network.ts` - Event listener updated to 'veilcord:connection'
- `frontend/src/components/layout/UpdatePrompt.tsx` - Event listener updated to 'veilcord:update_available'
- `frontend/src/components/groups/JoinGroupDialog.tsx` - URL scheme updated to veilcord://join/

## Decisions Made

1. **Preserved cryptographic protocol identifiers** - Kept all byte strings in src/crypto/signal_session.py unchanged (e.g., `b"DiscordOpus_RootChain_v1"`) to maintain backward compatibility with existing encrypted sessions. Changing these would break all active Double Ratchet sessions.

2. **Updated event namespace comprehensively** - Changed all 26 custom events from 'discordopus:' to 'veilcord:' prefix across frontend stores, components, and TypeScript type definitions for consistency.

3. **URL scheme rebrand** - Updated group invite URL scheme from `discordopus://join/...` to `veilcord://join/...` for consistency with new brand identity.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - rebrand completed successfully with no issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Application fully rebranded to Veilcord
- Build system ready to produce Veilcord.exe
- Cryptographic protocol compatibility maintained
- Ready for README creation (11-02) which will use new Veilcord branding
- No blockers for documentation phase

---
*Phase: 11-branding-documentation-release*
*Completed: 2026-02-04*
