# Project State: DiscordOpus

**Current Phase:** Phase 2 - Signaling Infrastructure & Presence
**Status:** In Progress
**Last Updated:** 2026-01-30

## Project Reference

See: .planning/PROJECT.md

**Core value:** Prywatna, w pelni szyfrowana komunikacja P2P bez zaufania do centralnego serwera - uzytkownicy kontroluja swoje dane i tozsamosc.

**Current focus:** Phase 2 - Establishing signaling server connection via WebSocket, presence system for online/offline status, and contact status synchronization. This phase enables the P2P connection establishment required for messaging in Phase 3.

## Progress

```
[============>                                                          ] 14% (Phase 2 in progress)
```

| Phase | Name | Status | Plans | Requirements |
|-------|------|--------|-------|--------------|
| 1 | Cryptographic Foundation & Packaging | COMPLETE | 7/7 | 14 |
| 2 | Signaling Infrastructure & Presence | In Progress | 2/? | 12 |
| 3 | P2P Text Messaging | Pending | 0/? | 10 |
| 4 | File Transfer | Pending | 0/? | 7 |
| 5 | Voice Calls (1-on-1) | Pending | 0/? | 9 |
| 6 | Video & Screen Sharing | Pending | 0/? | 8 |
| 7 | Group Features | Pending | 0/? | 8 |
| 8 | Notifications & Polish | Pending | 0/? | 5 |

**Total:** 14/73 requirements completed (19%)

## Performance Metrics

**Velocity:**
- Plans completed: 9
- Average plan duration: 5m
- Estimated completion: TBD (more data needed)

**Quality:**
- Plans passing first time: N/A
- Verification failures: 0
- Rework ratio: N/A

**Blockers:**
- Active blockers: 0
- Resolved blockers: 0

## Accumulated Context

### Key Decisions

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2026-01-30 | 8 phases (not 6 from research) | Comprehensive depth setting + clearer separation of concerns (file transfer separate from messaging, video separate from voice) | Better delivery boundaries, each phase delivers one coherent capability |
| 2026-01-30 | Phase 1 includes UI foundation | Validate Python-React bridge early (high-risk), users can see progress immediately | UI ready for Phase 3 messaging |
| 2026-01-30 | No TURN relay (STUN only) | Accept 20-30% connection failure (symmetric NAT) for zero ongoing costs | Must implement clear connection diagnostics and error messages |
| 2026-01-30 | SQLCipher + DPAPI from Phase 1 | Secure key storage is architectural constraint, expensive to change later | Keys never stored plaintext, safe to backup |
| 2026-01-30 | Use sqlcipher3 (not -binary) | sqlcipher3-binary lacks Python 3.13 Windows wheels | None - same API |
| 2026-01-30 | Separate Ed25519 and X25519 keys | cryptography library removed Ed25519-to-X25519 conversion support | Generate two independent key pairs |
| 2026-01-30 | Private keys in filesystem, public in DB | Defense-in-depth: database compromise doesn't expose private keys | identity.key file separate from data.db |
| 2026-01-30 | Zustand stores manage state only | API calls happen in components via api.call() - simpler architecture | Clear separation of concerns |
| 2026-01-30 | Tailwind v4 @theme directive | Use native v4 approach instead of separate tailwind.config.ts | Simpler configuration |
| 2026-01-30 | RFC 9106 desktop params for Argon2id | 64MB memory, 3 iterations, 4 lanes - balances security with <1s completion | Backup creation fast enough for UX |
| 2026-01-30 | Versioned backup format with embedded KDF params | Future versions can read old backups by using embedded parameters | Forward compatibility for backup files |
| 2026-01-30 | Contact X25519 keys use placeholder | X25519 public keys exchanged during P2P connection, not at contact add time | Contact storage works before Phase 2 networking |
| 2026-01-30 | API methods return JSON-serializable dicts | Complex Python objects converted to dicts for JavaScript consumption | Clean API bridge pattern |
| 2026-01-30 | ed25519_private_key property on Identity | SignalingClient needs key object, not PEM bytes; added property to Identity class | Clean access to signing key |
| 2026-01-30 | websockets>=15.0 (not 16.0) | v15.0.1 already installed, API compatible with requirements | No additional install needed |
| 2026-01-30 | Settings stored as strings | All setting values are strings; callers handle type conversion | Simple key-value API |
| 2026-01-30 | Database migration via ALTER TABLE | Use try/except OperationalError pattern for column additions | Safe for existing databases |

### Active TODOs

- [x] Plan Phase 1 with `/gsd:plan-phase 1`
- [x] Execute 01-01-PLAN.md (project scaffolding)
- [x] Execute 01-02-PLAN.md (DPAPI + SQLCipher storage)
- [x] Execute 01-03-PLAN.md (cryptographic identity)
- [x] Execute 01-05-PLAN.md (React UI shell)
- [x] Execute 01-04-PLAN.md (password-based key backup)
- [x] Execute 01-06-PLAN.md (Settings panel and identity UI)
- [x] Execute 01-07-PLAN.md (PyInstaller packaging) - PHASE 1 COMPLETE
- [x] Execute 02-01-PLAN.md (WebSocket signaling client)
- [x] Execute 02-02-PLAN.md (presence system)
- [ ] Research aiortc data channels before Phase 3 planning
- [ ] Research aiortc audio codec interop before Phase 5 planning
- [ ] Research Sender Keys protocol before Phase 7 planning

### Blockers

*None currently*

### Research Flags

**High priority (research before planning):**
- Phase 5: aiortc audio codec interop with browser peers
- Phase 7: Sender Keys protocol implementation and mesh optimization

**Medium priority (research during planning):**
- Phase 3: aiortc data channel reliability, offline message patterns
- Phase 4: File chunking and resume protocol
- Phase 6: Cross-browser WebRTC compatibility

**Low priority (use standard patterns):**
- Phase 1, 2, 8: Well-documented, skip research-phase

## Session Continuity

**Last session:** 2026-01-30 - Completed 02-02-PLAN.md

**What we were doing:**
- Executed Phase 2 Plan 02: Presence State Management
- Created settings key-value storage
- Added online_status to contacts
- Built PresenceManager for user/contact status

**What's next:**
- Execute remaining Phase 2 plans
- Integrate PresenceManager with SignalingClient

**Open questions:**
- None

**Files created this session:**
- src/storage/settings.py
- src/network/presence.py
- .planning/phases/02-signaling-infrastructure--presence/02-02-SUMMARY.md

**Files modified this session:**
- src/storage/db.py (settings table, online_status column)
- src/storage/contacts.py (online_status field and functions)
- src/storage/__init__.py (settings exports)
- src/network/__init__.py (presence exports)

---

*State initialized: 2026-01-30*
*Last updated: 2026-01-30 after 02-02-PLAN.md execution*
