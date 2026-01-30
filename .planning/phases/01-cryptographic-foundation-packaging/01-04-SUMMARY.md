---
phase: 01-cryptographic-foundation-packaging
plan: 04
subsystem: crypto
tags: [argon2id, chacha20poly1305, backup, kdf, password-based-encryption]

# Dependency graph
requires:
  - phase: 01-03
    provides: Identity class with Ed25519/X25519 key pairs
provides:
  - Password-based identity backup with Argon2id KDF
  - ChaCha20Poly1305 authenticated encryption for backups
  - File I/O helpers for backup export/import
  - Backup metadata inspection without decryption
affects:
  - 01-06 (Settings panel - will add backup/restore UI)
  - Future machine migration scenarios

# Tech tracking
tech-stack:
  added: []  # argon2-cffi already in requirements.txt
  patterns:
    - Argon2id KDF with RFC 9106 desktop parameters (64MB, 3 iter, 4 lanes)
    - ChaCha20Poly1305 authenticated encryption
    - Versioned backup format for forward compatibility

key-files:
  created:
    - src/crypto/backup.py
  modified:
    - src/crypto/__init__.py

key-decisions:
  - "RFC 9106 desktop params for Argon2id (64MB memory, 3 iterations, 4 lanes)"
  - "Include version and KDF params in backup JSON for forward compatibility"
  - "Minimum 4 character password (8+ recommended)"

patterns-established:
  - "Password-based encryption: Argon2id -> ChaCha20Poly1305"
  - "Versioned data format with embedded parameters"
  - "Clear error messages for wrong password (BackupError)"

# Metrics
duration: 3min
completed: 2026-01-30
---

# Phase 01 Plan 04: Password-Based Key Backup Summary

**Argon2id password-based identity backup with ChaCha20Poly1305 authenticated encryption for cross-machine recovery**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-30T04:38:05Z
- **Completed:** 2026-01-30T04:41:XX Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Implemented password-based backup using Argon2id KDF (RFC 9106 parameters)
- ChaCha20Poly1305 provides authenticated encryption with tamper detection
- Fresh random salt (32 bytes) and nonce (12 bytes) per export
- Backup JSON includes version and KDF params for forward compatibility
- File I/O helpers for convenient backup export/import
- Clear "Wrong password or corrupted backup" error handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Argon2id Key Backup Export** - `94e4e9b` (feat)
2. **Task 2: Add Backup File I/O Helpers** - `1fa9f94` (feat)

## Files Created/Modified
- `src/crypto/backup.py` - Password-based backup with Argon2id + ChaCha20Poly1305
- `src/crypto/__init__.py` - Export backup functions (export_backup, import_backup, BackupError, etc.)

## Decisions Made
- **RFC 9106 desktop parameters:** memory_cost=65536 (64MB), iterations=3, lanes=4 - balances security with <1s completion time
- **Versioned backup format:** Backup JSON includes version and KDF params so future versions can read old backups
- **Minimum 4 character password:** Low bar for now, UI should recommend 8+ characters

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Backup/restore API ready for Settings UI (01-06)
- DPAPI keys can now be recovered if Windows is reinstalled
- Ready for Python-React bridge implementation (01-04 in original plan order, but already executed in 01-05)

---
*Phase: 01-cryptographic-foundation-packaging*
*Completed: 2026-01-30*
