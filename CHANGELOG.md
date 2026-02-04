# Changelog

All notable changes to Veilcord will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Future features and improvements will be listed here

## [1.0.0] - 2026-02-04

### Added

**Phase 1: Cryptographic Foundation & Packaging**
- Ed25519 and X25519 cryptographic identity generation
- SQLCipher encrypted local database with AES-256
- Windows DPAPI key protection for encryption keys
- Argon2id password-based backup system (RFC 9106 desktop parameters)
- React 19 frontend with Vite build system
- PyInstaller single-executable packaging
- Python-JavaScript bridge via pywebview

**Phase 2: Signaling Infrastructure & Presence**
- WebSocket signaling client for peer discovery
- Presence system with online/offline/away/busy statuses
- Contact management with public key storage
- Real-time presence updates across connected peers

**Phase 3: P2P Text Messaging**
- Signal Protocol end-to-end encryption (Double Ratchet + X3DH)
- WebRTC data channels for peer-to-peer messaging
- Message reactions and replies
- Typing indicators
- Message editing and deletion (soft delete)
- Encrypted message storage in SQLCipher database

**Phase 4: File Transfer**
- Encrypted file transfer over WebRTC data channels
- Chunked transfer with backpressure control (16KB chunks)
- Image and video thumbnail generation
- File storage with 100KB BLOB/filesystem threshold
- Transfer progress tracking and pause/resume support
- Support for images, videos, documents, and audio files

**Phase 5: Voice Calls (1-on-1)**
- WebRTC voice calls with Opus codec (50 kbps)
- Audio device enumeration and selection
- Microphone mute/unmute
- Voice message recording with waveform visualization
- Ogg Opus audio file format for voice messages
- Call state management (ringing, active, reconnecting, ended)

**Phase 6: Video & Screen Sharing**
- WebRTC video calls with H.264 codec
- Camera device enumeration and selection
- Video enable/disable during calls
- Screen sharing with display selection
- Real-time video frame transmission (30 FPS, JPEG 70%)
- Video renegotiation support for mid-call video changes

**Phase 7: Group Features**
- Encrypted group messaging with Sender Keys
- Group creation and member management
- Admin-only invite code generation (veilcord://join/ URL scheme)
- Mesh topology for group voice/video calls (up to 8 participants)
- Group member key rotation on member removal
- Forward secrecy for group messages

**Phase 8: Notifications & Polish**
- Windows toast notifications with Action Center integration
- Interactive notification callbacks (open chat, accept/reject calls)
- Secure auto-updater with TUF cryptographic verification
- Update prompt UI with download progress
- Custom AUMID for notification identification

**Phase 9: Audio & Video Effects**
- Hardware detection and GPU capability checking (CUDA, OpenCL)
- Automatic quality adaptation based on hardware
- DeepFilterNet3 AI-powered noise cancellation (GPU-accelerated)
- RNNoise lightweight noise suppression (CPU fallback)
- Professional audio enhancement chain (compressor, EQ, gate, de-esser)
- Voice effects: pitch shifting, reverb, chorus, distortion
- MediaPipe face tracking and segmentation
- Virtual backgrounds: blur, static images, animated backgrounds
- Beauty filters: skin smoothing, brightening, sharpening
- Creative video filters: grayscale, sepia, vignette, edge detection
- AR face overlays: glasses, hats, masks (landmark-anchored)
- Screen sharing overlays: watermarks, borders, cursor highlighting
- Effect preset system with built-in and custom presets
- Non-destructive voice message effects (applied during playback)

**Phase 10: UI/UX Redesign**
- Discord-inspired dark theme with blood red accents (#991b1b)
- Three-column layout with IconBar, ChannelList, and MainPanel
- Tailwind CSS v4 design system with 33 CSS custom properties
- Framer Motion animations for smooth transitions
- Button, Avatar, Badge, and Tooltip UI primitives
- Virtual scrolling with TanStack Virtual (1000+ message support)
- Discord-style message layout (no bubbles, flat design)
- Settings panel with two-column navigation
- Call UI with expandable overlay (audio/video modes)
- Effects panel for real-time audio/video effect control

**Phase 11: Branding & Release**
- Application rebranded from DiscordOpus to Veilcord
- Veilcord logo and multi-resolution Windows icon
- Comprehensive README with installation and security documentation
- Dual license (Personal free, Commercial paid)
- Contributing guidelines and Code of Conduct
- GitHub repository preparation

### Security

- Signal Protocol with Double Ratchet for perfect forward secrecy
- X3DH key agreement with ephemeral key exchange
- SQLCipher AES-256 database encryption
- Windows DPAPI key protection (no master password required)
- Argon2id password hashing for backup encryption (64MB, 3 iterations)
- Sender Keys for efficient group encryption with forward secrecy
- Domain-separated HKDF for key derivation
- Ed25519 signature verification before decryption
- Message sequence numbers to prevent replay attacks
- Separate Ed25519 (signing) and X25519 (encryption) keypairs

### Technical Stack

**Backend (Python 3.13+)**
- cryptography 46.0.4
- DoubleRatchet 1.3.0 / X3DH 1.1.0
- aiortc 1.14.0 (WebRTC)
- websockets 15.0+
- sqlcipher3 0.6.2+
- pywin32 306+
- sounddevice 0.5.0+ / PyOgg 0.6.14+
- opencv-python 4.0+ / mss 9.0+
- DeepFilterNet 0.5.6+ / RNNoise 0.4.3+ / Pedalboard 0.9.21+
- MediaPipe 0.10.32+
- pywebview 6.1+ / PyInstaller 6.18.0+

**Frontend**
- React 19 / Vite 6
- TypeScript 5.7+
- Tailwind CSS 4.1
- Framer Motion 12
- Zustand 5 (state management)
- TanStack Virtual 3.11 (virtual scrolling)

### Known Limitations

- **Windows Only**: Currently supports Windows 10/11 only
- **STUN Only**: No TURN relay, ~20-30% connection failure rate with symmetric NAT
- **Mesh Topology**: Group calls limited to 8 participants (mesh doesn't scale beyond this)
- **Manual Key Verification**: Users must manually verify contact public keys
- **Signaling Server Dependency**: Central server required for initial peer discovery
- **GPU Acceleration**: Some effects require CUDA/OpenCL-capable GPU for optimal performance

### Changed

- N/A (initial release)

### Deprecated

- N/A (initial release)

### Removed

- N/A (initial release)

### Fixed

- N/A (initial release)

## [0.9.0] - Development

Internal development versions (not released publicly).

---

[Unreleased]: https://github.com/mateuszsury/veilcord/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mateuszsury/veilcord/releases/tag/v1.0.0
