# Project State: DiscordOpus

**Current Phase:** Phase 4 - File Transfer
**Status:** In Progress
**Last Updated:** 2026-01-30

## Project Reference

See: .planning/PROJECT.md

**Core value:** Prywatna, w pelni szyfrowana komunikacja P2P bez zaufania do centralnego serwera - uzytkownicy kontroluja swoje dane i tozsamosc.

**Current focus:** Phase 4 - File transfer with E2E encryption over existing WebRTC data channels. Chunking for large files, progress tracking, and resume capability.

## Progress

```
[========================================>                              ] 52% (Phase 4 - 7/7 plans)
```

| Phase | Name | Status | Plans | Requirements |
|-------|------|--------|-------|--------------|
| 1 | Cryptographic Foundation & Packaging | COMPLETE | 7/7 | 14 |
| 2 | Signaling Infrastructure & Presence | COMPLETE | 5/5 | 12 |
| 3 | P2P Text Messaging | COMPLETE | 7/7 | 10 |
| 4 | File Transfer | COMPLETE | 7/7 | 7 |
| 5 | Voice Calls (1-on-1) | Pending | 0/? | 9 |
| 6 | Video & Screen Sharing | Pending | 0/? | 8 |
| 7 | Group Features | Pending | 0/? | 8 |
| 8 | Notifications & Polish | Pending | 0/? | 5 |

**Total:** 43/73 requirements completed (59%)

## Performance Metrics

**Velocity:**
- Plans completed: 26
- Average plan duration: 6m
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
| 2026-01-30 | No trickle ICE for aiortc | Wait for iceGatheringState == "complete" before returning SDP | Simpler SDP exchange via signaling |
| 2026-01-30 | Data channel before offer | aiortc requires data channel creation before createOffer() | Proper SDP negotiation |
| 2026-01-30 | 3-second typing throttle | Prevents typing indicator spam while maintaining UX | Max 1 typing event per 3 seconds |
| 2026-01-30 | Simplified X3DH key exchange | Use ephemeral + identity DH only (no pre-key bundles) | P2P connections exchange keys synchronously |
| 2026-01-30 | Async Signal encryption | All encrypt/decrypt methods are async (with sync wrappers) | Underlying doubleratchet library is fully async |
| 2026-01-30 | Lazy import for message_crypto | __getattr__ in crypto/__init__.py defers message_crypto imports | Breaks circular import with storage module |
| 2026-01-30 | Base64 encoding for encrypted transmission | Header, ciphertext, ephemeral_key encoded as base64 for data channel | JSON-safe message transmission |
| 2026-01-30 | Callback-based messaging notifications | MessagingService uses callbacks for async frontend notification | Clean separation, thread-safe event dispatch |
| 2026-01-30 | Inline SVG icons in chat UI | Use inline SVG paths instead of lucide-react dependency | Matches existing codebase pattern, no new dependencies |
| 2026-01-30 | Context menu inline SVG icons | Use inline SVG for MessageContextMenu icons | Consistency with existing pattern |
| 2026-01-30 | Unicode escape sequences for emoji | ReactionPicker uses \u{} escapes for consistent cross-platform rendering | Avoids font/encoding issues |
| 2026-01-30 | 100KB threshold for BLOB/filesystem storage | Research recommends 100KB as optimal balance between database size and filesystem overhead | Small files benefit from database transactionality, large files avoid database bloat |
| 2026-01-30 | Fernet for filesystem encryption | SQLCipher already encrypts BLOBs, only filesystem files need additional encryption; Fernet provides authenticated encryption | Defense-in-depth for large files on disk |
| 2026-01-30 | No double encryption for BLOBs | SQLCipher already encrypts database, additional encryption would be redundant | Better performance, same security |
| 2026-01-30 | 16KB chunk size for file transfer | Cross-browser compatibility - Firefox fragments at 16KB boundary, Chrome doesn't reassemble >16KB properly | Broader compatibility at slight throughput cost |
| 2026-01-30 | 64KB buffer threshold for backpressure | Typical WebRTC buffer limit is 256KB; use 64KB threshold to prevent overflow | Prevents connection crashes from buffer overflow |
| 2026-01-30 | Poll bufferedAmount instead of event-based | aiortc RTCDataChannel lacks bufferedAmountLow event (browser-only feature) | Slightly less efficient than event-driven but simplest working approach |
| 2026-01-30 | aiofiles for file transfer I/O | Prevent blocking asyncio event loop during file reads | Non-blocking transfers that don't degrade other operations |
| 2026-01-30 | Temp files for chunk assembly | Large files shouldn't be held in memory during reception | Supports receiving files larger than available RAM |
| 2026-01-30 | Max 3 concurrent transfers per contact | Prevent resource exhaustion from malicious or buggy peers | Service rejects new transfers when limit reached |
| 2026-01-30 | Callback-based transfer notifications | Clean separation between transfer logic and frontend notification | Service emits events that API layer translates to frontend updates |
| 2026-01-30 | Message routing by type detection | Route messages in NetworkService based on structure (binary 'C' prefix, JSON file_ type, control markers) | Clean separation between text messages and file transfers on same data channel |
| 2026-01-30 | Native file picker via tkinter | Use tkinter.filedialog for file selection | Cross-platform, no additional dependencies (bundled with Python), provides native OS dialogs |
| 2026-01-30 | Frontend events for file transfer | Custom events: file_progress, file_received, transfer_complete, transfer_error | Consistent with existing message events, allows reactive UI updates |
| 2026-01-30 | JPEG at 85% quality for thumbnails | Good balance between file size and visual quality for preview transmission | Small enough for fast loading, high enough quality for recognition |
| 2026-01-30 | 300x300 max thumbnail size | Large enough for recognition, small enough for fast transmission | Maintains aspect ratio, typical thumbnail size |
| 2026-01-30 | EXIF rotation via ImageOps.exif_transpose | Pillow automatically handles EXIF orientation metadata | Prevents sideways/upside-down mobile photos |
| 2026-01-30 | ffmpeg frame at 1 second | Extract video thumbnail at 1-second mark | Avoids blank/black first frames, configurable if needed |
| 2026-01-30 | Base64 preview transmission | Encode thumbnails as base64 for JSON-safe API responses | Simple data URI construction in frontend |
| 2026-01-30 | MIME-type-based component routing | FileMessage routes to ImagePreview, VideoPreview, or generic download based on MIME prefix | Clear separation of concerns, extensible for future types |
| 2026-01-30 | Transfer store uses Map for state | O(1) lookups by transferId, easier iteration over active transfers | Better performance than array filter/find |
| 2026-01-30 | Event-driven transfer updates | Transfer store listens to file_progress/file_received/transfer_complete/transfer_error events | Consistent with messages.ts pattern, automatic UI updates |
| 2026-01-30 | TransferProgress filters by contactId | Each chat shows only its own transfers, not all active transfers | Clean per-chat UX |
| 2026-01-30 | MessageInput restructured for composition | FileUpload button sits alongside input in ChatPanel wrapper | Removed MessageInput's border wrapper for cleaner integration |
| 2026-01-30 | File messages stored in messages table | Use file_id foreign key to reference files table, same table as text messages | Unified chat history simplifies querying and display |
| 2026-01-30 | Lazy metadata loading for file messages | FileMessageWrapper fetches metadata on mount instead of including in message | Better performance for scrolling through history |
| 2026-01-30 | Type-based preview routing | FileMessage routes based on MIME type: image → ImagePreview, video → VideoPreview, other → download | Extensible pattern for future file type support |

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
- [x] Execute 03-02-PLAN.md (Signal Protocol)
- [x] Execute 03-03-PLAN.md (WebRTC data channels)
- [x] Execute 03-04-PLAN.md (message protocol integration)
- [x] Execute 03-05-PLAN.md (chat UI)
- [x] Execute 03-06-PLAN.md (message features)
- [x] Execute 03-07-PLAN.md (integration) - PHASE 3 COMPLETE
- [x] Execute 04-01-PLAN.md (file storage infrastructure)
- [x] Execute 04-02-PLAN.md (file chunking and sender)
- [x] Execute 04-03-PLAN.md (file receiver and service orchestration)
- [x] Execute 04-04-PLAN.md (network and API integration)
- [x] Execute 04-05-PLAN.md (image and video previews)
- [x] Execute 04-07-PLAN.md (file transfer UI)
- [x] Execute 04-06-PLAN.md (file transfer message integration) - PHASE 4 COMPLETE
- [ ] Research aiortc audio codec interop before Phase 5 planning
- [ ] Research Sender Keys protocol before Phase 7 planning

### Blockers

*None currently*

### Research Flags

**High priority (research before planning):**
- Phase 5: aiortc audio codec interop with browser peers
- Phase 7: Sender Keys protocol implementation and mesh optimization

**Medium priority (research during planning):**
- Phase 4: File chunking and resume protocol
- Phase 6: Cross-browser WebRTC compatibility

**Low priority (use standard patterns):**
- Phase 1, 2, 8: Well-documented, skip research-phase

## Session Continuity

**Last session:** 2026-01-30 - Completed 04-06-PLAN.md (file transfer message integration)

**What we just completed:**
- Executed plan 04-06 (file transfer message integration)
- Extended message storage with file_id column and save_file_message function (already done in 04-07)
- Created FileMessageWrapper component for lazy metadata loading
- Updated MessageBubble to detect and render file messages
- Verified end-to-end file transfer working with user approval
- PHASE 4 COMPLETE - all 7 file transfer requirements satisfied

**What's next:**
- Research aiortc audio codec interop before Phase 5 planning
- Plan Phase 5 (Voice Calls) with `/gsd:plan-phase 5`

**Open questions:**
- None

**Files created this session:**
- frontend/src/components/chat/FileMessageWrapper.tsx
- .planning/phases/04-file-transfer/04-06-SUMMARY.md

**Files modified this session:**
- frontend/src/lib/pywebview.ts
- frontend/src/stores/messages.ts
- frontend/src/components/chat/MessageBubble.tsx
- .planning/STATE.md

---

*State initialized: 2026-01-30*
*Last updated: 2026-01-30 after completing 04-01-PLAN.md*
