# Project State: DiscordOpus

**Current Phase:** Phase 3 - P2P Text Messaging
**Status:** In Progress (Plan 1/7 complete)
**Last Updated:** 2026-01-30

## Project Reference

See: .planning/PROJECT.md

**Core value:** Prywatna, w pelni szyfrowana komunikacja P2P bez zaufania do centralnego serwera - uzytkownicy kontroluja swoje dane i tozsamosc.

**Current focus:** Phase 3 - P2P text messaging using WebRTC data channels over the signaling infrastructure built in Phase 2. Signal Protocol (Double Ratchet) for E2E encryption, message persistence in SQLCipher, and chat UI.

## Progress

```
[==================>                                                    ] 25% (Phase 2/8 COMPLETE)
```

| Phase | Name | Status | Plans | Requirements |
|-------|------|--------|-------|--------------|
| 1 | Cryptographic Foundation & Packaging | COMPLETE | 7/7 | 14 |
| 2 | Signaling Infrastructure & Presence | COMPLETE | 5/5 | 12 |
| 3 | P2P Text Messaging | In Progress | 1/7 | 10 |
| 4 | File Transfer | Pending | 0/? | 7 |
| 5 | Voice Calls (1-on-1) | Pending | 0/? | 9 |
| 6 | Video & Screen Sharing | Pending | 0/? | 8 |
| 7 | Group Features | Pending | 0/? | 8 |
| 8 | Notifications & Polish | Pending | 0/? | 5 |

**Total:** 26/73 requirements completed (36%)

## Performance Metrics

**Velocity:**
- Plans completed: 13
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
| 2026-01-30 | NetworkService runs in background thread | webview.start(func=...) runs in separate thread with asyncio loop | Non-blocking GUI |
| 2026-01-30 | Frontend events via CustomEvent | evaluate_js dispatches discordopus:* events | Clean JS notification pattern |
| 2026-01-30 | Network store initializes on Sidebar mount | Centralized initialization point for network state | Consistent state on app load |
| 2026-01-30 | Contact status matching uses includes() | Partial public key matching from presence events | Handles truncated keys in events |
| 2026-01-30 | Soft delete pattern for messages | delete_message with hard_delete=False sets deleted=1 and body=NULL | Preserves message metadata for conversation integrity |
| 2026-01-30 | UNIQUE constraint for reactions | Database-level enforcement on (message_id, sender_id, emoji) | Prevents duplicate reactions automatically |
| 2026-01-30 | BLOB for Signal session state | Binary BLOB type for signal_sessions.session_state | Flexibility in serialization format (pickle, msgpack, custom) |

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
- [x] Execute 02-03-PLAN.md (network integration)
- [x] Execute 02-04-PLAN.md (presence UI)
- [x] Execute 02-05-PLAN.md (visual verification) - PHASE 2 COMPLETE
- [x] Execute 03-01-PLAN.md (message storage layer)
- [ ] Execute 03-02-PLAN.md (Signal Protocol)
- [ ] Execute 03-03-PLAN.md (WebRTC data channels)
- [ ] Execute 03-04-PLAN.md (message protocol)
- [ ] Execute 03-05-PLAN.md (chat UI)
- [ ] Execute 03-06-PLAN.md (message features)
- [ ] Execute 03-07-PLAN.md (integration)
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

**Last session:** 2026-01-30 - Completed 03-01-PLAN.md (message storage layer)

**What we were doing:**
- Executed plan 03-01 (message storage layer)
- Extended SQLCipher schema with messages, reactions, signal_sessions tables
- Created messages.py with complete CRUD operations

**What's next:**
- Execute 03-02-PLAN.md (Signal Protocol implementation)
- Continue with remaining Phase 3 plans

**Open questions:**
- None

**Files created this session:**
- src/storage/messages.py

**Files modified this session:**
- src/storage/db.py (messages, reactions, signal_sessions tables)
- src/storage/__init__.py (exported message functions)

---

*State initialized: 2026-01-30*
*Last updated: 2026-01-30 after 03-01 completion*
