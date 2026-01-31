# Phase 7: Group Features - Research

**Researched:** 2026-01-31
**Domain:** Group Messaging with Sender Keys Encryption, WebRTC Mesh Topology for Group Calls
**Confidence:** MEDIUM (Sender Keys implementation requires custom work; mesh patterns verified)

## Summary

Phase 7 adds group features: group creation/management, group messaging with E2E encryption using Sender Keys protocol, and group voice calls using WebRTC mesh topology. The research reveals that group messaging encryption must be implemented using a "Sender Keys" approach (symmetric chain key ratchet with signature verification) rather than extending the existing pairwise Double Ratchet. Group voice calls require managing N*(N-1)/2 RTCPeerConnection instances for mesh topology, with a practical limit of 4 participants.

Key findings:
1. **Sender Keys protocol** uses a symmetric chain key ratchet where each sender maintains their own key pair; messages are broadcast-encrypted once and signed. The existing python-doubleratchet library's symmetric ratchet component can be adapted for the chain key mechanism.
2. **WebRTC mesh** requires creating separate RTCPeerConnection per peer pair. For 4 participants, each peer needs 3 connections (6 total). Bandwidth scales as (N-1) * stream_bitrate per peer.
3. **Group management** is local-only (no server-side group state). Invite codes use cryptographically secure random tokens. Member lists are synchronized via group messages.
4. **Key rotation** is required when members leave (all participants must generate new Sender Keys to ensure forward secrecy from removed members).

**Primary recommendation:** Implement custom Sender Keys using existing HKDF/cryptography primitives, manage group state locally in SQLCipher, use existing aiortc for mesh connections with audio bitrate limiting. Display warning for 5+ member groups.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cryptography | (existing) | HKDF, AES-GCM, Ed25519 signing | Already used for Signal Protocol; provides all primitives needed for Sender Keys |
| aiortc | 1.14.0+ | WebRTC mesh connections | Already used for 1:1 calls; supports multiple RTCPeerConnection instances |
| python-doubleratchet | 1.3.0 | Symmetric ratchet reference | Can study/adapt chain key ratchet; don't use directly for groups |
| sqlcipher3 | (existing) | Encrypted group/message storage | Already in use for contacts and messages |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| secrets | stdlib | Secure invite code generation | For generating group invite tokens |
| hashlib | stdlib | SHA256 for chain key advancement | For ratcheting chain keys |
| uuid | stdlib | Group and message IDs | For unique identifiers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom Sender Keys | MLS (Messaging Layer Security) | MLS is more secure but vastly more complex; overkill for 2-20 member groups |
| Mesh topology | SFU (Selective Forwarding Unit) | SFU scales better but requires server infrastructure; mesh is P2P-only |
| Local group state | Server-side groups | Server-side allows offline sync but breaks P2P-only architecture |

**Installation:**
```bash
# No new dependencies required - all primitives available via existing cryptography library
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── groups/
│   ├── __init__.py           # Module exports
│   ├── models.py             # Group, GroupMember, GroupMessage models
│   ├── group_service.py      # Group lifecycle management
│   ├── sender_keys.py        # Sender Keys encryption implementation
│   ├── invite.py             # Invite link/code generation and parsing
│   └── call_mesh.py          # Group call mesh coordination
├── storage/
│   ├── groups.py             # NEW: Group CRUD operations
│   └── db.py                 # EXTEND: Add groups, group_members, sender_keys tables
├── network/
│   └── service.py            # EXTEND: Group messaging and call signaling
└── voice/
    └── call_service.py       # EXTEND: Support multiple peer connections for mesh
```

### Pattern 1: Sender Keys Protocol
**What:** Symmetric key encryption for group messages with per-sender chain ratcheting
**When to use:** All group message encryption

```python
# Source: Signal Sender Keys specification + adapted from existing codebase
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import hashlib
import os

class SenderKey:
    """
    Sender Key for group message encryption.

    Each group member maintains their own Sender Key, which consists of:
    - Chain Key: 32-byte symmetric key that advances with each message
    - Signature Key: Ed25519 key pair for message authentication
    """

    def __init__(self, chain_key: bytes = None, signature_private: Ed25519PrivateKey = None):
        self.chain_key = chain_key or os.urandom(32)
        self.signature_private = signature_private or Ed25519PrivateKey.generate()
        self.message_index = 0

    def derive_message_key(self) -> bytes:
        """Derive next message key from chain key using HKDF."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"SenderKey_MessageKey"
        )
        return hkdf.derive(self.chain_key)

    def advance_chain(self):
        """Advance chain key using one-way hash (provides forward secrecy)."""
        self.chain_key = hashlib.sha256(
            self.chain_key + b"SenderKey_ChainAdvance"
        ).digest()
        self.message_index += 1

    def encrypt_message(self, plaintext: bytes) -> tuple[bytes, bytes, int]:
        """
        Encrypt message for group broadcast.

        Returns:
            Tuple of (ciphertext, signature, message_index)
        """
        # Derive message key
        message_key = self.derive_message_key()

        # Encrypt with AES-GCM
        nonce = os.urandom(12)
        aesgcm = AESGCM(message_key)
        ciphertext = nonce + aesgcm.encrypt(nonce, plaintext, None)

        # Sign the ciphertext
        signature = self.signature_private.sign(ciphertext)

        current_index = self.message_index

        # Advance chain for forward secrecy
        self.advance_chain()

        return ciphertext, signature, current_index

    def export_public(self) -> dict:
        """Export public portion for distribution to group members."""
        return {
            "chain_key": self.chain_key.hex(),
            "signature_public": self.signature_private.public_key().public_bytes_raw().hex(),
            "message_index": self.message_index
        }
```

### Pattern 2: Sender Key Distribution
**What:** Encrypt Sender Key to each group member using existing pairwise Signal sessions
**When to use:** When joining group or rotating keys

```python
# Source: Adapted from existing message_crypto.py
from src.crypto.message_crypto import encrypt_message

async def distribute_sender_key(group_id: str, sender_key: SenderKey, members: list[int]):
    """
    Distribute our Sender Key to all group members.

    Uses existing pairwise Signal Protocol sessions to encrypt
    the Sender Key individually for each member.
    """
    key_data = json.dumps(sender_key.export_public()).encode()

    for member_contact_id in members:
        # Encrypt Sender Key using existing pairwise session
        encrypted = await encrypt_message(member_contact_id, key_data.decode())

        # Send via group signaling
        await send_group_message({
            "type": "sender_key_distribution",
            "group_id": group_id,
            "encrypted_key": encrypted.to_dict()
        }, member_contact_id)
```

### Pattern 3: WebRTC Mesh for Group Calls
**What:** Create RTCPeerConnection per peer pair for N-way calling
**When to use:** Group voice calls with 2-4 participants

```python
# Source: aiortc + existing VoiceCallService patterns
from aiortc import RTCPeerConnection, RTCConfiguration
from typing import Dict

class GroupCallMesh:
    """
    Manages mesh topology for group voice calls.

    Each participant maintains (N-1) peer connections.
    For 4 participants: 3 connections per peer, 6 total in mesh.
    """

    def __init__(self, local_public_key: str):
        self.local_key = local_public_key
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.audio_tracks: Dict[str, any] = {}
        self._mic_track = None

    async def join_call(self, group_id: str, participants: list[str]):
        """
        Join group call by establishing connections to all participants.

        Uses polite/impolite peer pattern based on public key ordering
        to handle simultaneous connection attempts.
        """
        for peer_key in participants:
            if peer_key == self.local_key:
                continue

            # Determine who initiates (higher key = impolite = initiates)
            if self.local_key > peer_key:
                await self._initiate_connection(peer_key)
            # else: wait for them to initiate

    async def _initiate_connection(self, peer_key: str):
        """Create connection to peer and send offer."""
        pc = await self._create_peer_connection(peer_key)

        # Add local audio track (shared across all connections)
        if self._mic_track:
            pc.addTrack(self._mic_track)

        # Create and send offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Wait for ICE gathering (aiortc doesn't support trickle ICE)
        while pc.iceGatheringState != "complete":
            await asyncio.sleep(0.1)

        # Send offer via signaling
        await self._send_signaling({
            "type": "group_call_offer",
            "to": peer_key,
            "sdp": pc.localDescription.sdp
        })

        self.peer_connections[peer_key] = pc

    async def handle_new_participant(self, peer_key: str):
        """Handle new participant joining the call."""
        if self.local_key > peer_key:
            await self._initiate_connection(peer_key)

    async def handle_participant_left(self, peer_key: str):
        """Handle participant leaving the call."""
        if peer_key in self.peer_connections:
            await self.peer_connections[peer_key].close()
            del self.peer_connections[peer_key]

    def get_bandwidth_estimate(self, num_participants: int) -> dict:
        """
        Estimate bandwidth requirements for mesh call.

        Audio: ~50 kbps per stream (Opus)
        Upload: (N-1) * 50 kbps
        Download: (N-1) * 50 kbps
        """
        streams = num_participants - 1
        audio_kbps = 50
        return {
            "upload_kbps": streams * audio_kbps,
            "download_kbps": streams * audio_kbps,
            "total_kbps": 2 * streams * audio_kbps,
            "warning": num_participants > 4
        }
```

### Pattern 4: Group Invite Codes
**What:** Cryptographically secure invite tokens with embedded group info
**When to use:** Sharing group invites

```python
# Source: stdlib secrets + base64
import secrets
import base64
import json
import time

def generate_invite_code(group_id: str, group_name: str, creator_public_key: str) -> str:
    """
    Generate a secure invite code for a group.

    Format: discordopus://join/<base64-encoded-payload>

    The payload contains group ID, name, creator key, expiry, and a random token
    to prevent enumeration attacks.
    """
    payload = {
        "g": group_id,  # Group ID
        "n": group_name[:50],  # Group name (truncated)
        "c": creator_public_key,  # Creator's public key
        "e": int(time.time()) + (7 * 24 * 3600),  # Expires in 7 days
        "t": secrets.token_urlsafe(16)  # Random token for uniqueness
    }

    payload_json = json.dumps(payload)
    encoded = base64.urlsafe_b64encode(payload_json.encode()).decode()

    return f"discordopus://join/{encoded}"

def parse_invite_code(code: str) -> dict:
    """Parse and validate an invite code."""
    if not code.startswith("discordopus://join/"):
        raise ValueError("Invalid invite code format")

    encoded = code[len("discordopus://join/"):]

    try:
        payload_json = base64.urlsafe_b64decode(encoded)
        payload = json.loads(payload_json)
    except Exception:
        raise ValueError("Invalid invite code encoding")

    # Check expiry
    if payload.get("e", 0) < time.time():
        raise ValueError("Invite code expired")

    return {
        "group_id": payload["g"],
        "group_name": payload["n"],
        "creator_public_key": payload["c"]
    }
```

### Pattern 5: Group Call Signaling Coordination
**What:** Coordinate call state across multiple participants
**When to use:** Managing group call join/leave/state

```python
# Source: MDN WebRTC, adapted from existing signaling patterns
SIGNALING_MESSAGE_TYPES = {
    "group_call_start": "Initiator announces new group call",
    "group_call_join": "Participant announces joining",
    "group_call_offer": "WebRTC offer to specific peer",
    "group_call_answer": "WebRTC answer from peer",
    "group_call_leave": "Participant leaving call",
    "group_call_end": "Call terminated",
}

async def handle_group_call_signaling(message: dict, mesh: GroupCallMesh):
    """Handle incoming group call signaling messages."""
    msg_type = message.get("type")

    if msg_type == "group_call_start":
        # Someone started a group call
        group_id = message["group_id"]
        initiator = message["from"]
        # Notify UI of incoming group call

    elif msg_type == "group_call_join":
        # New participant joining
        peer_key = message["from"]
        await mesh.handle_new_participant(peer_key)

    elif msg_type == "group_call_offer":
        # WebRTC offer from peer
        peer_key = message["from"]
        sdp = message["sdp"]
        await mesh.handle_offer(peer_key, sdp)

    elif msg_type == "group_call_answer":
        # WebRTC answer from peer
        peer_key = message["from"]
        sdp = message["sdp"]
        await mesh.handle_answer(peer_key, sdp)

    elif msg_type == "group_call_leave":
        # Participant left
        peer_key = message["from"]
        await mesh.handle_participant_left(peer_key)
```

### Anti-Patterns to Avoid

- **Don't reuse Double Ratchet for groups:** Pairwise Double Ratchet encrypts separately for each recipient; Sender Keys broadcast-encrypts once. Wrong tool for the job.
- **Don't create mesh with 5+ participants:** Bandwidth scales as O(N^2); 5 participants = 4 connections each = ~400 kbps audio alone. SFU needed for larger groups.
- **Don't store group private keys in database:** Like identity keys, Sender Key signature private keys should be DPAPI-encrypted separately.
- **Don't skip key rotation on member removal:** Removed members still have old Sender Keys; must rotate to prevent them decrypting future messages.
- **Don't use sequential invite codes:** Makes enumeration attacks possible; always use cryptographic randomness.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Symmetric ratcheting | Custom hash chain | HKDF from cryptography | Proper key derivation with domain separation |
| Random invite tokens | uuid4() or similar | secrets.token_urlsafe() | Cryptographically secure randomness |
| Message signing | Custom MAC | Ed25519 signatures | Already using Ed25519 for identity; non-repudiation |
| Encrypted storage | Custom file encryption | SQLCipher (existing) | Already handles all storage encryption |
| Audio encoding | Custom Opus wrapper | aiortc built-in | Already handles WebRTC audio codecs |
| Key serialization | Custom binary format | JSON + hex encoding | Human-readable, debuggable, matches existing patterns |

**Key insight:** The cryptographic primitives (HKDF, AES-GCM, Ed25519) are already in use. The innovation is composing them into the Sender Keys pattern, not implementing new crypto.

## Common Pitfalls

### Pitfall 1: Sender Key Synchronization Across Devices
**What goes wrong:** Different devices have different Sender Key states; messages decrypt on one device but not another.
**Why it happens:** Each device generates independent Sender Keys; no synchronization mechanism.
**How to avoid:** Phase 7 scope is single-device only. Document this limitation. Future multi-device support would need key export/sync protocol.
**Warning signs:** User reports "messages not decrypting" on secondary device.

### Pitfall 2: Mesh Call ICE Gathering Timeout
**What goes wrong:** With 4 peers, setting up 3 connections takes too long; users see "connecting..." forever.
**Why it happens:** Each RTCPeerConnection does full ICE gathering (no trickle in aiortc); sequential setup multiplies latency.
**How to avoid:**
- Create peer connections in parallel (asyncio.gather)
- Set reasonable timeout per connection (30s)
- Show progress ("Connected to 2/3 participants")
**Warning signs:** Call setup takes >30 seconds for 3+ participants.

### Pitfall 3: Member Removal Without Key Rotation
**What goes wrong:** Removed member can still decrypt new group messages.
**Why it happens:** They still have valid Sender Keys from before removal.
**How to avoid:** When member is removed, all remaining members must:
1. Generate new Sender Keys
2. Distribute to all remaining members
3. Clear old keys
**Warning signs:** Removed user reports still seeing messages.

### Pitfall 4: Group State Desync
**What goes wrong:** Different members have different views of who's in the group.
**Why it happens:** P2P-only means no authoritative server; network partitions cause divergence.
**How to avoid:**
- Use group creator as tie-breaker for conflicts
- Include member list hash in every message
- Periodic sync messages
**Warning signs:** "User X not in group" errors when they think they are.

### Pitfall 5: Mesh Bandwidth Exhaustion
**What goes wrong:** Audio becomes choppy or connections drop during 4-person call.
**Why it happens:** Upload bandwidth saturated: 3 streams * 50kbps = 150kbps minimum, more with quality buffers.
**How to avoid:**
- Display bandwidth warning for 4+ participants
- Limit Opus bitrate to 24kbps for group calls
- Show connection quality indicators
**Warning signs:** Audio dropouts, "poor connection" during group calls only.

### Pitfall 6: Invite Code Replay Attacks
**What goes wrong:** Shared invite link is used after group was meant to be closed.
**Why it happens:** Invite codes don't expire or aren't revoked.
**How to avoid:**
- Include expiry timestamp in invite payload
- Allow group creator to revoke specific invites
- Track which invites have been used
**Warning signs:** Unexpected members joining "closed" groups.

## Code Examples

Verified patterns from official sources and existing codebase:

### HKDF Key Derivation for Sender Keys
```python
# Source: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

def derive_sender_key_components(master_secret: bytes) -> tuple[bytes, bytes]:
    """
    Derive chain key and signing key from master secret.

    Uses HKDF with domain separation for each key type.
    """
    # Derive chain key (32 bytes)
    chain_key_hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"DiscordOpus_SenderKey_ChainKey_v1"
    )
    chain_key = chain_key_hkdf.derive(master_secret)

    # Derive signing key seed (32 bytes) - used to generate Ed25519 key
    signing_seed_hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"DiscordOpus_SenderKey_SigningKey_v1"
    )
    signing_seed = signing_seed_hkdf.derive(master_secret)

    return chain_key, signing_seed
```

### SQLCipher Schema for Groups
```sql
-- Groups table: local group metadata
CREATE TABLE IF NOT EXISTS groups (
    id TEXT PRIMARY KEY,                    -- UUID
    name TEXT NOT NULL,
    creator_public_key TEXT NOT NULL,       -- Ed25519 public key of creator
    created_at INTEGER NOT NULL,            -- Unix timestamp ms
    updated_at INTEGER NOT NULL,
    invite_code TEXT,                       -- Current active invite code
    is_active INTEGER DEFAULT 1             -- 0 if user left the group
);

-- Group members table: members of each group
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT NOT NULL,
    public_key TEXT NOT NULL,               -- Member's Ed25519 public key
    display_name TEXT NOT NULL,
    joined_at INTEGER NOT NULL,
    is_admin INTEGER DEFAULT 0,             -- Creator is admin
    FOREIGN KEY (group_id) REFERENCES groups(id),
    UNIQUE(group_id, public_key)
);

-- Sender keys table: Sender Keys received from group members
CREATE TABLE IF NOT EXISTS sender_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT NOT NULL,
    sender_public_key TEXT NOT NULL,        -- Who this key belongs to
    chain_key BLOB NOT NULL,                -- Current chain key state
    signature_public BLOB NOT NULL,         -- Ed25519 public key for verification
    message_index INTEGER NOT NULL,         -- Last processed message index
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    UNIQUE(group_id, sender_public_key)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_group_members ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_sender_keys ON sender_keys(group_id, sender_public_key);
```

### Group Message Format
```python
# Group message protocol format
GROUP_MESSAGE = {
    "type": "group_message",
    "group_id": "uuid-group-id",
    "message_id": "uuid-message-id",
    "sender_public_key": "hex-ed25519-public",
    "timestamp": 1706700000000,  # ms since epoch

    # Sender Key encrypted payload
    "message_index": 42,  # Chain position for key derivation
    "ciphertext": "hex-aes-gcm-ciphertext",  # AES-GCM(message_key, plaintext)
    "signature": "hex-ed25519-signature",  # Ed25519.sign(ciphertext)

    # Inner message structure (decrypted)
    # {
    #     "body": "Hello group!",
    #     "reply_to": null  # or message ID
    # }
}

# Sender Key distribution message (encrypted per-recipient via existing Signal session)
SENDER_KEY_DISTRIBUTION = {
    "type": "sender_key_distribution",
    "group_id": "uuid-group-id",
    "sender_public_key": "hex-ed25519-public",

    # Encrypted per-recipient using existing pairwise Signal Protocol
    "encrypted_key": {
        "header": { ... },
        "ciphertext": "hex-ciphertext",
        "ephemeral_key": "hex-key-if-first-message"
    }
    # Decrypts to:
    # {
    #     "chain_key": "hex-32-bytes",
    #     "signature_public": "hex-32-bytes",
    #     "message_index": 0
    # }
}
```

### Secure Invite Token Generation
```python
# Source: Python stdlib secrets documentation
import secrets
import hashlib

def generate_invite_token() -> str:
    """
    Generate a cryptographically secure invite token.

    Uses secrets.token_urlsafe for true randomness.
    URL-safe encoding for sharing in links.
    """
    return secrets.token_urlsafe(24)  # 32 characters, 192 bits of entropy

def hash_invite_token(token: str) -> str:
    """
    Hash invite token for storage (don't store plaintext).

    Store hash, not token, to prevent DB leak exposing valid invites.
    """
    return hashlib.sha256(token.encode()).hexdigest()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pairwise encryption for groups | Sender Keys / MLS | ~2018+ | O(N) instead of O(N^2) encryption for N members |
| Full mesh for large groups | SFU/MCU | ~2020+ | Mesh limited to 4-6; SFU for 5+ participants |
| Static group keys | Ratcheting chain keys | Signal Sender Keys | Forward secrecy for group messages |
| Server-managed groups | Decentralized groups | Matrix/Session | True P2P group management possible |

**Deprecated/outdated:**
- **Static symmetric key for all group messages:** No forward secrecy; one key compromise exposes all history
- **Encrypting to each member separately:** O(N^2) complexity; doesn't scale past small groups
- **Trusting removed members:** Must rotate keys on any membership change

## Open Questions

Things that couldn't be fully resolved:

1. **Sender Key library availability in Python**
   - What we know: No production-ready Sender Keys library for Python; Signal's libsignal has it but Rust-only
   - What's unclear: Whether to port from libsignal-rust or build from primitives
   - Recommendation: Build from primitives using existing cryptography library; pattern is simpler than full Double Ratchet

2. **Group state conflict resolution without server**
   - What we know: P2P-only means no authoritative source for group membership
   - What's unclear: How to handle split-brain scenarios where different members have different views
   - Recommendation: Use group creator as tiebreaker; include member list version in messages; periodic full sync

3. **Optimal mesh call participant limit**
   - What we know: 4 is commonly cited; some sources say 6 possible
   - What's unclear: Actual limit with aiortc on typical hardware/bandwidth
   - Recommendation: Start with 4 limit, show warning at 5+, allow user override with "may degrade quality" notice

4. **Sender Key rotation frequency**
   - What we know: Signal rotates on member removal; WhatsApp rotates every 50 messages or when member changes
   - What's unclear: Optimal rotation policy for our use case
   - Recommendation: Rotate on member removal only; simpler and sufficient for small groups

5. **Group call join coordination**
   - What we know: Perfect negotiation pattern helps with simultaneous offers
   - What's unclear: How to sequence connection setup to minimize "connecting" time
   - Recommendation: Use public key ordering (higher key initiates); parallel connection attempts

## Sources

### Primary (HIGH confidence)
- [Signal Protocol Double Ratchet Specification](https://signal.org/docs/specifications/doubleratchet/) - Chain key ratchet mechanism (adapted for Sender Keys)
- [cryptography.io HKDF Documentation](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/) - Key derivation for Sender Keys
- [MDN WebRTC Perfect Negotiation](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Perfect_negotiation) - Polite/impolite peer pattern
- [Python secrets module](https://docs.python.org/3/library/secrets.html) - Secure random token generation
- Existing codebase: `src/crypto/signal_session.py` - Ratchet patterns to adapt

### Secondary (MEDIUM confidence)
- [E2E Encrypted Groups Guide](https://blog.bigwhalelabs.com/an-incomplete-guide-to-e2e-encrypted-groups/) - Sender Keys conceptual overview
- [WebRTC Mesh Topology Overview](https://antmedia.io/webrtc-network-topology/) - Mesh vs SFU comparison, bandwidth calculations
- [aiortc GitHub](https://github.com/aiortc/aiortc) - Multiple RTCPeerConnection support confirmed
- [VideoSDK Group Call Guide](https://www.videosdk.live/developer-hub/webrtc/webrtc-group-video-call) - Mesh connection patterns

### Tertiary (LOW confidence - needs validation)
- [WhatsApp Sender Keys paper (2023)](https://eprint.iacr.org/2023/1385.pdf) - Academic analysis (PDF not parseable)
- Various blog posts on group encryption patterns

## Metadata

**Confidence breakdown:**
- Sender Keys architecture: MEDIUM - Pattern clear from specs, but no Python library; custom implementation required
- WebRTC mesh: HIGH - Well-documented pattern, existing aiortc proven for 1:1
- Group management: MEDIUM - Local-only pattern straightforward, but sync challenges in P2P
- Group call signaling: MEDIUM - Patterns clear, but integration with existing service needs planning
- Database schema: HIGH - Extension of existing proven patterns

**Research date:** 2026-01-31
**Valid until:** ~2026-03-31 (60 days - stable cryptographic patterns, WebRTC mature)

**Validation needed before planning:**
- Test aiortc with 3 simultaneous RTCPeerConnections for 4-person call
- Verify Sender Key encryption/decryption round-trip with custom implementation
- Measure actual bandwidth usage for 4-person audio mesh on typical connection
- Confirm group message format works with existing data channel 16KB chunk limit
