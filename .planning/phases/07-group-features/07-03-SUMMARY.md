---
phase: 07-group-features
plan: 03
subsystem: groups
tags: [groups, invite-codes, lifecycle, membership, base64, secrets]

# Dependency graph
requires:
  - phase: 07-01
    provides: Group and GroupMember models, group storage functions
  - phase: 07-02
    provides: Sender Keys for group message encryption
provides:
  - GroupService class for group lifecycle management
  - Invite code generation with cryptographic security
  - Invite parsing and validation with expiry checking
  - Member management with permission checks
affects: [07-04, 07-05, 07-06, 07-07, 07-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Callback-based service events for UI integration"
    - "Permission checks in service layer (admin/creator)"
    - "discordopus://join/ URL scheme for invites"

key-files:
  created:
    - src/groups/invite.py
    - src/groups/group_service.py
  modified:
    - src/groups/__init__.py

key-decisions:
  - "discordopus://join/ URL scheme for invite codes"
  - "Base64-encoded JSON payload in invite URLs"
  - "7-day default invite expiry"
  - "128-bit random token via secrets.token_urlsafe"
  - "Creator automatically added as admin on group creation"
  - "Only admins can generate invites and remove members"
  - "Creator cannot be removed from group"

patterns-established:
  - "GroupService callback pattern for event notification"
  - "Service layer permission checks before storage operations"
  - "InviteData dataclass for parsed invite metadata"

# Metrics
duration: 4min
completed: 2026-01-31
---

# Phase 7 Plan 3: Group Service Summary

**GroupService with invite code generation, membership management, and permission-based lifecycle operations**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-31
- **Completed:** 2026-01-31
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Invite code generation with discordopus://join/ URL scheme and cryptographic randomness
- GroupService class managing full group lifecycle (create, join, leave, invite)
- Permission system: only admins can generate invites and remove members
- Callback-based event notifications for UI integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement invite code generation and parsing** - `d2fa487` (feat)
2. **Task 2: Implement GroupService for lifecycle management** - `ad9a8a2` (feat)
3. **Task 3: Update groups __init__ with new exports** - `b10949d` (chore)

## Files Created/Modified

- `src/groups/invite.py` - Invite code generation/parsing with InviteData dataclass
- `src/groups/group_service.py` - GroupService class for lifecycle operations
- `src/groups/__init__.py` - Updated exports for new modules

## Decisions Made

1. **discordopus://join/ URL scheme** - Custom protocol for invite URLs enables deep linking
2. **Base64-encoded JSON payload** - Self-contained invite with all metadata, no database lookup needed
3. **7-day default expiry** - Balance between security and usability
4. **128-bit random token** - Prevents enumeration attacks on invite codes
5. **Creator auto-admin** - Group creator is automatically added as admin member
6. **Admin-only invites** - Only admins can generate invite codes
7. **Creator protection** - Creator cannot be removed from group

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- GroupService ready for network integration (07-04)
- Invite codes can be shared and validated
- Member management APIs ready for UI binding
- Sender Keys integration point ready (leave_group cleans up keys)

---
*Phase: 07-group-features*
*Completed: 2026-01-31*
