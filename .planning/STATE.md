# Project State: DiscordOpus

**Current Phase:** Phase 10 - UI/UX Redesign
**Status:** In progress (4/10 plans complete)
**Last Updated:** 2026-02-02T08:05:00Z

## Project Reference

See: .planning/PROJECT.md

**Core value:** Prywatna, w pelni szyfrowana komunikacja P2P bez zaufania do centralnego serwera - uzytkownicy kontroluja swoje dane i tozsamosc.

**Current focus:** Phase 10 UI/UX Redesign - establishing design system foundation.

## Progress

```
[=================================================================           ] 87% (v1.0 COMPLETE, Phase 10 in progress)
```

| Phase | Name | Status | Plans | Requirements |
|-------|------|--------|-------|--------------|
| 1 | Cryptographic Foundation & Packaging | COMPLETE | 7/7 | 14 |
| 2 | Signaling Infrastructure & Presence | COMPLETE | 5/5 | 12 |
| 3 | P2P Text Messaging | COMPLETE | 7/7 | 10 |
| 4 | File Transfer | COMPLETE | 8/8 | 7 |
| 5 | Voice Calls (1-on-1) | COMPLETE | 8/8 | 9 |
| 6 | Video & Screen Sharing | COMPLETE | 6/6 | 8 |
| 7 | Group Features | COMPLETE | 8/8 | 8 |
| 8 | Notifications & Polish | COMPLETE | 5/5 | 5 |
| 9 | Audio & Video Effects | COMPLETE | 12/12 | 8 |
| 10 | UI/UX Redesign | IN PROGRESS | 4/10 | - |

**Total:** 81/81 core requirements completed (100% - v1.0 complete)
**Phase 10 Progress:** 4/10 plans completed (10-01 Design System, 10-02 UI Primitives, 10-03 IconBar, 10-04 ChannelList COMPLETE)

## Performance Metrics

**Velocity:**
- Plans completed: 66
- Average plan duration: 9m
- Project complete: All planned phases finished

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
| 2026-01-30 | User re-selects file for resume | No original path storage - user must locate and re-select the same file for resume | Simpler implementation, validated by file size match |
| 2026-01-30 | sounddevice for audio device access | Auto-installs PortAudio on Windows, simpler API than PyAudio | Cleaner device enumeration and audio I/O |
| 2026-01-30 | 7-state CallState enum | IDLE, RINGING_*, CONNECTING, ACTIVE, RECONNECTING, ENDED covers full lifecycle | Clear state machine for UI and logic |
| 2026-01-30 | Thread-safe async queue for audio | Use loop.call_soon_threadsafe() to bridge sounddevice callback thread to asyncio | Safe audio data transfer between threads |
| 2026-01-30 | Mute returns silence instead of stopping | When muted, track returns zero-filled frames instead of stopping capture | Allows instant unmute without stream restart |
| 2026-01-30 | Drop frames on queue full | Prevent memory bloat by dropping oldest frames when buffer exceeds 100 | Better than blocking callback thread |
| 2026-01-30 | PyOgg libopusenc for voice messages | Use low-level libopusenc bindings instead of high-level API | Streams Opus directly to Ogg files, no memory bloat |
| 2026-01-30 | ctypes to numpy via as_array() | Use np.ctypeslib.as_array() for OpusFile buffer conversion | PyOgg returns LP_c_short pointer, not buffer protocol |
| 2026-01-30 | Separate PC for voice calls | Voice calls use different RTCPeerConnection than data channels | Allows media renegotiation independent of messaging |
| 2026-01-30 | Callback-based voice call notifications | VoiceCallService uses callbacks for state changes and signaling | Consistent with messaging and file transfer patterns |
| 2026-01-30 | Voice recorder stored on NetworkService | _voice_recorder attribute lazily created on first recording | Shared instance for recording session, cleared after stop/cancel |
| 2026-01-30 | Call store event listeners for full lifecycle | Listen to call_state, incoming_call, call_answered, call_rejected, call_ended events | Complete call UI state synchronization |
| 2026-01-30 | Local duration timer in ActiveCallOverlay | Timer increments locally every second instead of syncing from backend | Simpler implementation, avoids network latency in duration display |
| 2026-01-30 | Duration polling every 100ms for voice recording | Smooth UI updates without pushing duration from backend | Clean polling pattern in Zustand store |
| 2026-01-30 | Audio file detection via MIME type and extension | Robust detection using both mimeType.startsWith('audio/') and file extension list | Handles edge cases where MIME type is generic |
| 2026-01-30 | 5 minute max recording with 4:30 warning | Reasonable limit for voice messages, warning gives time to finish | Prevents very large recordings, good UX |
| 2026-01-31 | mss package name (not python-mss) | PyPI package is 'mss', not 'python-mss' as originally planned | Corrected requirements.txt |
| 2026-01-31 | 15 FPS for screen sharing | Screen sharing is less demanding than camera, reduces bandwidth | Default fps=15 for ScreenShareTrack |
| 2026-01-31 | last_frame buffer for API access | Store most recent frame for API access without blocking WebRTC pipeline | Enables frontend to request frames without timing issues |
| 2026-01-31 | RemoteVideoHandler as separate class | Dedicated class for remote video frame handling | Clean separation from VoiceCallService, reusable pattern |
| 2026-01-31 | BGR output for video frames | Convert to BGR for get_local/remote_video_frame methods | OpenCV uses BGR, ready for JPEG encoding without additional conversion |
| 2026-01-31 | Renegotiation via new offer | Create new SDP offer for video enable/disable | aiortc doesn't support removeTrack, renegotiation via new offer works |
| 2026-01-31 | sdp_type field for renegotiation | Use sdp_type field to distinguish offer/answer in call_video_renegotiate messages | Same message type for both directions, field disambiguates |
| 2026-01-31 | Video state in call store | Single source of truth for video-related state during calls | Enables reactive UI updates when video state changes |
| 2026-01-31 | 30 FPS frame polling | Poll video frames at 33ms interval for smooth playback | Balance between smoothness and CPU usage |
| 2026-01-31 | JPEG at 70% quality for frames | Good compression for real-time transmission | Acceptable quality with small payload size |
| 2026-01-31 | Expandable call overlay | Compact for audio-only, 480x380 for video | Good UX for both call types |
| 2026-01-31 | Soft delete for groups | is_active flag instead of hard delete | Preserves group history |
| 2026-01-31 | UNIQUE constraint on group members | (group_id, public_key) enforced at DB level | Prevents duplicate members |
| 2026-01-31 | Hex encoding for sender key blobs | chain_key and signature_public as hex in to_dict() | JSON-safe serialization |
| 2026-01-31 | Domain separation for sender keys | Unique HKDF info strings (DiscordOpus_SenderKey_*) | Prevents key reuse vulnerabilities |
| 2026-01-31 | Max 1000 message skip for out-of-order | Limit skipped key cache size | Balance out-of-order tolerance with memory safety |
| 2026-01-31 | Signature verification before decrypt | Verify Ed25519 signature first in decrypt() | Fail fast on tampered messages |
| 2026-01-31 | discordopus://join/ URL scheme | Custom protocol for invite codes enables deep linking | Self-contained invite URLs |
| 2026-01-31 | Base64 JSON payload in invites | All invite metadata in URL, no server lookup needed | Offline-capable invite validation |
| 2026-01-31 | 7-day default invite expiry | Balance security with usability | Reasonable time window for joining |
| 2026-01-31 | 128-bit random token in invites | Use secrets.token_urlsafe(16) for uniqueness | Prevents invite enumeration attacks |
| 2026-01-31 | Creator auto-admin on group create | Group creator automatically added as admin member | Consistent permission model |
| 2026-01-31 | Admin-only invite generation | Only admins can generate invite codes | Controlled group access |
| 2026-01-31 | Mesh topology for group calls | Each participant maintains N-1 peer connections | Best latency, no SFU required |
| 2026-01-31 | Polite/impolite by public key | Higher public key initiates connection | Deterministic, no coordination needed |
| 2026-01-31 | 4 participant soft limit | 300 kbps total bandwidth is reasonable | Warning displayed for 5+ |
| 2026-01-31 | 8 participant hard limit | Mesh becomes impractical above this | Refuse connections above limit |
| 2026-01-31 | 50 kbps per audio stream | Opus codec at standard quality | Consistent with 1:1 calls |
| 2026-01-31 | Callback-based broadcast for groups | GroupMessagingCallbacks.broadcast_group_message | Consistent with messaging/file transfer patterns |
| 2026-01-31 | Key rotation on member removal | Regenerate sender key when member leaves | Forward secrecy - removed member can't decrypt future messages |
| 2026-01-31 | Mutual exclusion for contact/group selection | setSelectedContact clears group, setSelectedGroup clears contact | Clean UX - only one chat active at a time |
| 2026-01-31 | Group event listeners at module level | Store registers listeners on load, not in components | Global state updates regardless of mounted components |
| 2026-01-31 | Admin detection via creator_public_key | Compare group.creator_public_key to identity.publicKey | Simple admin check without role system |
| 2026-01-31 | InteractableWindowsToaster for notifications | Use InteractableWindowsToaster (not WindowsToaster) for Action Center button callbacks | Callbacks work after notification relegation |
| 2026-01-31 | Custom AUMID for notifications | "DiscordOpus.SecureMessenger" for consistent notification identification | May need Windows registration for production |
| 2026-01-31 | Lazy toaster initialization | Avoid startup delays by creating toaster on first notification | Better app startup time |
| 2026-01-31 | Callback-based notification responses | on_open_chat, on_accept_call, on_reject_call hooks | NetworkService integration pattern |
| 2026-01-31 | Lazy tufup client initialization | Avoid startup delays by creating client only when needed | UpdateService doesn't slow app launch |
| 2026-01-31 | Graceful degradation for missing root.json | Return None from check_for_updates() when root.json missing | Development mode works without TUF repo |
| 2026-01-31 | Callback hooks for UpdateService | on_update_available, on_download_progress, on_update_ready, on_error | UI integration points for update notifications |
| 2026-01-31 | UpdateService singleton pattern | get_update_service() matches other service patterns | Consistent service access pattern |
| 2026-01-31 | NotificationService init in _async_start | Initialize after messaging service, wire callbacks to NetworkService methods | Clean integration point for notifications |
| 2026-01-31 | discordopus:open_chat event for notification clicks | Frontend event listener in contacts store routes to UIStore.setSelectedContact | Notification click switches to relevant chat |
| 2026-01-31 | 3-second delay before update check | Wait for app to fully initialize before checking updates | Avoids race conditions with frontend loading |
| 2026-01-31 | UpdatePrompt in AppLayout as global component | Banner appears regardless of active panel | Consistent UX across all views |
| 2026-01-31 | Session-based dismiss for update banner | User can dismiss, banner returns on restart if update still available | Balance between persistence and user control |
| 2026-02-02 | Lazy torch import in HardwareDetector | torch is large and slow to import; lazy loading avoids delaying app startup | Prevents Phase 9 effects from slowing application startup |
| 2026-02-02 | Singleton pattern for HardwareDetector | Hardware capabilities don't change during app runtime, cache results | Efficient re-detection avoidance, single source of truth |
| 2026-02-02 | QualityPreset CUDA→ULTRA, OpenCL→HIGH, CPU→MEDIUM | Auto-select best quality based on hardware capabilities | Optimal quality with graceful CPU fallback |
| 2026-02-02 | GPUtil as optional dependency | Only works with NVIDIA GPUs, not all users have NVIDIA | Graceful degradation for non-NVIDIA or integrated graphics |
| 2026-02-02 | Blur strength mapping for virtual backgrounds | Map 1-100 to Gaussian kernel 15-95 (15 + strength * 0.8) | Intuitive user control with technical precision |
| 2026-02-02 | AnimatedBackground preloads all frames | GIF/video frames loaded to memory for smooth playback | Prevents I/O latency during real-time processing |
| 2026-02-02 | Background image caching by frame size | Cache resized backgrounds to avoid repeated cv2.resize | Performance optimization for real-time video |
| 2026-02-02 | BaseVoiceEffect intensity blending | All voice effects inherit from BaseVoiceEffect with 0.0-1.0 intensity for wet/dry blending | Consistent UX for smooth effect control across all voice transformations |
| 2026-02-02 | De-esser before compressor | De-esser must come before compressor in signal chain to prevent amplifying sibilance | Professional audio quality following industry best practices |
| 2026-02-02 | Professional signal chain order | Gate → De-esser → EQ(corrective) → Compressor → EQ(creative) → Effects | Standard vocal processing chain used in studios and broadcasts |
| 2026-02-02 | EQ presets over raw frequency controls | Provide clarity/warmth/presence presets instead of raw frequency band adjustments | Better UX for non-technical users, custom mode for advanced users |
| 2026-02-02 | Graceful Pedalboard degradation | Effects check availability, log warnings, bypass processing if unavailable | Robust development without requiring Pedalboard installation |
| 2026-02-02 | MediaPipe landmark anchors for AR overlays | GLASSES use eyes 33/263, HAT uses forehead 10, MASK uses nose 1 | MediaPipe Face Mesh provides 478 landmarks with stable indices |
| 2026-02-02 | BGRA PNG format for overlays | PNG with alpha channel (4 channels) for transparency | Standard AR overlay format, widely supported |
| 2026-02-02 | Placeholder generation for missing overlay assets | Creates colored shapes when PNG files not found | Allows testing without actual asset files |
| 2026-02-02 | Helper functions avoid circular imports | _get_eye_distance() and _get_face_angle() at module level | AROverlay needs face calculations without FaceTracker dependency |
| 2026-02-02 | AROverlayManager with shared FaceTracker | Single face detection pass for multiple overlays | Efficient - one detection per frame regardless of overlay count |
| 2026-02-02 | MediaStreamTrack wrapper pattern for effects | AudioEffectsTrack/VideoEffectsTrack wrap source tracks with effect processing | Clean separation of concerns, effects toggleable mid-call |
| 2026-02-02 | Frame skipping for slow video processing | Return previous processed frame instead of blocking pipeline | Maintains smooth video even with heavy effects |
| 2026-02-02 | Performance monitoring for effects tracks | Warn at 15ms for audio, 33ms for video frame time | Clear feedback when effects are too computationally expensive |
| 2026-02-02 | Simple overlay system for screen sharing | Focus on watermark, border, cursor highlight only (per Phase 9 context) | Screen sharing doesn't need complex effects, performance matters |
| 2026-02-02 | Text and image watermark support | WatermarkOverlay can use text OR image with alpha channel | Flexibility for branding and attribution |
| 2026-02-02 | Position calculation with presets | Five position presets (top_left, top_right, bottom_left, bottom_right, center) | Common use cases covered, easy to extend |
| 2026-02-02 | Cursor position external to overlay | CursorHighlight requires set_cursor_position(x, y) to be called externally | mss library doesn't provide cursor position |
| 2026-02-02 | Lazy import in video_track.py | Import ScreenOverlayManager lazily to avoid circular dependencies | video_track imported early in call_service |
| 2026-02-02 | Convenience methods on ScreenShareTrack | set_watermark(), set_border(), set_cursor_highlight() methods | Simple API for common cases without manager |
| 2026-02-02 | ScreenOverlayManager preset system | create_preset() for common configurations (presentation, branded, minimal) | Quick setup for typical screen sharing scenarios |
| 2026-02-02 | Non-destructive voice message effects | Effects applied during playback, not baked into recordings | Preserves original audio, allows changing effects post-recording |
| 2026-02-02 | Unified effects package exports | Single __init__.py with all effect exports | Clean import path, easier frontend integration |
| 2026-02-02 | Package-level singleton getters | get_hardware_detector(), get_quality_adapter(), get_preset_manager() | Consistent access pattern, ensures single instance |
| 2026-02-02 | Feature flags for optional dependencies | AR_AVAILABLE and VIRTUAL_BACKGROUND_AVAILABLE flags | Graceful degradation when MediaPipe unavailable |
| 2026-02-02 | Dedicated favorites API methods | get/set/add/remove_favorite_presets() in API bridge | Common use case, simpler than generic settings |
| 2026-02-02 | Discord dark palette with softer grays | #1e1f22 primary instead of pure black | Less eye strain, Discord-inspired |
| 2026-02-02 | Blood red accent (#991b1b) | Darker, serious, elegant red for accents | Blue links (#00a8fc) like Discord, red for accents only |
| 2026-02-02 | Tailwind v4 @theme directive for design tokens | 33 CSS custom properties for entire design system | Enables bg-discord-*, text-discord-*, border-accent-* utility classes |
| 2026-02-02 | HTMLMotionProps for Button | Extends motion props instead of ButtonHTMLAttributes | Full Framer Motion support while maintaining native button props |
| 2026-02-02 | StatusBadge border matches parent bg | Uses border-discord-bg-secondary for visual separation | Clear status dots on avatars without floating appearance |
| 2026-02-02 | Variant/size pattern for Tailwind classes | variantStyles and sizeStyles objects for class composition | Scalable pattern for styled components with multiple variants |
| 2026-02-02 | AnimatePresence for channel list transitions | Slide animations x: -20 to 0 to 20 when switching sections | Smooth visual feedback for section changes |
| 2026-02-02 | UserStatus to StatusType mapping | Backend has 6 statuses, UI Badge only supports 4 | invisible/unknown/offline all map to 'offline' |
| 2026-02-02 | as const for framer-motion ease arrays | TypeScript requires const assertion for tuple types | Proper typing for transition objects |

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
- [x] Execute 04-06-PLAN.md (file transfer message integration)
- [x] Execute 04-08-PLAN.md (file transfer resume API & UI) - PHASE 4 COMPLETE
- [x] Execute 05-01-PLAN.md (audio device foundation)
- [x] Execute 05-02-PLAN.md (audio tracks)
- [x] Execute 05-04-PLAN.md (voice message recording)
- [x] Execute 05-03-PLAN.md (call service)
- [x] Execute 05-05-PLAN.md (voice integration)
- [x] Execute 05-06-PLAN.md (call UI components)
- [x] Execute 05-07-PLAN.md (voice message UI)
- [x] Execute 05-08-PLAN.md (integration testing) - PHASE 5 COMPLETE
- [x] Execute 06-01-PLAN.md (video track infrastructure)
- [x] Execute 06-02-PLAN.md (video track management)
- [x] Execute 06-03-PLAN.md (video signaling integration)
- [x] Execute 06-04-PLAN.md (video UI components)
- [x] Execute 06-05-PLAN.md (video display components)
- [x] Execute 06-06-PLAN.md (integration verification - deferred) - PHASE 6 COMPLETE
- [x] Execute 07-01-PLAN.md (group storage schema)
- [x] Execute 07-02-PLAN.md (Sender Keys encryption)
- [x] Execute 07-03-PLAN.md (Group service)
- [x] Execute 07-04-PLAN.md (Group messaging)
- [x] Execute 07-05-PLAN.md (WebRTC mesh topology)
- [x] Execute 07-06-PLAN.md (Group network integration)
- [x] Execute 07-07-PLAN.md (Group UI components)
- [x] Execute 07-08-PLAN.md (Group chat integration - verification deferred) - PHASE 7 COMPLETE
- [x] Execute 08-01-PLAN.md (Windows notification service)
- [x] Execute 08-02-PLAN.md (Auto-update service)
- [x] Execute 08-03-PLAN.md (Notification API integration)
- [x] Execute 08-04-PLAN.md (Update prompt UI)
- [x] Execute 08-05-PLAN.md (Verification checkpoint - deferred) - PHASE 8 COMPLETE - MILESTONE v1.0 COMPLETE
- [x] Execute 09-01-PLAN.md (hardware detection and quality adaptation)
- [x] Execute 09-02-PLAN.md (noise cancellation with DeepFilterNet3 and RNNoise)
- [x] Execute 09-03-PLAN.md (audio effects chain with Pedalboard)
- [x] Execute 09-04-PLAN.md (video processing core with MediaPipe)
- [x] Execute 09-05-PLAN.md (virtual background effects)
- [x] Execute 09-06-PLAN.md (creative video filters)
- [x] Execute 09-07-PLAN.md (AR face overlays)
- [x] Execute 09-08-PLAN.md (effects track integration)
- [x] Execute 09-09-PLAN.md (effect preset management)
- [x] Execute 09-11-PLAN.md (screen sharing overlays)
- [x] Execute 09-10-PLAN.md (voice message effects integration)
- [x] Execute 09-12-PLAN.md (final integration and API bridge) - PHASE 9 COMPLETE
- [x] Execute 10-01-PLAN.md (design system foundation) - Discord theme, red accents, dependencies
- [x] Execute 10-02-PLAN.md (UI primitives) - Button, Avatar, Badge, Tooltip components
- [x] Execute 10-03-PLAN.md (IconBar component) - Section navigation with icons
- [x] Execute 10-04-PLAN.md (ChannelList panel) - ContactList, GroupList, HomePanel with slide transitions

### Blockers

*None - milestone complete*

### Research Flags

*All research completed - milestone v1.0 achieved*

## Session Continuity

**Last session:** 2026-02-02 - Completed 10-04-PLAN.md

**What we just completed:**
- 10-04: Channel List Panel
  - ChannelList container with 240px width and AnimatePresence transitions
  - ContactList with Avatar, status indicators, and selection
  - GroupList with member counts and create/join buttons
  - HomePanel with app branding and welcome message
  - Slide animations (x: -20 to 0 to 20) for section changes
  - 3 tasks completed in 8 minutes
  - **Phase 10 Plan 04 COMPLETE**

**What's next:**
- Execute 10-05-PLAN.md (AppLayout assembly)
- Continue Phase 10 UI/UX Redesign plans 05-10
- ChannelList ready for integration with IconBar in AppLayout

**Open questions:**
- Human verification tests for Phase 6, 7, 8, 9 deferred - should be run before production
- Production deployment requires TUF repository initialization and root.json bundling
- AUMID may need Windows registration for notification callbacks in production
- AR overlay asset creation needed (currently using placeholders)
- Effect type registry needed for full AudioEffectChain metadata reconstruction

**Files created this session:**
- .planning/phases/09-audio-video-effects/09-01-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-02-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-03-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-04-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-05-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-06-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-07-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-08-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-09-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-10-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-11-SUMMARY.md
- .planning/phases/09-audio-video-effects/09-12-SUMMARY.md
- src/effects/hardware/__init__.py
- src/effects/hardware/gpu_detector.py
- src/effects/hardware/quality_adapter.py
- src/effects/hardware/resource_monitor.py
- src/effects/audio/__init__.py
- src/effects/audio/noise_cancellation.py
- src/effects/audio/voice_effects.py
- src/effects/audio/enhancement.py
- src/effects/audio/effect_chain.py
- src/effects/video/__init__.py
- src/effects/video/face_tracker.py
- src/effects/video/segmentation.py
- src/effects/video/virtual_background.py
- src/effects/video/beauty_filters.py
- src/effects/video/creative_filters.py
- src/effects/video/ar_overlays.py
- src/effects/video/screen_overlays.py
- src/effects/tracks/__init__.py
- src/effects/tracks/audio_effects_track.py
- src/effects/tracks/video_effects_track.py
- src/effects/presets/__init__.py
- src/effects/presets/built_in_presets.py
- src/effects/presets/preset_manager.py
- assets/overlays/.gitkeep
- assets/overlays/README.md

**Files modified this session:**
- requirements.txt (Phase 9 dependencies: deepfilternet, pyrnnoise, pedalboard, mediapipe, psutil)
- src/voice/call_service.py (effects track integration, preset management)
- src/voice/video_track.py (screen overlay integration)
- src/voice/voice_message.py (voice message effects integration)
- src/voice/models.py (effect metadata field)
- src/effects/__init__.py (unified package exports)
- src/effects/audio/__init__.py (voice message effects exports)
- src/effects/video/__init__.py (screen overlay exports)
- src/api/bridge.py (effect control methods)
- src/storage/settings.py (preset persistence)
- .planning/STATE.md

---

### Roadmap Evolution

- Phase 9 added: Audio & Video Effects (noise cancellation, voice effects, video filters, background blur, local AI processing)
- Phase 10 added: UI/UX Redesign (Discord-inspired layout, black-red theme, animations, production-grade polish)

---

*State initialized: 2026-01-30*
*Last updated: 2026-02-02 after completing 10-04*
