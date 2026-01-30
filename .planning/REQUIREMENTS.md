# Requirements: DiscordOpus

**Defined:** 2026-01-30
**Core Value:** Prywatna, w pełni szyfrowana komunikacja P2P bez zaufania do centralnego serwera

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Identity & Security

- [x] **IDEN-01**: User can generate cryptographic identity (Ed25519/X25519 key pair)
- [x] **IDEN-02**: User can view their public key as shareable ID
- [x] **IDEN-03**: User can set display name (local, not on server)
- [x] **IDEN-04**: User can verify contact's identity via fingerprint comparison
- [x] **IDEN-05**: User can export encrypted key backup with password
- [x] **IDEN-06**: User can import key backup to restore identity

### Encryption

- [x] **ENCR-01**: All messages are E2E encrypted (Signal Protocol)
- [ ] **ENCR-02**: All voice/video calls are E2E encrypted
- [ ] **ENCR-03**: All file transfers are E2E encrypted
- [x] **ENCR-04**: Keys stored securely using Windows DPAPI
- [x] **ENCR-05**: Perfect forward secrecy (Double Ratchet)

### Contacts

- [x] **CONT-01**: User can add contact by public key
- [x] **CONT-02**: User can view contact list with online status
- [x] **CONT-03**: User can remove contact
- [x] **CONT-04**: User can set nickname for contact (local)
- [x] **CONT-05**: User sees contact verification status (verified/unverified)

### Messaging

- [x] **MSG-01**: User can send text message to contact (1:1)
- [x] **MSG-02**: User can receive text message from contact
- [x] **MSG-03**: User can view message history (locally stored, encrypted)
- [x] **MSG-04**: User can send message to group
- [x] **MSG-05**: User can edit sent message
- [x] **MSG-06**: User can delete sent message
- [x] **MSG-07**: User sees typing indicator when contact is typing
- [x] **MSG-08**: User can add emoji reaction to message

### Voice Messages

- [ ] **VMSG-01**: User can record voice message
- [ ] **VMSG-02**: User can send voice message to contact/group
- [ ] **VMSG-03**: User can play received voice message
- [ ] **VMSG-04**: Voice messages are E2E encrypted

### Voice Calls

- [ ] **CALL-01**: User can start voice call with contact (1:1)
- [ ] **CALL-02**: User can receive incoming voice call
- [ ] **CALL-03**: User can mute/unmute microphone during call
- [ ] **CALL-04**: User can end call
- [ ] **CALL-05**: User can start group voice call (2-4 participants)
- [ ] **CALL-06**: User can join ongoing group call

### Video Calls

- [ ] **VID-01**: User can start video call with contact (1:1)
- [ ] **VID-02**: User can enable/disable camera during call
- [ ] **VID-03**: User can switch between cameras if multiple available
- [ ] **VID-04**: User can see remote participant's video

### Screen Sharing

- [ ] **SCRN-01**: User can share screen during call
- [ ] **SCRN-02**: User can select which screen/window to share
- [ ] **SCRN-03**: User can stop screen sharing
- [ ] **SCRN-04**: User can view shared screen from other participant

### File Transfer

- [x] **FILE-01**: User can send file to contact (no size limit)
- [x] **FILE-02**: User can see file transfer progress
- [x] **FILE-03**: User can cancel file transfer
- [x] **FILE-04**: User can resume interrupted file transfer
- [x] **FILE-05**: User can preview images/videos in chat
- [x] **FILE-06**: Files are E2E encrypted during transfer

### Groups

- [ ] **GRP-01**: User can create group with name
- [ ] **GRP-02**: User can generate invite link/code for group
- [ ] **GRP-03**: User can join group via invite link/code
- [ ] **GRP-04**: User can leave group
- [ ] **GRP-05**: User can see group member list
- [ ] **GRP-06**: Group creator can remove members

### Presence & Status

- [x] **PRES-01**: User can set status (online/away/busy/invisible)
- [x] **PRES-02**: User can see contacts' online status
- [x] **PRES-03**: Status synced via signaling server

### Notifications

- [ ] **NOTF-01**: User receives Windows notification for new message
- [ ] **NOTF-02**: User receives notification for incoming call
- [ ] **NOTF-03**: User can enable/disable notifications
- [ ] **NOTF-04**: Clicking notification opens relevant chat/call

### UI/UX

- [x] **UI-01**: Dark cosmic theme with starry animations
- [x] **UI-02**: Sidebar with contacts and groups
- [x] **UI-03**: Main chat panel with message history
- [x] **UI-04**: Settings panel for preferences
- [x] **UI-05**: Smooth transitions and animations

### Infrastructure

- [x] **INFR-01**: Signaling server for NAT traversal (WebSocket)
- [x] **INFR-02**: STUN server for ICE candidates
- [x] **INFR-03**: User presence system on signaling server
- [x] **INFR-04**: Secure signaling (WSS + authentication)

### Packaging

- [x] **PKG-01**: Single .exe installer/portable for Windows
- [x] **PKG-02**: App starts in reasonable time (<5 seconds)
- [ ] **PKG-03**: Auto-updater for new versions

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Groups

- **GRP-V2-01**: Role-based permissions (admin/moderator/member)
- **GRP-V2-02**: Persistent voice channels (drop-in rooms)
- **GRP-V2-03**: Group video calls (5+ participants via SFU)

### Multi-Device

- **DEV-01**: User can link additional device
- **DEV-02**: Message history syncs between devices
- **DEV-03**: Sessions sync between devices

### Advanced Features

- **ADV-01**: Custom emoji upload
- **ADV-02**: Message search
- **ADV-03**: Rich link previews with embeds
- **ADV-04**: Onion routing for IP privacy

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Phone/email registration | Conflicts with cryptographic identity model |
| Cloud message sync | Conflicts with local-only privacy model |
| TURN relay server | Cost/complexity trade-off, accept ~20-30% NAT failure |
| Mobile apps (iOS/Android) | Windows desktop only in v1 |
| Always-on read receipts | Privacy concern, optional only |
| SMS/MMS integration | Out of scope, pure P2P focus |
| Blockchain/crypto | Scope creep, not relevant |
| Light theme | Single dark cosmic theme for v1 |
| Web version | Desktop app only for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| IDEN-01 | Phase 1 | Complete |
| IDEN-02 | Phase 1 | Complete |
| IDEN-03 | Phase 1 | Complete |
| IDEN-04 | Phase 1 | Complete |
| IDEN-05 | Phase 1 | Complete |
| IDEN-06 | Phase 1 | Complete |
| ENCR-01 | Phase 3 | Complete |
| ENCR-02 | Phase 5 | Pending |
| ENCR-03 | Phase 4 | Pending |
| ENCR-04 | Phase 1 | Complete |
| ENCR-05 | Phase 3 | Complete |
| CONT-01 | Phase 2 | Complete |
| CONT-02 | Phase 2 | Complete |
| CONT-03 | Phase 2 | Complete |
| CONT-04 | Phase 2 | Complete |
| CONT-05 | Phase 2 | Complete |
| MSG-01 | Phase 3 | Complete |
| MSG-02 | Phase 3 | Complete |
| MSG-03 | Phase 3 | Complete |
| MSG-04 | Phase 3 | Complete |
| MSG-05 | Phase 3 | Complete |
| MSG-06 | Phase 3 | Complete |
| MSG-07 | Phase 3 | Complete |
| MSG-08 | Phase 3 | Complete |
| VMSG-01 | Phase 5 | Pending |
| VMSG-02 | Phase 5 | Pending |
| VMSG-03 | Phase 5 | Pending |
| VMSG-04 | Phase 5 | Pending |
| CALL-01 | Phase 5 | Pending |
| CALL-02 | Phase 5 | Pending |
| CALL-03 | Phase 5 | Pending |
| CALL-04 | Phase 5 | Pending |
| CALL-05 | Phase 7 | Pending |
| CALL-06 | Phase 7 | Pending |
| VID-01 | Phase 6 | Pending |
| VID-02 | Phase 6 | Pending |
| VID-03 | Phase 6 | Pending |
| VID-04 | Phase 6 | Pending |
| SCRN-01 | Phase 6 | Pending |
| SCRN-02 | Phase 6 | Pending |
| SCRN-03 | Phase 6 | Pending |
| SCRN-04 | Phase 6 | Pending |
| FILE-01 | Phase 4 | Complete |
| FILE-02 | Phase 4 | Complete |
| FILE-03 | Phase 4 | Complete |
| FILE-04 | Phase 4 | Complete |
| FILE-05 | Phase 4 | Complete |
| FILE-06 | Phase 4 | Complete |
| GRP-01 | Phase 7 | Pending |
| GRP-02 | Phase 7 | Pending |
| GRP-03 | Phase 7 | Pending |
| GRP-04 | Phase 7 | Pending |
| GRP-05 | Phase 7 | Pending |
| GRP-06 | Phase 7 | Pending |
| PRES-01 | Phase 2 | Complete |
| PRES-02 | Phase 2 | Complete |
| PRES-03 | Phase 2 | Complete |
| NOTF-01 | Phase 8 | Pending |
| NOTF-02 | Phase 8 | Pending |
| NOTF-03 | Phase 8 | Pending |
| NOTF-04 | Phase 8 | Pending |
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 1 | Complete |
| UI-03 | Phase 1 | Complete |
| UI-04 | Phase 1 | Complete |
| UI-05 | Phase 1 | Complete |
| INFR-01 | Phase 2 | Complete |
| INFR-02 | Phase 2 | Complete |
| INFR-03 | Phase 2 | Complete |
| INFR-04 | Phase 2 | Complete |
| PKG-01 | Phase 1 | Complete |
| PKG-02 | Phase 1 | Complete |
| PKG-03 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 73 total
- Mapped to phases: 73 (100%)
- Unmapped: 0

**Phase Distribution:**
- Phase 1: 14 requirements
- Phase 2: 12 requirements
- Phase 3: 10 requirements
- Phase 4: 7 requirements
- Phase 5: 9 requirements
- Phase 6: 8 requirements
- Phase 7: 8 requirements
- Phase 8: 5 requirements

---
*Requirements defined: 2026-01-30*
*Last updated: 2026-01-30 after Phase 3 completion*
