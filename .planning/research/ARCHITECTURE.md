# Architecture Research: DiscordOpus

**Domain:** P2P Communication App (Discord-like with E2E encryption)
**Researched:** 2026-01-30
**Confidence:** HIGH (verified with official sources and recent documentation)

## Summary

P2P communication systems like Signal, Session, and Jami employ a layered architecture separating untrusted signaling infrastructure from trusted client-side cryptographic operations. The core pattern: **minimal signaling server (untrusted) + WebRTC P2P layer (encrypted) + client-side E2E encryption (Signal Protocol) + local encrypted storage (SQLCipher)**. For DiscordOpus, this translates to: Python backend handling crypto/storage/WebRTC orchestration, React frontend in webview for UI, lightweight VPS signaling server for connection establishment only, and strict security boundaries preventing signaling server from accessing message content or encryption keys.

## System Components

### 1. Client Application (Python + React + Webview)

**Python Backend Layer:**
- **Purpose:** Cryptographic operations, WebRTC orchestration, local storage management
- **Technology:** Python 3.10+ with aiortc for WebRTC, SQLCipher for encrypted database
- **Responsibilities:**
  - Identity key generation and management (Ed25519/X25519 key pairs)
  - Signal Protocol implementation (X3DH key agreement, Double Ratchet encryption)
  - WebRTC peer connection management via aiortc
  - Local message/contact storage in encrypted SQLite database
  - File encryption/decryption for transfers
  - WebSocket client for signaling server communication

**React Frontend Layer:**
- **Purpose:** User interface, rendering, user interactions
- **Technology:** React in webview (pywebview)
- **Responsibilities:**
  - Contact list, room list, message display
  - Call controls (mute, video on/off, hang up)
  - File selection for transfers
  - Settings and key management UI
  - Communicates with Python backend via pywebview JavaScript bridge

**Webview Integration Layer:**
- **Purpose:** Native window container for web-based UI
- **Technology:** pywebview (EdgeWebView2 on Windows, requires .NET Framework >4.0)
- **Responsibilities:**
  - Display React UI in native window
  - Expose Python API to JavaScript via pywebview.api
  - Handle window lifecycle (minimize, close, etc.)
  - Package as single .exe with PyInstaller

**Packaging:**
- PyInstaller bundles Python + React build + dependencies into standalone .exe
- Challenges: Exclude unused dependencies (e.g., PyQt if not used), handle sys._MEIPASS for resource paths

### 2. Signaling Server (Minimal Design)

**Purpose:** Connection establishment only - does NOT see message content or encryption keys

**Technology:** Node.js + WebSocket (or Python + websockets)

**Responsibilities:**
- Relay SDP offers/answers between peers
- Relay ICE candidates for NAT traversal
- Maintain user presence (online/offline status)
- Route signaling messages by user ID (public key hash or derived identifier)
- Tear down sessions when peers disconnect

**What It Does NOT Do:**
- Does NOT store messages (ephemeral relay only)
- Does NOT access encryption keys
- Does NOT decrypt message content
- Does NOT relay media streams (those go P2P via WebRTC)
- Does NOT require authentication (identity is cryptographic)

**Trust Boundary:**
- **ZERO TRUST** - assume signaling server is untrusted/compromised
- E2E encryption prevents signaling server from reading messages
- Identity verification via Signal Protocol prevents MITM attacks
- Use WSS (WebSocket Secure) to prevent passive eavesdropping on signaling metadata

**Minimal Implementation:**
```
Server receives: {from: userA_pubkey_hash, to: userB_pubkey_hash, type: "offer", sdp: "..."}
Server relays to userB if online
Server does NOT parse/modify SDP content
```

### 3. P2P Layer (WebRTC)

**Purpose:** Direct peer-to-peer connections for media and data transfer

**Technology:** WebRTC via aiortc (Python implementation)

**Components:**

**a) ICE (Interactive Connectivity Establishment):**
- Collect ICE candidates (host, server-reflexive via STUN)
- Exchange candidates via signaling server
- Establish direct connection (succeeds ~75-80% of time with STUN alone)
- NOTE: Project specifies NO TURN relay (cost savings), so 20-25% of connections may fail behind strict NATs

**b) DTLS/SRTP (Transport Security):**
- DTLS handshake for SCTP data channels
- SRTP encryption for audio/video streams
- WebRTC provides transport encryption (prevents network-level eavesdropping)
- NOT sufficient for E2E encryption (need additional layer)

**c) Media Streams:**
- Audio: Opus codec (supported by aiortc)
- Video: VP8 or H.264 (supported by aiortc)
- Bundled audio + video in single peer connection

**d) Data Channels:**
- Reliable, ordered data channels for text messages
- Reliable, ordered data channels for file transfers (split files into 64KB chunks)
- Data channels encrypted at transport layer (DTLS/SCTP)

**Group Call Architecture:**
- **2-4 participants:** Mesh (full P2P) - each peer connects to all others
  - Pros: Zero server cost, minimal latency
  - Cons: Upload bandwidth scales O(n) per participant, CPU usage high
- **5+ participants:** Consider SFU (Selective Forwarding Unit) for scalability
  - Each peer uploads once, SFU forwards to others
  - Reduces client upload bandwidth and CPU usage
  - Adds server cost (~$500/month vs mesh's $0)
  - NOTE: Project likely starts with mesh for MVP

**Connection Success:**
- Host candidates: Work on same LAN only
- STUN server-reflexive candidates: ~75-80% success on internet
- Without TURN relay: ~20-25% of connections may fail behind symmetric NAT
- Hybrid fallback: Could add TURN later if needed

### 4. Encryption Layer (Signal Protocol)

**Purpose:** End-to-end encryption ensuring only conversation participants can read messages

**Technology:** Signal Protocol (X3DH + Double Ratchet)

**Key Hierarchy:**

**a) Identity Keys (Long-term):**
- Generated once per client installation
- Ed25519 for signing, X25519 for key agreement
- Public key (or hash) serves as user identifier
- Stored locally in encrypted database

**b) Prekeys (Medium-term):**
- Signed prekey pair: Rotated periodically (e.g., weekly)
- One-time prekey pairs: Ephemeral, consumed per conversation initiation
- "Key bundle" (identity public key + signed prekey + one-time prekeys) stored on signaling server

**c) Session Keys (Ephemeral):**
- Derived via X3DH when initiating conversation
- Master secret → root key + sending chain key
- Double Ratchet generates new message key per message
- Forward secrecy: Old keys cannot be derived from new keys
- Backward secrecy: New keys cannot be derived from old keys

**X3DH (Extended Triple Diffie-Hellman):**
- Establishes shared secret when initiating conversation
- Alice fetches Bob's key bundle from signaling server
- Alice performs 3-4 DH operations with her keys and Bob's keys
- Output: Master secret (authenticated and forward-secure)

**Double Ratchet:**
- Symmetric ratchet: KDF chain for deriving message keys
- DH ratchet: New DH key pair per message, mixed into key derivation
- Every message encrypted with unique message key
- Provides post-compromise security (recovering from key compromise)

**Group Encryption:**
- Sender Keys protocol (extension of Signal Protocol for groups)
- Each member has sender key chain, distributes to group members
- Scalable for small-medium groups (not suitable for large channels)

**Integration with WebRTC:**
- WebRTC provides transport encryption (DTLS/SRTP)
- Signal Protocol provides E2E encryption (on top of transport)
- Messages encrypted before sending via data channel
- Files encrypted before chunking and transfer

### 5. Storage Layer (Local Encrypted Database)

**Purpose:** Secure local storage of messages, contacts, keys, and metadata

**Technology:** SQLite with SQLCipher extension

**Encryption:**
- 256-bit AES encryption (military-grade)
- Entire database file encrypted at rest
- Encryption key derived from user passphrase or system keystore
- Tamper-resistant design
- Cross-platform compatibility (same encrypted DB works on all platforms)

**Schema (Example):**

**Contacts Table:**
- contact_id (public key hash)
- display_name
- public_key (identity key)
- last_seen
- trust_status (verified/unverified)

**Conversations Table:**
- conversation_id
- type (1-on-1, group)
- participants (JSON array of contact_ids)
- last_message_timestamp

**Messages Table:**
- message_id (UUID)
- conversation_id (foreign key)
- sender_id (contact_id)
- plaintext (decrypted message)
- timestamp
- read_status

**Sessions Table:**
- session_id
- remote_contact_id
- root_key, chain_keys, message_keys (Signal Protocol state)
- ratchet_state

**Prekeys Table:**
- prekey_id
- private_key
- public_key
- used (boolean)

**Files Table:**
- file_id (hash)
- file_path (local path)
- encryption_key
- size, mime_type

**Key Management:**
- Master encryption key stored in OS keystore (e.g., Windows DPAPI)
- Or derived from user passphrase using Argon2 KDF
- Database unlocked on app start, locked on close

**Backup Considerations:**
- Database file is encrypted, safe to backup
- Key backup/recovery mechanism needed for device loss
- Could export encrypted key backup to another device

## Data Flow

### Message Send Flow (1-on-1)

```
1. User types message in React UI
2. React calls Python API: sendMessage(recipient_id, plaintext)
3. Python backend:
   a. Lookup Signal Protocol session for recipient
   b. If no session: Fetch recipient's key bundle, perform X3DH
   c. Encrypt message with Double Ratchet (derive new message key)
   d. Store encrypted message in local DB (but store plaintext for sender's history)
4. Python sends encrypted message via WebRTC data channel to recipient
   - If no active P2P connection: Signal server relays "initiate connection" message
   - Peers exchange SDP/ICE via signaling server
   - Establish WebRTC data channel
5. Python sends encrypted message payload over data channel
6. Recipient's Python backend:
   a. Receive encrypted message from data channel
   b. Decrypt using Double Ratchet session
   c. Store plaintext in local DB
   d. Notify React UI via event
7. Recipient's React UI displays message
```

### Voice/Video Call Flow

```
1. User A clicks "Call" button for User B
2. React calls Python API: initiateCall(recipient_id, media_type)
3. Python backend:
   a. Create RTCPeerConnection with audio/video tracks
   b. Gather ICE candidates (via STUN)
   c. Create SDP offer
   d. Send offer + ICE candidates to recipient via signaling server
4. Signaling server relays offer to User B (WebSocket message)
5. User B's Python backend:
   a. Receive call offer
   b. Notify React UI (show incoming call prompt)
6. User B accepts call
7. User B's Python backend:
   a. Create RTCPeerConnection with audio/video tracks
   b. Set remote description (offer)
   c. Create SDP answer
   d. Gather ICE candidates
   e. Send answer + ICE candidates via signaling server
8. Signaling server relays answer to User A
9. Both peers:
   a. Set remote description
   b. ICE connectivity checks (try direct P2P)
   c. WebRTC connection established
   d. Media streams flow directly P2P (NOT through server)
10. Python backend pipes audio/video to React UI for rendering
```

### File Transfer Flow

```
1. User A selects file in React UI
2. React calls Python API: sendFile(recipient_id, file_path)
3. Python backend:
   a. Read file, generate random encryption key
   b. Encrypt file content (AES-256-GCM)
   c. Split encrypted file into 64KB chunks
   d. Store file metadata + encryption key in local DB
4. For each chunk:
   a. Send chunk via WebRTC data channel (reliable, ordered)
   b. Monitor transfer progress
5. After all chunks sent:
   a. Send file metadata + encryption key via encrypted Signal Protocol message
6. Recipient's Python backend:
   a. Receive chunks via data channel, buffer to disk
   b. Receive metadata message, decrypt encryption key
   c. Decrypt file using encryption key
   d. Store decrypted file, update DB
   e. Notify React UI
7. React UI displays file in chat
```

### Group Call Flow (Mesh)

```
For 2-4 participants:

1. User A creates group call in room
2. Python backend:
   a. Create RTCPeerConnection to User B
   b. Create RTCPeerConnection to User C
   c. Each connection has audio/video tracks
3. User A uploads media stream twice (once to B, once to C)
4. User A receives media stream from B and from C
5. React UI mixes/displays 3 video feeds
6. Bandwidth: Each peer uploads (N-1) streams, downloads (N-1) streams
7. For 4 participants: Each uploads 3x, downloads 3x
```

## Component Interactions

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React Frontend (pywebview)                   │  │
│  │  - UI Rendering                                           │  │
│  │  - User Input                                             │  │
│  │  - Message Display                                        │  │
│  │  - Call Controls                                          │  │
│  └─────────────────┬────────────────────────────────────────┘  │
│                    │ pywebview.api (JavaScript bridge)         │
│                    ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Python Backend                               │  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌──────────────────┐               │  │
│  │  │ Crypto Engine   │  │  WebRTC Engine   │               │  │
│  │  │ - Key mgmt      │  │  - aiortc        │               │  │
│  │  │ - Signal Proto  │  │  - ICE/STUN      │               │  │
│  │  │ - Encryption    │  │  - Media streams │               │  │
│  │  └────────┬────────┘  └────────┬─────────┘               │  │
│  │           │                     │                          │  │
│  │           ▼                     ▼                          │  │
│  │  ┌──────────────────────────────────────┐                │  │
│  │  │     Storage Layer (SQLCipher)        │                │  │
│  │  │  - Messages  - Contacts  - Keys      │                │  │
│  │  └──────────────────────────────────────┘                │  │
│  └─────────────────┬────────────────────────────────────────┘  │
│                    │                                            │
└────────────────────┼────────────────────────────────────────────┘
                     │
                     │ WebSocket (WSS) - Signaling only
                     │ (SDP/ICE exchange, presence)
                     ▼
        ┌────────────────────────────┐
        │   SIGNALING SERVER (VPS)   │
        │  - Relay SDP/ICE           │
        │  - User presence           │
        │  - NO message content      │
        │  - NO encryption keys      │
        └────────────┬───────────────┘
                     │
                     │ WSS
                     │
                     ▼
        ┌────────────────────────────┐
        │   OTHER CLIENT(S)          │
        └────────────────────────────┘

               TRUST BOUNDARY
══════════════════════════════════════════════════════════
  Above line: UNTRUSTED (signaling server)
  Below line: TRUSTED (client application)

┌────────────────────────────────────────────────────────────┐
│             WebRTC P2P Connections                          │
│                                                             │
│  Client A  ←──────────────────────────────────────►  Client B
│             DTLS/SRTP encrypted data channel              │
│             Direct P2P (NOT through signaling server)      │
│                                                             │
│  - Media streams (audio/video)                             │
│  - Encrypted messages (Signal Protocol encrypted)          │
│  - File chunks (encrypted)                                 │
└────────────────────────────────────────────────────────────┘
```

**Key Interaction Principles:**

1. **Signaling is separate from media/data:** Signaling server never sees P2P traffic
2. **E2E encryption before transmission:** Messages encrypted client-side, sent encrypted over WebRTC
3. **Local storage is encrypted:** Database encrypted at rest, keys never leave client
4. **Zero trust signaling:** Signaling server treated as untrusted relay

## Suggested Build Order

Based on dependencies and risk mitigation:

### Phase 1: Foundation (Local-First)
**Components:**
- SQLCipher database schema and encryption
- Basic identity key generation (Ed25519/X25519)
- Contact storage (local only, no sync)
- Python backend skeleton with API structure
- React UI skeleton with pywebview integration

**Why first:**
- No network dependencies (can develop offline)
- Establishes data model and storage patterns
- Tests Python ↔ React integration early
- Validates PyInstaller packaging early

**Deliverable:** Single .exe that generates keys, stores contacts locally, displays UI

### Phase 2: Signaling Infrastructure
**Components:**
- Minimal signaling server (WebSocket relay)
- WebSocket client in Python backend
- Presence system (online/offline)
- User discovery (by public key ID)

**Why second:**
- Needed before P2P connections can be established
- Simplest network component (stateless relay)
- Testable without WebRTC complexity

**Deliverable:** Clients can connect to signaling server, see each other's online status

### Phase 3: P2P Messaging (Text)
**Components:**
- Signal Protocol implementation (X3DH + Double Ratchet)
- WebRTC data channel establishment (aiortc)
- ICE/STUN integration
- Encrypted text message send/receive
- Message storage and display

**Why third:**
- Core value proposition (encrypted messaging)
- Validates entire crypto + P2P stack
- Most complex component, needs early testing
- Does NOT require media (simpler than voice/video)

**Deliverable:** Two clients can exchange encrypted text messages P2P

### Phase 4: Voice/Video Calls (1-on-1)
**Components:**
- Audio capture/playback (Opus codec)
- Video capture/playback (VP8/H.264 codec)
- WebRTC media streams (aiortc)
- Call signaling (offer/answer/ICE)
- Call UI controls

**Why fourth:**
- Builds on proven P2P foundation from Phase 3
- Start with 1-on-1 (simpler than group)
- Media codecs supported by aiortc

**Deliverable:** Two clients can do voice/video calls

### Phase 5: File Transfer
**Components:**
- File encryption (AES-256-GCM)
- Chunking and reassembly (64KB chunks)
- Progress tracking
- File metadata messaging

**Why fifth:**
- Uses existing data channels from Phase 3
- Independent of voice/video
- File size unlimited (per project requirements)

**Deliverable:** Send files of any size P2P

### Phase 6: Group Features
**Components:**
- Group rooms (persistent)
- Group messaging (Sender Keys)
- Group calls (mesh for 2-4, potentially SFU for 5+)

**Why sixth:**
- Requires stable 1-on-1 foundation
- Most complex (mesh = N*(N-1) connections)
- Can start with small groups (2-4)

**Deliverable:** Group chat rooms with voice/video

### Phase 7: Polish and Optimization
**Components:**
- Message history sync
- Multi-device support (link new device)
- Key backup/recovery
- UI/UX improvements
- Performance optimization

**Why last:**
- Depends on core features being stable
- Nice-to-have vs must-have
- Can iterate based on user feedback

## Critical Boundaries

### Security Boundary: Client vs Signaling Server

**Principle:** Signaling server is UNTRUSTED, client is TRUSTED

**Enforcement:**
- All encryption happens client-side (Python backend)
- Signaling server receives only opaque signaling messages (SDP/ICE)
- No plaintext messages, encryption keys, or sensitive metadata sent to server
- Signal Protocol provides authentication (prevents signaling server MITM)

**What crosses boundary:**
- User presence (online/offline) - ACCEPTABLE metadata leakage
- Connection initiation requests (Alice wants to connect to Bob) - ACCEPTABLE
- SDP offers/answers and ICE candidates - OPAQUE to server
- NO message content, NO encryption keys, NO file content

### Privacy Boundary: Network vs Client Storage

**Principle:** Plaintext data NEVER leaves encrypted client storage

**Enforcement:**
- Messages encrypted before sending over WebRTC data channel
- Files encrypted before chunking and transfer
- Local database encrypted at rest with SQLCipher
- Encryption keys derived from user passphrase or OS keystore

**What crosses boundary (encrypted):**
- Message ciphertext (Signal Protocol encrypted)
- File ciphertext (AES-256-GCM encrypted)
- Media streams (SRTP encrypted at transport layer)

### Crypto Boundary: WebRTC Transport vs E2E Encryption

**Principle:** WebRTC encryption is NOT sufficient for E2E, need additional layer

**Why:**
- WebRTC DTLS/SRTP encrypts peer-to-peer connection
- BUT if using SFU/MCU, server can decrypt media
- Signal Protocol ensures encryption end-to-end (only participants can decrypt)

**Enforcement:**
- Text messages: Encrypted with Signal Protocol BEFORE sending over data channel
- Files: Encrypted with AES-256-GCM BEFORE sending over data channel
- Voice/video: WebRTC SRTP sufficient for P2P mesh (no intermediary), but consider adding E2E for paranoid security

### Process Boundary: Python Backend vs React Frontend

**Principle:** All cryptographic operations in Python, UI in React

**Why:**
- JavaScript crypto is harder to secure (no native secure storage)
- Python has better crypto libraries (cryptography, aiortc)
- Separation of concerns (UI doesn't handle sensitive operations)

**Enforcement:**
- React NEVER accesses raw encryption keys
- React sends plaintext to Python via pywebview.api
- Python encrypts and sends over network
- Python receives encrypted data, decrypts, passes plaintext to React
- Database credentials stay in Python backend

### Network Boundary: P2P vs Server

**Principle:** Media/data flows P2P, NOT through server (except signaling)

**Why:**
- Privacy: Server cannot eavesdrop on E2E encrypted communication
- Performance: Direct P2P has lower latency
- Cost: No bandwidth cost for server (only signaling overhead)

**Enforcement:**
- Signaling server relays SDP/ICE only
- WebRTC data channels connect peers directly
- Voice/video streams flow directly between peers
- File chunks sent directly P2P
- NO TURN relay (project requirement, cost savings)

**Trade-off:**
- ~20-25% of connections may fail behind strict NATs without TURN
- Could add TURN later if needed (increases server cost significantly)

## Architecture Patterns to Follow

### Pattern 1: Layered Encryption

**What:** Multiple layers of encryption for defense in depth

**Layers:**
1. Application layer: Signal Protocol E2E encryption (message content)
2. Transport layer: WebRTC DTLS/SRTP (P2P connection)
3. Network layer: TLS for signaling (WebSocket Secure)
4. Storage layer: SQLCipher (database at rest)

**Example:**
```python
# Application layer
plaintext = "Hello"
ciphertext = signal_encrypt(plaintext, session)

# Transport layer (automatic)
webrtc_datachannel.send(ciphertext)  # DTLS encrypted transport

# Receiving side
ciphertext = webrtc_datachannel.receive()  # DTLS decrypted transport
plaintext = signal_decrypt(ciphertext, session)  # Application decrypted
```

### Pattern 2: Key Derivation Hierarchy

**What:** Derive keys hierarchically, never reuse keys

**Hierarchy:**
```
User Passphrase
  └─> Master Database Key (Argon2 KDF)
        └─> SQLCipher Database Encryption Key

Identity Key Pair (long-term)
  └─> X3DH Shared Secret
        └─> Root Key + Chain Key
              └─> Message Keys (one per message)
```

**Why:** Key compromise at lower level doesn't compromise higher levels

### Pattern 3: Zero-Trust Signaling

**What:** Treat signaling server as hostile relay

**Implementation:**
- Use Signal Protocol X3DH (includes identity verification)
- Verify identity keys out-of-band (e.g., QR code scan, safety number)
- Signaling server cannot MITM because it lacks private keys
- Use WSS (not WS) to prevent passive network eavesdropping on signaling

### Pattern 4: Local-First Architecture

**What:** All data stored locally, no cloud sync

**Benefits:**
- Privacy: Data never leaves user's device (except E2E encrypted)
- Offline capability: Read message history offline
- No sync conflicts (single source of truth per device)

**Trade-off:**
- Multi-device support requires explicit device linking (Signal model)
- Message history not automatically synced to new devices

### Pattern 5: Async Event-Driven Communication

**What:** Python backend uses asyncio, React uses event listeners

**Python side (aiortc requires asyncio):**
```python
async def handle_incoming_message(message):
    plaintext = await decrypt_message(message)
    await store_message(plaintext)
    window.evaluate_js(f"window.onNewMessage({json.dumps(plaintext)})")
```

**React side:**
```javascript
window.onNewMessage = (message) => {
  dispatch(addMessage(message));
};
```

**Why:** aiortc is async, Python-React bridge is async, matches WebRTC event-driven model

## Anti-Patterns to Avoid

### Anti-Pattern 1: Storing Keys in Frontend

**What:** Passing encryption keys to JavaScript/React

**Why bad:** JavaScript has no secure storage, XSS can leak keys

**Instead:** All crypto operations in Python backend, only pass plaintext to React

### Anti-Pattern 2: Trusting Signaling Server

**What:** Assuming signaling server is honest

**Why bad:** Signaling server could be compromised, ISP could MITM

**Instead:** Use Signal Protocol for authentication, verify identity out-of-band, use WSS

### Anti-Pattern 3: Reusing Encryption Keys

**What:** Using same key for multiple messages

**Why bad:** Cryptanalysis easier with more ciphertext, no forward secrecy

**Instead:** Signal Protocol Double Ratchet (new key per message)

### Anti-Pattern 4: Plaintext Database

**What:** Storing messages unencrypted in SQLite

**Why bad:** Disk theft, malware, forensics can read entire history

**Instead:** SQLCipher with strong passphrase-derived key

### Anti-Pattern 5: Blocking UI Thread

**What:** Doing crypto/network operations synchronously in React event handlers

**Why bad:** UI freezes during operations

**Instead:** All heavy operations in Python async backend, React gets events when complete

### Anti-Pattern 6: Large File Buffering

**What:** Loading entire file into memory before sending

**Why bad:** Out of memory for large files (project has no file size limit)

**Instead:** Stream file in 64KB chunks, encrypt and send chunk-by-chunk

### Anti-Pattern 7: Ignoring NAT Failure

**What:** Assuming P2P always succeeds

**Why bad:** ~20-25% of connections fail without TURN (symmetric NAT, firewall)

**Instead:** Detect connection failure, inform user, potentially add TURN relay for critical users

## Scalability Considerations

### At 10 Users (MVP)
- **Signaling server:** Single VPS (1 CPU, 512MB RAM) - trivial load
- **Client:** Mesh topology works fine for group calls (2-4 participants)
- **Storage:** Local SQLite handles thousands of messages easily
- **Bandwidth:** Direct P2P, no server bandwidth cost

### At 100 Users
- **Signaling server:** Same VPS handles hundreds of concurrent connections
- **Client:** Mesh still works for small group calls
- **Storage:** Database may grow to 100s of MB (still fast)
- **Bandwidth:** Still P2P, no server bandwidth cost

### At 1000 Users
- **Signaling server:** May need vertical scaling (2-4 CPU, 2GB RAM) or horizontal (multiple servers)
- **Client:** Mesh becomes problematic for large groups (5+ participants)
  - Consider SFU for groups >4 (adds server cost ~$500/month)
- **Storage:** Database may grow to GB range (still manageable)
- **Bandwidth:** P2P scales poorly for large groups (need SFU)

### At 10,000 Users
- **Signaling server:** Horizontal scaling required (load balancer + multiple servers)
- **Client:** SFU required for group calls (mesh impractical)
- **Storage:** Database size varies (depends on retention policy)
- **Bandwidth:** SFU reduces client upload but adds server bandwidth cost significantly

**Project Starting Point:**
- Start with mesh (free, simple)
- Monitor connection success rate (STUN-only ~75-80%)
- Add TURN if needed (~20-25% improvement, high cost)
- Add SFU when groups >4 become common (medium cost)

## Sources

### P2P Architecture and WebRTC
- [Peer-to-Peer WebRTC Architecture](https://getstream.io/resources/projects/webrtc/architectures/p2p/)
- [WebRTC Signaling Server Explained](https://antmedia.io/webrtc-signaling-servers-everything-you-need-to-know/)
- [P2P, SFU, MCU Architecture Guide for 2026](https://www.forasoft.com/blog/article/webrtc-architecture-guide-for-business-2026)
- [WebRTC ICE and Connection Establishment](https://webrtc.link/en/articles/webrtc-workflow/)

### Signal Protocol and E2E Encryption
- [Signal Protocol Documentation](https://signal.org/docs/)
- [Signal Protocol X3DH Specification](https://signal.org/docs/specifications/x3dh/)
- [Signal Protocol Double Ratchet](https://signal.org/docs/specifications/doubleratchet/)
- [Demystifying Signal Protocol](https://medium.com/@justinomora/demystifying-the-signal-protocol-for-end-to-end-encryption-e2ee-ad6a567e6cb4)

### Jami DHT Architecture
- [Jami Distributed Network](https://docs.jami.net/en_US/user/jami-distributed-network.html)
- [OpenDHT Implementation](https://github.com/savoirfairelinux/opendht)
- [Jami Dynamic Routing Table](https://docs.jami.net/en_US/developer/jami-concepts/drt.html)

### Session Messenger
- [Session Messenger Review 2026](https://cyberinsider.com/secure-encrypted-messaging-apps/session/)
- [Session PFS and PQE Improvements](https://www.privacyguides.org/news/2025/12/03/session-messenger-adds-pfs-pqe-and-other-improvements/)

### WebRTC Data Channels and File Transfer
- [WebRTC File Transfer Sample](https://webrtc.github.io/samples/src/content/datachannel/filetransfer/)
- [WebRTC Data Channels (web.dev)](https://web.dev/webrtc-datachannels/)
- [RFC 8831: WebRTC Data Channels](https://datatracker.ietf.org/doc/html/rfc8831)

### Python WebRTC (aiortc)
- [aiortc GitHub Repository](https://github.com/aiortc/aiortc)
- [aiortc Python WebRTC Library Guide](https://webrtc.link/en/articles/aiortc-python-webrtc-library/)
- [Python WebRTC Basics with aiortc](https://dev.to/whitphx/python-webrtc-basics-with-aiortc-48id)

### SQLCipher Encrypted Storage
- [SQLCipher Official Site](https://www.zetetic.net/sqlcipher/)
- [SimpleX Chat Encrypted Database](https://simplex.chat/blog/20220928-simplex-chat-v4-encrypted-database.html)
- [SQLCipher GitHub](https://github.com/sqlcipher/sqlcipher)

### Packaging and Desktop App
- [pywebview Documentation](https://pywebview.flowrl.com/)
- [Building Python Desktop Apps with pywebview](https://medium.com/@nohkachi/how-to-build-a-python-desktop-app-with-pywebview-and-flask-73025115e061)
- [pywebview Freezing Guide](https://pywebview.flowrl.com/guide/freezing.html)

### Security Architecture
- [RFC 8827: WebRTC Security Architecture](https://www.rfc-editor.org/rfc/rfc8827.html)
- [WebRTC Security Study](https://webrtc-security.github.io/)
- [WebRTC Encryption and Security 2026](https://www.mirrorfly.com/blog/webrtc-encryption-and-security/)

### Messaging App Architecture
- [Chat App Architecture Guide](https://www.rst.software/blog/chat-app-architecture)
- [Messaging App Architecture 2026](https://dev.to/jackdavis32/how-to-build-a-messaging-app-like-whatsapp-in-2026-features-tech-stack-security-cost-4f60)
- [Chat Application System Design](https://www.cometchat.com/blog/chat-application-architecture-and-system-design)

### Group Call Architectures
- [Mesh vs SFU vs MCU Comparison](https://antmedia.io/webrtc-network-topology/)
- [WebRTC Architecture P2P vs SFU vs MCU](https://www.red5.net/blog/webrtc-architecture-p2p-sfu-mcu-xdn/)
- [WebRTC Multiparty Video Alternatives](https://bloggeek.me/webrtc-multiparty-video-alternatives/)

### Identity Management
- [Identity-based Cryptography](https://cpl.thalesgroup.com/blog/access-management/identity-based-cryptography)
- [Digital ID Trends 2026](https://www.spokeo.com/compass/five-digital-id-trends-in-2026/)
- [Decentralized Identity (DID)](https://en.wikipedia.org/wiki/Identity-based_cryptography)
