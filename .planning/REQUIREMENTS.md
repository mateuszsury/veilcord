# Requirements: DiscordOpus

**Defined:** 2026-01-30
**Core Value:** Prywatna, w pełni szyfrowana komunikacja P2P bez zaufania do centralnego serwera

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Identity & Security

- [ ] **IDEN-01**: User can generate cryptographic identity (Ed25519/X25519 key pair)
- [ ] **IDEN-02**: User can view their public key as shareable ID
- [ ] **IDEN-03**: User can set display name (local, not on server)
- [ ] **IDEN-04**: User can verify contact's identity via fingerprint comparison
- [ ] **IDEN-05**: User can export encrypted key backup with password
- [ ] **IDEN-06**: User can import key backup to restore identity

### Encryption

- [ ] **ENCR-01**: All messages are E2E encrypted (Signal Protocol)
- [ ] **ENCR-02**: All voice/video calls are E2E encrypted
- [ ] **ENCR-03**: All file transfers are E2E encrypted
- [ ] **ENCR-04**: Keys stored securely using Windows DPAPI
- [ ] **ENCR-05**: Perfect forward secrecy (Double Ratchet)

### Contacts

- [ ] **CONT-01**: User can add contact by public key
- [ ] **CONT-02**: User can view contact list with online status
- [ ] **CONT-03**: User can remove contact
- [ ] **CONT-04**: User can set nickname for contact (local)
- [ ] **CONT-05**: User sees contact verification status (verified/unverified)

### Messaging

- [ ] **MSG-01**: User can send text message to contact (1:1)
- [ ] **MSG-02**: User can receive text message from contact
- [ ] **MSG-03**: User can view message history (locally stored, encrypted)
- [ ] **MSG-04**: User can send message to group
- [ ] **MSG-05**: User can edit sent message
- [ ] **MSG-06**: User can delete sent message
- [ ] **MSG-07**: User sees typing indicator when contact is typing
- [ ] **MSG-08**: User can add emoji reaction to message

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

- [ ] **FILE-01**: User can send file to contact (no size limit)
- [ ] **FILE-02**: User can see file transfer progress
- [ ] **FILE-03**: User can cancel file transfer
- [ ] **FILE-04**: User can resume interrupted file transfer
- [ ] **FILE-05**: User can preview images/videos in chat
- [ ] **FILE-06**: Files are E2E encrypted during transfer

### Groups

- [ ] **GRP-01**: User can create group with name
- [ ] **GRP-02**: User can generate invite link/code for group
- [ ] **GRP-03**: User can join group via invite link/code
- [ ] **GRP-04**: User can leave group
- [ ] **GRP-05**: User can see group member list
- [ ] **GRP-06**: Group creator can remove members

### Presence & Status

- [ ] **PRES-01**: User can set status (online/away/busy/invisible)
- [ ] **PRES-02**: User can see contacts' online status
- [ ] **PRES-03**: Status synced via signaling server

### Notifications

- [ ] **NOTF-01**: User receives Windows notification for new message
- [ ] **NOTF-02**: User receives notification for incoming call
- [ ] **NOTF-03**: User can enable/disable notifications
- [ ] **NOTF-04**: Clicking notification opens relevant chat/call

### UI/UX

- [ ] **UI-01**: Dark cosmic theme with starry animations
- [ ] **UI-02**: Sidebar with contacts and groups
- [ ] **UI-03**: Main chat panel with message history
- [ ] **UI-04**: Settings panel for preferences
- [ ] **UI-05**: Smooth transitions and animations

### Infrastructure

- [ ] **INFR-01**: Signaling server for NAT traversal (WebSocket)
- [ ] **INFR-02**: STUN server for ICE candidates
- [ ] **INFR-03**: User presence system on signaling server
- [ ] **INFR-04**: Secure signaling (WSS + authentication)

### Packaging

- [ ] **PKG-01**: Single .exe installer/portable for Windows
- [ ] **PKG-02**: App starts in reasonable time (<5 seconds)
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
| IDEN-01 | TBD | Pending |
| IDEN-02 | TBD | Pending |
| ... | ... | ... |

**Coverage:**
- v1 requirements: 58 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 58

---
*Requirements defined: 2026-01-30*
*Last updated: 2026-01-30 after initial definition*
