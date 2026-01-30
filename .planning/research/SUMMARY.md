# Project Research Summary

**Project:** DiscordOpus
**Domain:** P2P Privacy-Focused Communication App (Discord-like with E2E encryption)
**Researched:** 2026-01-30
**Confidence:** HIGH

## Executive Summary

DiscordOpus is a privacy-first P2P communication application combining Discord's rich communication features (voice, video, group channels) with Signal-level encryption and cryptographic identity. The recommended approach is a layered architecture: Python backend (aiortc for WebRTC, Signal Protocol for E2E encryption, SQLCipher for encrypted storage), React frontend in pywebview for UI, minimal untrusted signaling server for connection establishment, and Nuitka packaging for production distribution. This architecture separates cryptographic operations (trusted, client-side) from signaling infrastructure (untrusted, server-side), following patterns proven by Signal, Session, and Jami.

The core technical challenge is balancing Discord-like feature richness with P2P constraints. WebRTC mesh topology works well for 2-4 participant groups but degrades beyond that, requiring eventual SFU architecture for larger groups. The deliberate "no TURN relay" decision trades 20-30% connection failure rate (symmetric NAT scenarios) for zero ongoing infrastructure costs. This architectural constraint must be clearly communicated to users with robust connection diagnostics.

Critical risks center on three areas: NAT traversal limitations without TURN (test across real networks early, implement clear error messages), desktop key management security (use Windows DPAPI from day one, never store keys in plaintext), and PyInstaller packaging pitfalls (avoid --onefile mode, test frozen app thoroughly). The Signal Protocol implementation provides strong cryptographic guarantees, but desktop apps lack mobile platform sandboxing, making secure key storage paramount. Early testing across restrictive networks (corporate VPNs, mobile hotspots, symmetric NAT) is essential to validate the no-TURN architecture decision.

## Key Findings

### Recommended Stack

Modern P2P communication stacks in 2026 converge on WebRTC for transport, Signal Protocol for encryption, and local-first storage. Python provides excellent cryptography libraries and WebRTC support via aiortc, while React offers a mature UI ecosystem with good dark theme support (shadcn/ui). PyWebView bridges the two using native OS webviews (Edge WebView2 on Windows) instead of bundling Chromium like Electron, reducing bundle size 10x.

**Core technologies:**
- **Python 3.11/3.12 + aiortc 1.14.0**: WebRTC implementation with asyncio support, handles audio (Opus), video (VP8/H.264), and data channels with built-in DTLS encryption
- **Signal Protocol (X3DH 1.3.0 + DoubleRatchet 1.3.0)**: Industry-standard E2E encryption with perfect forward secrecy, used by Signal/WhatsApp/Facebook Messenger
- **React 19 + Vite 7 + TanStack Query + Zustand**: Modern frontend stack, Vite replaces deprecated Create React App, TanStack Query for server state, Zustand for client state
- **PyWebView 6.1**: Native webview container using Edge WebView2 on Windows, lightweight alternative to Electron
- **Nuitka**: Python-to-C compiler for production releases, lower antivirus false positives than PyInstaller, faster startup times
- **SQLCipher**: Encrypted SQLite with transparent 256-bit AES encryption for local message history and key storage
- **aiohttp 3.13.3**: Async HTTP server for signaling server with built-in WebSocket support

**Critical version notes:**
- Use Python 3.11 or 3.12 for best performance (3.10-3.14 supported)
- Nuitka for production distribution, PyInstaller 6.18.0 for development only (high AV false positive rate)
- Vite 7.3.1 stable (Vite 8 in beta, avoid for production)
- Tailwind CSS v4 with OKLCH colors for better dark mode accessibility

### Expected Features

Privacy-focused messengers in 2026 face a clear dichotomy: users expect both feature parity with mainstream apps (Discord/Telegram) and privacy guarantees of Signal/Session. DiscordOpus's positioning combines Discord's communication richness with Session's privacy model.

**Must have (table stakes):**
- E2E encryption (text, voice, video, files) with perfect forward secrecy
- 1-on-1 messaging, voice calls, video calls, file sharing
- Group text chat and group voice calls
- Cryptographic identity (no phone/email requirement)
- Contact verification (prevent MITM attacks)
- Message history persistence with local encrypted storage
- Offline message delivery (store-and-forward)
- Basic UX features (typing indicators, read receipts, emoji reactions)

**Should have (competitive):**
- Persistent group rooms (Discord's server/channel model)
- Metadata minimization (unlike Signal which collects connection graphs)
- Local-first architecture (data stays on user devices)
- Simplified key management UX (hide crypto complexity from users)
- Voice channels (always-on drop-in rooms vs call-based paradigm)
- Multi-device support (device linking without central server)

**Defer (v2+):**
- Onion routing for IP privacy (Session feature, adds significant complexity)
- Message editing/deletion (requires distributed consensus)
- Rich media embeds (UX polish, not essential)
- Screen sharing (Medium-High complexity, defer to Phase 2)
- Group video calls (resource-intensive, requires SFU for 5+ participants)

**Anti-features (do not build):**
- Phone number requirement (de-anonymizes users)
- Cloud message sync (central server = privacy risk)
- Always-on read receipts and last seen (metadata leak)
- SMS/MMS integration (Signal removed in 2023, fragmentation risk)
- Blockchain/cryptocurrency integration (scope creep)

### Architecture Approach

P2P communication systems employ a layered architecture separating untrusted signaling infrastructure from trusted client-side cryptographic operations. The core pattern: minimal signaling server (untrusted, relay only) + WebRTC P2P layer (DTLS/SRTP encrypted) + client-side E2E encryption (Signal Protocol) + local encrypted storage (SQLCipher). This creates a zero-trust model where the signaling server cannot access message content or encryption keys.

**Major components:**
1. **Client Application (Python + React + PyWebView)** — Cryptographic operations (Signal Protocol, key management), WebRTC orchestration (aiortc), local storage (SQLCipher), UI rendering (React in webview). Python backend handles all security-critical operations; React frontend only displays UI.
2. **Signaling Server (aiohttp WebSocket)** — Minimal relay for SDP/ICE exchange during connection establishment. Does NOT see message content, encryption keys, or media streams. Zero-trust design: assume server is compromised.
3. **P2P Layer (WebRTC via aiortc)** — Direct peer-to-peer connections for media (audio/video via SRTP) and data (text/files via DTLS data channels). ICE with STUN for NAT traversal (no TURN relay per requirements). Mesh topology for 2-4 participants, SFU needed for 5+ in group calls.
4. **Encryption Layer (Signal Protocol)** — E2E encryption on top of WebRTC transport encryption. Identity keys (long-term, Ed25519/X25519), prekeys (medium-term, rotated weekly), session keys (ephemeral, one per message via Double Ratchet). Provides forward secrecy and post-compromise recovery.
5. **Storage Layer (SQLCipher)** — Encrypted SQLite database for messages, contacts, sessions, keys. 256-bit AES encryption, key derived from user passphrase or Windows DPAPI. Entire database encrypted at rest, safe to backup.

**Critical architectural boundaries:**
- **Security boundary (client vs signaling server)**: All encryption client-side, server is untrusted relay
- **Privacy boundary (network vs local storage)**: Plaintext never leaves encrypted client storage
- **Crypto boundary (WebRTC vs E2E)**: WebRTC DTLS/SRTP insufficient alone, need Signal Protocol layer
- **Process boundary (Python vs React)**: All crypto operations in Python, React only handles UI
- **Network boundary (P2P vs server)**: Media/data flows P2P, NOT through server (except signaling)

### Critical Pitfalls

1. **NAT traversal failures without TURN relay** — Accepting "no TURN" means accepting 20-30% connection failure rate, with 100% failure when both peers are behind symmetric NAT (common in mobile tethering, corporate networks). Must implement clear connection diagnostics, user-friendly error messages, and test extensively across real networks (corporate VPNs, mobile hotspots). Consider fallback: allow optional TURN server configuration for advanced users.

2. **Insecure key storage on desktop** — Desktop apps lack mobile platform sandboxing. Keys stored in plaintext files, unencrypted databases, or hardcoded in source compromise entire E2E security model. Use Windows DPAPI or CNG Key Storage from day one. Never store keys in %APPDATA% as plaintext, never hardcode default keys. Implement key backup mechanism to prevent data loss on Windows password reset (DPAPI keys are password-derived).

3. **PyInstaller --onefile mode pitfalls** — Using --onefile creates 200MB+ startup delays (5-10 seconds unpacking to temp), symbolic link failures on some filesystems, and complicates updates. Use --onedir mode instead: faster startup, better compression as .zip, easier updates. Nuitka for production releases (lower AV false positives), PyInstaller for development only.

4. **Testing only in local development** — WebRTC connections always succeed on localhost/LAN, giving false confidence. App fails in production with real NAT, firewalls, and network restrictions. Test one peer on WiFi + another on mobile data, one behind corporate VPN, use cloud VMs in different regions. Monitor ICE candidate types (need "srflx" from STUN, not just "host").

5. **Weak signaling server authentication** — Unauthenticated WebSocket signaling allows attackers to intercept/inject SDP offers, impersonate users, hijack calls. Even though WebRTC media is encrypted, compromised signaling redirects connections. Use WSS (not WS), implement JWT token-based authentication, sign SDP offers/answers with user's private key for verification.

## Implications for Roadmap

Based on research, suggested phase structure follows dependency order: foundation (local crypto/storage) → signaling infrastructure → P2P messaging → voice/video → group features → privacy enhancements. This order mitigates risks early (test packaging, key management, NAT traversal) before adding complexity.

### Phase 1: Cryptographic Foundation (Local-First)
**Rationale:** Establish data model, key management, and storage patterns before network dependencies. Tests Python-React integration and PyInstaller packaging early (both high-risk areas). No network dependencies means can develop offline.

**Delivers:** Single .exe that generates cryptographic identity (Ed25519/X25519 keys), stores contacts locally in encrypted database, displays UI with working Python-React bridge.

**Addresses features:**
- Cryptographic identity (no phone/email)
- Local encrypted storage (SQLCipher)
- Contact management
- Basic key generation and storage (with DPAPI)

**Avoids pitfalls:**
- Insecure key storage (implement DPAPI from day one)
- PyInstaller packaging issues (test --onedir early, validate frozen app)
- Weak key generation (use cryptography library, not random module)

**Tech stack elements:**
- Python 3.11/3.12 + cryptography 46.0.4
- SQLCipher (via pysqlcipher3)
- React 19 + Vite 7 + Zustand
- PyWebView 6.1 + PyInstaller (development mode)

### Phase 2: Signaling Infrastructure
**Rationale:** Needed before P2P connections can be established. Simplest network component (stateless relay), testable without WebRTC complexity. Establishes security patterns (WSS, authentication) for all future network operations.

**Delivers:** Minimal aiohttp signaling server, WebSocket client in Python backend, user presence system (online/offline), user discovery by public key hash.

**Addresses features:**
- User presence (online/offline status)
- Contact discovery (by cryptographic ID)
- Connection establishment protocol

**Avoids pitfalls:**
- Weak signaling authentication (implement WSS + JWT from start)
- Free STUN server unreliability (host own STUN on VPS with coturn)

**Tech stack elements:**
- aiohttp 3.13.3 (signaling server)
- WebSocket Secure (WSS)
- JWT authentication
- STUN server (coturn on VPS)

### Phase 3: P2P Messaging (Text + Files)
**Rationale:** Core value proposition (encrypted messaging). Validates entire crypto + P2P stack before adding media complexity. Most technically complex component, needs early testing. Does NOT require media codecs (simpler than voice/video).

**Delivers:** Two clients can exchange E2E encrypted text messages over WebRTC data channels. File transfer with encryption, chunking, and progress tracking. Working NAT traversal (STUN-only, ~75-80% success rate).

**Addresses features:**
- 1-on-1 text messaging (E2E encrypted)
- File sharing (unlimited size, encrypted)
- Offline message delivery (store-and-forward)
- Message history persistence

**Avoids pitfalls:**
- NAT traversal failures (implement diagnostics, test across real networks early)
- Testing only locally (cross-network testing from start)
- Message replay attacks (implement sequence numbers and signatures)
- WebView bridge XSS (use JSON serialization, avoid eval)

**Tech stack elements:**
- aiortc 1.14.0 (WebRTC data channels)
- X3DH 1.3.0 + DoubleRatchet 1.3.0 (Signal Protocol)
- ICE with STUN (no TURN)

**Research flag:** Phase 3 needs deeper research into aiortc data channel performance and reliable file chunking patterns (64KB chunks, resume capability). MEDIUM complexity, some patterns well-documented but aiortc-specific details sparse.

### Phase 4: Voice/Video Calls (1-on-1)
**Rationale:** Builds on proven P2P foundation from Phase 3. Start with 1-on-1 (simpler than group). Media codecs supported by aiortc (Opus for audio, VP8/H.264 for video).

**Delivers:** Two clients can do voice/video calls with acceptable latency (<100ms on good networks). Call controls (mute, video on/off, hang up). Screen sharing (desktop capture).

**Addresses features:**
- 1-on-1 voice calls
- 1-on-1 video calls
- Screen sharing
- Push-to-talk (gaming/tactical use)

**Avoids pitfalls:**
- Audio codec limitations (force Opus in SDP negotiation, test with multiple browsers)
- Browser compatibility (test Chrome, Firefox, Safari, Edge)
- PyAV frame timestamp issues (monitor frame.pts for audio interruptions)

**Tech stack elements:**
- aiortc audio/video support (Opus, VP8/H.264)
- WebRTC media streams (SRTP)
- PyAV for frame processing

**Research flag:** Phase 4 needs research into cross-browser WebRTC compatibility (Safari historically limited, different SDP handling). aiortc audio codec negotiation with browsers needs testing. HIGH priority research before implementation.

### Phase 5: Group Features
**Rationale:** Requires stable 1-on-1 foundation. Most complex (mesh = N*(N-1) connections). Can start with small groups (2-4 participants) using mesh, defer SFU to Phase 6.

**Delivers:** Group chat rooms with persistent history, group messaging using Sender Keys protocol, group voice calls (mesh topology for 2-4 participants).

**Addresses features:**
- Group text chat
- Group voice calls (2-4 participants)
- Persistent group rooms
- Group file sharing

**Avoids pitfalls:**
- Mesh topology bandwidth limits (document 2-4 participant limit clearly)
- Group encryption complexity (Sender Keys protocol)

**Tech stack elements:**
- Sender Keys protocol (Signal Protocol extension)
- WebRTC mesh topology
- Group session management

**Research flag:** Phase 5 needs research into Sender Keys protocol implementation and WebRTC mesh optimization for groups. HIGH complexity, moderate documentation available. Consider research-phase before implementation.

### Phase 6: Scaling & Polish
**Rationale:** Depends on core features being stable. SFU architecture for 5+ participant groups, update mechanism for long-term maintenance, multi-device support for user convenience.

**Delivers:** SFU server for scalable group calls (5-25 participants), auto-updater with Tufup, multi-device key sync protocol, encrypted key backup/recovery, Nuitka-packaged production builds.

**Addresses features:**
- Group video calls (5+ participants via SFU)
- Multi-device support (link new device)
- Message editing/deletion
- Rich media embeds
- Custom emojis/reactions

**Avoids pitfalls:**
- No update mechanism (implement Tufup from start of Phase 6)
- DPAPI key loss on password reset (encrypted backup with user password)
- Large bundle size (exclude unused modules, optimize React build)

**Tech stack elements:**
- Nuitka (production packaging)
- Tufup (secure auto-updater)
- SFU server (for 5+ participant groups)

### Phase Ordering Rationale

- **Foundation before networking**: Phase 1 establishes crypto/storage without network complexity, allowing offline development and early validation of packaging/key management.
- **Signaling before P2P**: Phase 2 required for any peer connections, simplest network component, establishes security patterns.
- **Text before media**: Phase 3 validates P2P stack with data channels (simpler than media codecs), provides immediate user value.
- **1-on-1 before groups**: Phase 4 proves media streaming works before N-way mesh complexity.
- **Groups before scaling**: Phase 5 delivers group features with mesh (free, 2-4 limit), Phase 6 adds SFU when needed.
- **Polish deferred**: Phase 6 features are nice-to-have, depend on stable core, can iterate based on user feedback.

**Critical early testing**: NAT traversal (Phase 3), key storage security (Phase 1), and packaging (Phase 1) must be validated early as they're architectural constraints that are expensive to change later.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 3 (P2P Messaging)**: aiortc data channel performance characteristics, reliable file transfer patterns with resume capability, store-and-forward offline messaging implementation. MEDIUM complexity, some documentation available but aiortc-specific patterns need investigation.

- **Phase 4 (Voice/Video)**: Cross-browser WebRTC compatibility (Safari SDP differences, codec negotiation), aiortc audio codec interop with browser peers, PyAV timestamp handling for audio frames. HIGH priority research, browser interop poorly documented for aiortc.

- **Phase 5 (Groups)**: Sender Keys protocol implementation details, WebRTC mesh optimization for 3-4 participants, group key management UX. HIGH complexity, moderate documentation. Consider dedicated research-phase sprint.

Phases with standard patterns (can skip research-phase):

- **Phase 1 (Foundation)**: Well-documented patterns for SQLCipher, Python DPAPI usage, PyInstaller packaging. Use official docs and avoid pitfalls identified in research.

- **Phase 2 (Signaling)**: Standard WebSocket server patterns, JWT authentication is well-documented, STUN server setup (coturn) has extensive documentation.

- **Phase 6 (Scaling)**: Tufup and SFU architectures well-documented, multi-device sync follows Signal's model (documented in protocol specs).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified from PyPI/npm (Jan 2026), production-stable libraries, official documentation confirms features. Signal Protocol implementations by same author (Syndace), actively maintained. |
| Features | MEDIUM-HIGH | Core messaging features and E2E encryption requirements verified across multiple sources. Implementation complexity estimates based on community consensus, not tested in this project. P2P-specific challenges (offline messaging, NAT traversal) documented but real-world success rates vary. |
| Architecture | HIGH | Architecture patterns verified with official WebRTC/Signal Protocol specs, aiohttp docs, SQLCipher documentation. Component boundaries follow proven designs from Signal, Session, Jami. aiortc examples and GitHub issues confirm WebRTC capabilities. |
| Pitfalls | HIGH | NAT traversal statistics from multiple WebRTC sources, PyInstaller issues from official docs, Windows DPAPI from Microsoft docs, E2E encryption pitfalls from OWASP/NIST. All pitfalls verified with recent 2025-2026 sources and official documentation. |

**Overall confidence:** HIGH

Research based on official documentation (Python/npm package repos, Microsoft docs, Signal Protocol specs, WebRTC RFCs), verified with recent 2025-2026 sources, cross-referenced across multiple authoritative sources. Architecture patterns proven by existing privacy messengers (Signal, Session, Jami).

### Gaps to Address

Areas where research was inconclusive or needs validation during implementation:

- **NAT traversal success rate without TURN**: Sources cite 75-80% success with STUN-only, but this varies by network topology, ISP CGNAT policies, and geographic region. Must track actual connection success rate in production and consider TURN fallback if success rate <70%. Test extensively across network types in Phase 3.

- **aiortc audio codec interop with browsers**: PyAV documentation is sparse, frame timestamp handling requires experimentation. aiortc-to-browser audio calls need thorough testing in Phase 4. Safari compatibility historically problematic, may need workarounds or browser restrictions.

- **Group call mesh scalability**: Research suggests 2-4 participants viable for mesh, but actual bandwidth/CPU limits depend on video resolution, codec settings, hardware. Need real-world testing in Phase 5 to determine when SFU becomes mandatory vs optional.

- **Store-and-forward offline messaging**: Session uses swarms (DHT-based routing), Briar uses Bluetooth/WiFi fallback. Best implementation pattern for DiscordOpus needs deeper research in Phase 3 planning. Complexity trade-off: simple message queue on signaling server vs distributed swarm routing.

- **Multi-device sync without central server**: Signal's device linking protocol documented, but implementation details for P2P context need research in Phase 6. Challenge: syncing message history and session state across devices when devices aren't always online simultaneously.

- **Windows DPAPI key recovery after password reset**: Sources confirm DPAPI keys lost on forced password reset (not normal change). Key backup mechanism design needs user experience research: recovery codes vs password-encrypted backup vs optional cloud backup trade-offs.

## Sources

### Primary Sources (HIGH confidence)

**Stack research:**
- aiortc PyPI (https://pypi.org/project/aiortc/) — Version 1.14.0 verified, Oct 2025 release
- aiohttp PyPI (https://pypi.org/project/aiohttp/) — Version 3.13.3 verified, Jan 2026 release
- cryptography PyPI (https://pypi.org/project/cryptography/) — Version 46.0.4 verified, Jan 28 2026 release
- DoubleRatchet PyPI (https://pypi.org/project/DoubleRatchet/) — Version 1.3.0 verified, Jan 29 2026 release
- python-doubleratchet GitHub (https://github.com/Syndace/python-doubleratchet) — Signal Protocol implementation
- python-x3dh GitHub (https://github.com/Syndace/python-x3dh) — X3DH implementation
- PyWebView PyPI (https://pypi.org/project/pywebview/) — Version 6.1 verified
- PyInstaller PyPI (https://pypi.org/project/PyInstaller/) — Version 6.18.0 verified, Jan 13 2026 release
- Vite releases (https://vite.dev/releases) — Version 7.3.1 stable verified
- React Router v7 announcement (https://remix.run/blog/react-router-v7)
- shadcn/ui Tailwind v4 guide (https://ui.shadcn.com/docs/tailwind-v4)

**Architecture research:**
- Signal Protocol Documentation (https://signal.org/docs/)
- Signal Protocol X3DH Specification (https://signal.org/docs/specifications/x3dh/)
- Signal Protocol Double Ratchet (https://signal.org/docs/specifications/doubleratchet/)
- aiortc GitHub Repository (https://github.com/aiortc/aiortc)
- aiohttp WebSocket documentation (https://docs.aiohttp.org/en/stable/websocket_utilities.html)
- RFC 8831: WebRTC Data Channels (https://datatracker.ietf.org/doc/html/rfc8831)
- RFC 8827: WebRTC Security Architecture (https://www.rfc-editor.org/rfc/rfc8827.html)
- SQLCipher Official Site (https://www.zetetic.net/sqlcipher/)

**Pitfalls research:**
- PyInstaller Common Issues and Pitfalls (https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html)
- OWASP Key Management Cheat Sheet (https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- Microsoft CNG Key Storage (https://learn.microsoft.com/en-us/windows/win32/seccng/key-storage-and-retrieval)
- Microsoft Windows DPAPI (https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptographic-key-storage-and-exchange)
- Python secrets module documentation (https://docs.python.org/3/library/secrets.html)

### Secondary Sources (MEDIUM confidence)

**Features research:**
- Signal Review 2026 (https://cyberinsider.com/secure-encrypted-messaging-apps/signal/)
- Session Review 2026 (https://cyberinsider.com/secure-encrypted-messaging-apps/session/)
- Jami P2P Messaging (https://awesome-privacy.xyz/communication/p2p-messaging/jami)
- WebRTC Tech Stack Guide 2026 (https://webrtc.ventures/2026/01/webrtc-tech-stack-guide-architecture-for-scalable-real-time-applications/)
- Discord Review 2026 (https://pumble.com/reviews/discord-review)

**Architecture patterns:**
- Peer-to-Peer WebRTC Architecture (https://getstream.io/resources/projects/webrtc/architectures/p2p/)
- WebRTC Signaling Server Explained (https://antmedia.io/webrtc-signaling-servers-everything-you-need-to-know/)
- Jami Distributed Network (https://docs.jami.net/en_US/user/jami-distributed-network.html)
- Python WebRTC basics with aiortc (https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id)

**Pitfalls patterns:**
- WebRTC NAT Traversal: Understanding STUN, TURN, and ICE (https://www.nihardaily.com/168-webrtc-nat-traversal-understanding-stun-turn-and-ice)
- WebRTC Stun vs Turn Servers (https://getstream.io/resources/projects/webrtc/advanced/stun-turn/)
- An Intro to WebRTC's NAT/Firewall Problem (https://webrtchacks.com/an-intro-to-webrtcs-natfirewall-problem/)
- Common WebRTC Mistakes (https://bloggeek.me/common-beginner-mistakes-in-webrtc/)
- WebRTC Security Study (https://webrtc-security.github.io/)
- Nuitka vs PyInstaller comparison (https://krrt7.dev/en/blog/nuitka-vs-pyinstaller)

### Tertiary Sources (LOW confidence, needs validation)

- State management in 2026 (https://www.nucamp.co/blog/state-management-in-2026-redux-context-api-and-modern-patterns) — Community trends, not official
- Mesh vs SFU vs MCU bandwidth estimates — Multiple sources with varying numbers, need real-world testing
- NAT traversal success rate statistics (75-80% STUN-only) — Based on 2020-2023 studies, may vary by region/ISP
- aiortc datachannel performance improvements — Mentioned in release notes but no recent benchmarks

---
*Research completed: 2026-01-30*
*Ready for roadmap: yes*
