# Roadmap: DiscordOpus

**Created:** 2026-01-30
**Phases:** 8
**Requirements:** 73 v1

## Overview

| Phase | Name | Goal | Requirements |
|-------|------|------|--------------|
| 1 | Cryptographic Foundation & Packaging | Users can generate secure cryptographic identity and use basic UI | 14 |
| 2 | Signaling Infrastructure & Presence | Users can discover contacts and see online status | 12 |
| 3 | P2P Text Messaging | Users can exchange E2E encrypted text messages | 10 |
| 4 | File Transfer | Users can share files of any size with E2E encryption | 7 |
| 5 | Voice Calls (1-on-1) | Users can make encrypted voice calls and send voice messages | 9 |
| 6 | Video & Screen Sharing | Users can make video calls and share screens | 8 |
| 7 | Group Features | Users can create groups and participate in group calls | 8 |
| 8 | Notifications & Polish | Users receive system notifications and auto-updates | 5 |

## Phase 1: Cryptographic Foundation & Packaging

**Goal:** Users can generate secure cryptographic identity, manage contacts locally, and experience the UI in a packaged .exe application.

**Requirements:**
- IDEN-01, IDEN-02, IDEN-03, IDEN-04, IDEN-05, IDEN-06
- ENCR-04
- PKG-01, PKG-02
- UI-01, UI-02, UI-03, UI-04, UI-05

**Plans:** 7 plans

Plans:
- [x] 01-01-PLAN.md - Project scaffolding (Python + React)
- [x] 01-02-PLAN.md - Secure storage foundation (DPAPI + SQLCipher)
- [x] 01-03-PLAN.md - Cryptographic identity (Ed25519/X25519)
- [x] 01-04-PLAN.md - Key backup and restore (Argon2id)
- [x] 01-05-PLAN.md - React UI shell (theme + layout)
- [x] 01-06-PLAN.md - Identity and contact management UI
- [x] 01-07-PLAN.md - PyInstaller packaging and verification

**Status:** Complete (2026-01-30)

**Success Criteria:**
1. User downloads single .exe file and launches app within 5 seconds
2. User generates cryptographic identity (Ed25519/X25519 keys) on first launch
3. User views their public key as shareable ID in settings
4. User sets display name that persists across app restarts
5. User adds contact by pasting public key
6. User exports encrypted key backup with password
7. User imports key backup to restore identity
8. User verifies contact's identity via fingerprint comparison
9. Keys are stored securely using Windows DPAPI (never plaintext)
10. UI displays dark cosmic theme with starry animations
11. Sidebar shows contacts list (empty until Phase 2 connection)
12. Main panel ready for chat display (Phase 3)
13. Settings panel accessible for identity management

**Dependencies:** None

---

## Phase 2: Signaling Infrastructure & Presence

**Goal:** Users can discover contacts, see online/offline status, and establish signaling connection with server.

**Requirements:**
- INFR-01, INFR-02, INFR-03, INFR-04
- PRES-01, PRES-02, PRES-03
- CONT-01, CONT-02, CONT-03, CONT-04, CONT-05

**Plans:** 5 plans

Plans:
- [x] 02-01-PLAN.md - WebSocket signaling client with auto-reconnect and Ed25519 auth
- [x] 02-02-PLAN.md - Presence state management and settings storage
- [x] 02-03-PLAN.md - API bridge integration and network service orchestration
- [x] 02-04-PLAN.md - Frontend presence UI (status selector, contact presence)
- [x] 02-05-PLAN.md - Visual verification checkpoint

**Status:** Complete (2026-01-30)

**Success Criteria:**
1. User connects to signaling server via WSS on app launch
2. User authenticates to signaling server with cryptographic signature
3. User sets status (online/away/busy/invisible) and it persists
4. User sees contacts' online status update in real-time (within 5 seconds)
5. User adds contact by public key and sees if they're online
6. User removes contact and they disappear from list
7. User sets nickname for contact (local, not shared)
8. User sees contact verification status (verified/unverified badge)
9. Signaling server relays presence without seeing message content
10. Connection recovers automatically after network interruption
11. STUN server provides ICE candidates for NAT traversal

**Dependencies:** Phase 1 (cryptographic identity required for authentication)

---

## Phase 3: P2P Text Messaging

**Goal:** Users can exchange E2E encrypted text messages over P2P connections with persistent history.

**Requirements:**
- MSG-01, MSG-02, MSG-03, MSG-04, MSG-05, MSG-06, MSG-07, MSG-08
- ENCR-01, ENCR-05

**Plans:** 7 plans

Plans:
- [x] 03-01-PLAN.md - Database schema extension for messages, reactions, and Signal sessions
- [x] 03-02-PLAN.md - Signal Protocol encryption layer (X3DH + Double Ratchet)
- [x] 03-03-PLAN.md - WebRTC peer connection manager (aiortc data channels)
- [x] 03-04-PLAN.md - P2P messaging integration (network service + API bridge)
- [x] 03-05-PLAN.md - Chat UI core (message list, input, stores)
- [x] 03-06-PLAN.md - Enhanced features (typing, reactions, edit, delete)
- [x] 03-07-PLAN.md - Layout integration and verification checkpoint

**Status:** Complete (2026-01-30)

**Success Criteria:**
1. User sends text message to online contact and it arrives within 2 seconds
2. User receives text message from contact with notification
3. Messages are E2E encrypted using Signal Protocol (Double Ratchet)
4. User views message history that persists after app restart
5. User edits sent message and recipient sees update
6. User deletes sent message and it's removed from both sides
7. User sees typing indicator when contact is typing (live feedback)
8. User adds emoji reaction to message and contact sees it
9. User sends message to group (Phase 7 feature, foundation here)
10. Messages stored locally in encrypted database (SQLCipher)
11. P2P connection established via WebRTC data channel with STUN (no TURN)
12. Connection diagnostics show NAT type and ICE candidate status
13. User sees clear error message if P2P connection fails (symmetric NAT)

**Dependencies:** Phase 2 (signaling required for WebRTC connection establishment)

**Research Notes:** Research completed (03-RESEARCH.md). Using aiortc for WebRTC, python-doubleratchet + python-x3dh for Signal Protocol.

---

## Phase 4: File Transfer

**Goal:** Users can share files of any size with E2E encryption, progress tracking, and resume capability.

**Requirements:**
- FILE-01, FILE-02, FILE-03, FILE-04, FILE-05, FILE-06

**Plans:** 8 plans

Plans:
- [x] 04-01-PLAN.md - Database schema and encrypted file storage layer
- [x] 04-02-PLAN.md - File chunker and sender with backpressure control
- [x] 04-03-PLAN.md - File receiver and transfer service orchestration
- [x] 04-04-PLAN.md - NetworkService integration and API bridge
- [x] 04-05-PLAN.md - Image and video preview generation
- [x] 04-06-PLAN.md - Message integration and E2E verification checkpoint
- [x] 04-07-PLAN.md - Frontend UI components (store, upload, progress)
- [x] 04-08-PLAN.md - Gap closure: Resume transfer API and UI (from verification)

**Status:** Complete (2026-01-30)

**Success Criteria:**
1. User sends file to contact (up to 5GB tested) and it transfers successfully
2. User sees file transfer progress (percentage, speed, ETA)
3. User cancels file transfer mid-flight and both sides stop cleanly
4. User resumes interrupted file transfer from last checkpoint
5. User previews images in chat without downloading separately
6. User previews videos in chat with inline playback
7. Files are E2E encrypted during transfer (on top of WebRTC DTLS)
8. File chunks transmitted over existing WebRTC data channel (no new connection)
9. Transferred files stored encrypted locally until user opens them
10. Large file transfers don't block message sending (concurrent streams)

**Dependencies:** Phase 3 (WebRTC data channel established for file chunks)

**Research Notes:** Research completed (04-RESEARCH.md). Using 16KB chunks for cross-browser compatibility, backpressure via bufferedAmountLowThreshold, Pillow for image thumbnails, ffmpeg for video thumbnails.

**Verification Notes:** 04-VERIFICATION.md passed on re-verification after gap closure plan 04-08. All 10 success criteria verified, 6/6 requirements satisfied.

---

## Phase 5: Voice Calls (1-on-1)

**Goal:** Users can make encrypted voice calls with acceptable latency and send voice messages.

**Requirements:**
- CALL-01, CALL-02, CALL-03, CALL-04
- VMSG-01, VMSG-02, VMSG-03, VMSG-04
- ENCR-02

**Success Criteria:**
1. User starts voice call with online contact and hears ringing
2. User receives incoming call notification and can accept/reject
3. User mutes/unmutes microphone during call with visual feedback
4. User ends call cleanly and resources are released
5. Voice call audio quality is clear (Opus codec, <100ms latency on good networks)
6. Voice calls are E2E encrypted via WebRTC SRTP + Signal Protocol
7. User records voice message (up to 5 minutes tested)
8. User sends voice message to contact and it appears in chat
9. User plays received voice message with playback controls
10. Voice messages are E2E encrypted before sending
11. Audio devices (mic/speaker) selectable in settings
12. Call continues seamlessly if contact switches network (mobile to WiFi)

**Dependencies:** Phase 3 (P2P connection established before media streams)

**Research Notes:** HIGH priority research needed for aiortc audio codec interop with browser peers and cross-platform audio handling.

---

## Phase 6: Video & Screen Sharing

**Goal:** Users can make video calls and share screens during calls.

**Requirements:**
- VID-01, VID-02, VID-03, VID-04
- SCRN-01, SCRN-02, SCRN-03, SCRN-04

**Success Criteria:**
1. User starts video call and sees own camera preview
2. User enables/disables camera during call and remote participant sees change
3. User switches between cameras if multiple available
4. User sees remote participant's video stream in real-time
5. Video quality adapts to network conditions (VP8/H.264 codec)
6. User shares screen during call and remote participant sees it
7. User selects specific screen or window to share (privacy)
8. User stops screen sharing and returns to camera view
9. Remote participant views shared screen with acceptable frame rate (10+ fps)
10. Screen sharing works during voice-only call (adds video stream)
11. Video calls maintain E2E encryption (SRTP)

**Dependencies:** Phase 5 (audio pipeline established, video adds media track)

**Research Notes:** Cross-browser compatibility testing needed (Safari SDP differences). Screen capture APIs vary by OS.

---

## Phase 7: Group Features

**Goal:** Users can create groups, exchange group messages, and participate in group voice calls (2-4 participants via mesh).

**Requirements:**
- GRP-01, GRP-02, GRP-03, GRP-04, GRP-05, GRP-06
- CALL-05, CALL-06

**Success Criteria:**
1. User creates group with name and it appears in sidebar
2. User generates invite link/code for group
3. User joins group via invite link/code and sees group chat
4. User leaves group and it's removed from their sidebar
5. User sees group member list with online status
6. Group creator removes member and they're ejected from group
7. User sends message to group and all members receive it
8. Group messages are E2E encrypted using Sender Keys protocol
9. User starts group voice call (2-4 participants tested)
10. User joins ongoing group call and hears all participants
11. Group call uses mesh topology (each peer connects to all others)
12. Group call quality degrades gracefully at 4 participants (bandwidth limit)
13. App displays warning when creating 5+ member group (mesh limit)

**Dependencies:** Phase 5 (1-on-1 calls proven before N-way mesh)

**Research Notes:** HIGH complexity. Sender Keys protocol implementation and WebRTC mesh optimization need dedicated research before planning.

---

## Phase 8: Notifications & Polish

**Goal:** Users receive Windows notifications for messages/calls and get automatic updates for new versions.

**Requirements:**
- NOTF-01, NOTF-02, NOTF-03, NOTF-04
- PKG-03

**Success Criteria:**
1. User receives Windows notification when new message arrives (app in background)
2. User receives notification for incoming call with accept/reject actions
3. User enables/disables notifications in settings
4. User clicks notification and app opens to relevant chat/call
5. Notifications respect Windows Do Not Disturb mode
6. App checks for updates on launch (Tufup auto-updater)
7. User notified when update available with changelog
8. User installs update and app restarts seamlessly
9. Updates are cryptographically signed and verified before install
10. App packaged with Nuitka for production (lower AV false positives)

**Dependencies:** Phase 7 (all core features complete, notifications are final polish)

**Research Notes:** Tufup integration for secure updates. Windows notification API usage straightforward.

---

## Coverage Validation

| Category | Total | Mapped | Coverage |
|----------|-------|--------|----------|
| Identity & Security | 6 | 6 | 100% |
| Encryption | 5 | 5 | 100% |
| Contacts | 5 | 5 | 100% |
| Messaging | 8 | 8 | 100% |
| Voice Messages | 4 | 4 | 100% |
| Voice Calls | 6 | 6 | 100% |
| Video Calls | 4 | 4 | 100% |
| Screen Sharing | 4 | 4 | 100% |
| File Transfer | 6 | 6 | 100% |
| Groups | 6 | 6 | 100% |
| Presence & Status | 3 | 3 | 100% |
| Notifications | 4 | 4 | 100% |
| UI/UX | 5 | 5 | 100% |
| Infrastructure | 4 | 4 | 100% |
| Packaging | 3 | 3 | 100% |

**Total:** 73/73 requirements mapped (100%)

---

## Phase Dependencies Graph

```
Phase 1: Foundation
   |
   v
Phase 2: Signaling & Presence
   |
   v
Phase 3: Text Messaging ----------+
   |                              |
   v                              |
Phase 4: File Transfer            |
                                  |
Phase 5: Voice Calls <------------+
   |
   v
Phase 6: Video & Screen Sharing
   |
   v
Phase 7: Group Features
   |
   v
Phase 8: Notifications & Polish
```

---

## Research Flags Summary

**Phases requiring deeper research during planning:**

- **Phase 3**: aiortc data channel reliability, offline message store-and-forward (MEDIUM complexity) - RESEARCH COMPLETE
- **Phase 4**: File chunking and resume protocol (MEDIUM complexity) - RESEARCH COMPLETE
- **Phase 5**: aiortc audio codec interop with browsers, cross-platform audio (HIGH priority)
- **Phase 6**: Cross-browser WebRTC compatibility, screen capture APIs (MEDIUM complexity)
- **Phase 7**: Sender Keys protocol, WebRTC mesh optimization (HIGH complexity, consider research-phase)

**Phases with standard patterns (skip research-phase):**

- **Phase 1**: SQLCipher, DPAPI, PyInstaller well-documented
- **Phase 2**: WebSocket server, JWT auth, STUN setup well-documented
- **Phase 8**: Tufup and Windows notifications well-documented

---

*Roadmap created: 2026-01-30*
*Last updated: 2026-01-30*
