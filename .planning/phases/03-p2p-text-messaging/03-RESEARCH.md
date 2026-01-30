# Phase 3: P2P Text Messaging - Research

**Researched:** 2026-01-30
**Domain:** WebRTC Data Channels, Signal Protocol (E2E Encryption), Message Storage
**Confidence:** HIGH

## Summary

Phase 3 implements P2P text messaging with E2E encryption using WebRTC data channels for transport and Signal Protocol (X3DH + Double Ratchet) for cryptographic security. The existing signaling infrastructure from Phase 2 handles connection establishment, while aiortc provides the WebRTC implementation.

Key findings:
1. **aiortc** (v1.14.0) provides complete WebRTC data channel support for Python 3.13, with reliable ordered delivery by default
2. **python-doubleratchet** (v1.3.0) and **python-x3dh** (v1.1.0) from Syndace provide production-ready Signal Protocol implementations
3. aiortc does NOT support trickle ICE - must wait for ICE gathering to complete before sending offer/answer
4. Data channels should be created BEFORE SDP negotiation to include them in session description
5. Message persistence uses existing SQLCipher infrastructure with new tables for messages, sessions, and reactions

**Primary recommendation:** Use aiortc for WebRTC transport with reliable ordered data channels, Syndace's python-doubleratchet + python-x3dh for Signal Protocol encryption, and extend existing SQLCipher schema for message storage.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiortc | 1.14.0 | WebRTC data channels | Pure Python, asyncio-native, supports Python 3.13, actively maintained |
| DoubleRatchet | 1.3.0 | Signal Protocol encryption | Production-stable, implements Signal spec, MIT license |
| X3DH | 1.1.0 | Key agreement protocol | Companion to DoubleRatchet from same author, handles session initialization |
| cryptography | (existing) | Cryptographic primitives | Already in use for Ed25519/X25519, provides HKDF, AES-GCM |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlcipher3 | (existing) | Encrypted message storage | Already configured, extend schema for messages |
| websockets | (existing) | Signaling transport | Already configured for offer/answer exchange |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| aiortc | WebRTC browser-only | aiortc enables Python-Python connections without browser |
| python-doubleratchet | Custom implementation | Syndace lib is tested, maintained, follows spec exactly |
| SQLCipher messages | Separate message files | Database provides better querying, atomic operations |

**Installation:**
```bash
pip install aiortc DoubleRatchet X3DH
```

**Note on X3DH dependencies:** X3DH requires libsodium system library. On Windows, prebuilt binaries are available for amd64.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── network/
│   ├── signaling_client.py    # (existing) WebSocket signaling
│   ├── peer_connection.py     # NEW: aiortc RTCPeerConnection manager
│   ├── data_channel.py        # NEW: Data channel abstraction
│   └── service.py             # (extend) Add P2P connection lifecycle
├── crypto/
│   ├── identity.py            # (existing) Ed25519/X25519 keys
│   ├── signal_session.py      # NEW: X3DH + Double Ratchet session
│   └── message_crypto.py      # NEW: Message encryption/decryption
├── storage/
│   ├── db.py                  # (extend) New tables for messages, sessions
│   ├── messages.py            # NEW: Message CRUD operations
│   └── signal_store.py        # NEW: Signal Protocol state persistence
└── api/
    └── bridge.py              # (extend) Messaging API methods
```

### Pattern 1: WebRTC Connection Lifecycle
**What:** Manage P2P connections through signaling server
**When to use:** When establishing connection to a contact

```python
# Source: aiortc documentation + research
async def create_peer_connection(contact_public_key: str) -> RTCPeerConnection:
    """Create and configure RTCPeerConnection for a contact."""
    from aiortc import RTCPeerConnection, RTCConfiguration
    from src.network.stun import get_ice_servers

    config = RTCConfiguration(iceServers=get_ice_servers())
    pc = RTCPeerConnection(configuration=config)

    # Create data channel BEFORE creating offer
    channel = pc.createDataChannel("messages", ordered=True)

    # Create offer and wait for ICE gathering to complete
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # CRITICAL: aiortc doesn't support trickle ICE
    # Must wait for gathering to complete
    while pc.iceGatheringState != "complete":
        await asyncio.sleep(0.1)

    # Now localDescription.sdp contains all ICE candidates
    return pc, channel
```

### Pattern 2: Signal Protocol Session Initialization
**What:** Establish encrypted session using X3DH then Double Ratchet
**When to use:** First message to a contact or session recovery

```python
# Source: Signal Protocol specification + python-doubleratchet docs
# Simplified conceptual pattern - actual implementation requires subclassing

class SignalSession:
    """Manages E2E encrypted messaging session with a contact."""

    async def initialize_as_sender(self, their_x25519_public: bytes):
        """Initialize session as message sender (Alice role)."""
        # 1. Perform X3DH key agreement
        # 2. Use shared secret to initialize Double Ratchet
        # 3. Store session state in database
        pass

    async def initialize_as_receiver(self, their_ephemeral_key: bytes):
        """Initialize session as receiver (Bob role)."""
        # 1. Complete X3DH with received ephemeral key
        # 2. Initialize Double Ratchet from shared secret
        # 3. Store session state
        pass

    def encrypt_message(self, plaintext: bytes) -> tuple[bytes, bytes]:
        """Encrypt message, returns (header, ciphertext)."""
        # Double Ratchet advances sending chain
        # Returns header (contains DH ratchet key) and ciphertext
        pass

    def decrypt_message(self, header: bytes, ciphertext: bytes) -> bytes:
        """Decrypt message, handles out-of-order delivery."""
        # Double Ratchet may advance receiving chain or use stored keys
        pass
```

### Pattern 3: Message Protocol Format
**What:** JSON message format for data channel communication
**When to use:** All P2P messaging

```python
# Message types sent over data channel
MESSAGE_TYPES = {
    "text": "Regular text message",
    "edit": "Edit existing message",
    "delete": "Delete message",
    "reaction": "Emoji reaction",
    "typing": "Typing indicator",
    "ack": "Delivery acknowledgment",
}

# Example encrypted message envelope
{
    "type": "text",
    "id": "uuid-message-id",
    "timestamp": 1706600000000,  # ms since epoch
    "header": "base64-double-ratchet-header",
    "ciphertext": "base64-encrypted-content",
}

# Decrypted content structure
{
    "body": "Hello!",
    "reply_to": null,  # or message ID
}

# Edit message
{
    "type": "edit",
    "id": "new-uuid",
    "target_id": "original-message-uuid",
    "header": "...",
    "ciphertext": "...",  # Contains new body
}

# Reaction
{
    "type": "reaction",
    "id": "uuid",
    "target_id": "message-uuid",
    "emoji": "thumbsup",  # Unicode emoji or shortcode
    "action": "add",  # or "remove"
}

# Typing indicator (not encrypted, ephemeral)
{
    "type": "typing",
    "active": true,
}
```

### Pattern 4: Connection State Handling
**What:** Monitor and react to P2P connection state changes
**When to use:** Detecting disconnections, triggering reconnection

```python
# Source: aiortc API documentation
@pc.on("connectionstatechange")
async def on_connection_state_change():
    state = pc.connectionState
    if state == "connected":
        # Connection established, can send messages
        pass
    elif state == "failed":
        # ICE connection failed - likely NAT issues
        # Notify user, offer retry
        await pc.close()
    elif state == "disconnected":
        # Temporary disconnect, may recover
        # Start reconnection timer
        pass
    elif state == "closed":
        # Connection terminated
        pass
```

### Anti-Patterns to Avoid
- **Creating data channels after SDP negotiation:** Requires renegotiation, adds latency. Create channels BEFORE createOffer().
- **Expecting trickle ICE in aiortc:** aiortc requires gathering to complete before sending offer. Don't send offer immediately after setLocalDescription.
- **Storing private keys in database:** Continue pattern from Phase 1 - session state in DB, but never private keys.
- **Blocking on message send:** Use async patterns, queue messages if connection temporarily down.
- **Re-encrypting on edit/delete:** Only the edited content needs encryption, not the entire history.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Double Ratchet | Custom ratcheting | python-doubleratchet | Crypto is hard, spec is complex, library is tested |
| X3DH key exchange | Custom DH protocol | python-x3dh | Handles one-time prekeys, signed prekeys correctly |
| WebRTC transport | Raw UDP/TCP | aiortc | Handles ICE, DTLS, SCTP properly |
| Message ordering | Custom sequence numbers | SCTP ordered mode | Built into WebRTC data channels |
| Reliability | Custom ACK/retry | SCTP reliable mode | Data channels handle retransmission |
| UTF-8 encoding | Manual encoding | Data channel send() | Automatic for strings |

**Key insight:** WebRTC data channels with ordered=True (default) provide reliable, in-order message delivery. Don't implement custom reliability on top.

## Common Pitfalls

### Pitfall 1: aiortc Trickle ICE Limitation
**What goes wrong:** Attempting to send offer immediately after setLocalDescription, expecting trickle ICE
**Why it happens:** Browser WebRTC supports trickle ICE, aiortc does not
**How to avoid:** Always wait for `pc.iceGatheringState == "complete"` before sending offer/answer
**Warning signs:** Connection stays in "checking" state forever, no ICE candidates exchanged

### Pitfall 2: Data Channel Creation Timing
**What goes wrong:** Creating data channel after createOffer() requires renegotiation
**Why it happens:** Data channels must be in SDP to be negotiated
**How to avoid:** Create all needed data channels BEFORE calling createOffer()
**Warning signs:** `ondatachannel` event never fires on remote peer

### Pitfall 3: Double Ratchet State Persistence
**What goes wrong:** Session state not persisted, messages can't decrypt after restart
**Why it happens:** Double Ratchet state includes chain keys, message counters, skipped keys
**How to avoid:** Serialize and persist session state after every encrypt/decrypt operation
**Warning signs:** "Unable to decrypt" errors after app restart

### Pitfall 4: Signal Protocol Session Recovery
**What goes wrong:** Out-of-order messages cause decryption failures
**Why it happens:** Double Ratchet stores limited skipped message keys (default ~1000)
**How to avoid:** Implement proper message acknowledgments, limit window of unacked messages
**Warning signs:** Messages decrypt fine in order, fail randomly when delayed

### Pitfall 5: Symmetric NAT Connection Failures
**What goes wrong:** WebRTC connection fails with "failed" ICE state
**Why it happens:** Project uses STUN only (no TURN), symmetric NAT blocks connections
**How to avoid:** Clear error messaging to user, document limitation, suggest network changes
**Warning signs:** Works on some networks but not others, iceConnectionState goes to "failed"

### Pitfall 6: Typing Indicator Spam
**What goes wrong:** Typing indicator sent on every keystroke overwhelms channel
**Why it happens:** No throttling on typing events
**How to avoid:** Throttle to max one indicator per 3 seconds (Slack pattern)
**Warning signs:** High message volume, laggy UI during fast typing

## Code Examples

Verified patterns from official sources:

### aiortc Peer Connection Setup
```python
# Source: https://aiortc.readthedocs.io/en/latest/api.html
from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription
import asyncio

async def setup_peer_connection(ice_servers: list[dict]):
    config = RTCConfiguration(iceServers=ice_servers)
    pc = RTCPeerConnection(configuration=config)

    # Monitor connection state
    @pc.on("connectionstatechange")
    async def on_state_change():
        print(f"Connection state: {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()

    return pc
```

### aiortc Data Channel Usage
```python
# Source: https://github.com/aiortc/aiortc/blob/main/examples/datachannel-cli/cli.py
# Sender side - create channel
channel = pc.createDataChannel("messages", ordered=True)

@channel.on("open")
def on_open():
    print("Data channel open")
    channel.send("Hello!")

@channel.on("message")
def on_message(message):
    print(f"Received: {message}")

# Receiver side - accept channel
@pc.on("datachannel")
def on_datachannel(channel):
    @channel.on("message")
    def on_message(message):
        print(f"Received: {message}")
        channel.send("Pong!")
```

### Offer/Answer Exchange (non-trickle)
```python
# Source: aiortc documentation + GitHub issues
async def create_offer_with_candidates(pc: RTCPeerConnection) -> str:
    """Create offer with all ICE candidates included."""
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # Wait for ICE gathering to complete (no trickle)
    while pc.iceGatheringState != "complete":
        await asyncio.sleep(0.1)

    # localDescription now contains all candidates in SDP
    return pc.localDescription.sdp

async def handle_offer(pc: RTCPeerConnection, offer_sdp: str) -> str:
    """Handle incoming offer and create answer."""
    offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Wait for ICE gathering
    while pc.iceGatheringState != "complete":
        await asyncio.sleep(0.1)

    return pc.localDescription.sdp
```

### SQLCipher Message Schema
```sql
-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,           -- UUID
    conversation_id INTEGER NOT NULL,  -- Contact ID for 1:1
    sender_id TEXT NOT NULL,       -- Public key of sender
    type TEXT NOT NULL DEFAULT 'text',  -- text, edit, delete
    body TEXT,                     -- Decrypted message body (encrypted at rest by SQLCipher)
    reply_to TEXT,                 -- Message ID being replied to
    edited INTEGER DEFAULT 0,      -- 1 if message was edited
    deleted INTEGER DEFAULT 0,     -- 1 if soft-deleted
    timestamp INTEGER NOT NULL,    -- Unix timestamp ms
    received_at INTEGER,           -- When we received it
    FOREIGN KEY (conversation_id) REFERENCES contacts(id)
);

-- Reactions table
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,       -- Who reacted
    emoji TEXT NOT NULL,           -- Unicode emoji
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(id),
    UNIQUE(message_id, sender_id, emoji)
);

-- Signal Protocol session state
CREATE TABLE IF NOT EXISTS signal_sessions (
    contact_id INTEGER PRIMARY KEY,
    session_state BLOB NOT NULL,   -- Serialized DoubleRatchet state
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_reactions_message ON reactions(message_id);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| OTR encryption | Signal Protocol (Double Ratchet) | ~2013 | Better forward secrecy, async support |
| WebSocket for P2P | WebRTC data channels | Mature | NAT traversal, lower latency |
| Custom key exchange | X3DH | Standard | Proven security, async initialization |

**Deprecated/outdated:**
- OTR (Off-the-Record Messaging): Replaced by Signal Protocol for better async support
- Manual ICE candidate exchange: aiortc bundles candidates in SDP (non-trickle)
- audioop module: Removed in Python 3.13, aiortc 1.14.0 handles this

## Open Questions

Things that couldn't be fully resolved:

1. **X3DH One-Time Prekeys Management**
   - What we know: X3DH spec recommends one-time prekeys for enhanced forward secrecy
   - What's unclear: Without a central server storing prekeys, how to handle async initialization
   - Recommendation: For P2P direct connection, use simplified X3DH without one-time prekeys (just identity + signed prekey)

2. **Offline Message Queue**
   - What we know: Users may try to send when contact is offline
   - What's unclear: Best approach - queue locally, use signaling server relay, or just error
   - Recommendation: Queue locally, send when connection re-establishes, show "pending" status in UI

3. **Multi-Device Session Management**
   - What we know: Phase 3 scope is single device
   - What's unclear: How sessions would sync across devices
   - Recommendation: Defer to future phase, document session as device-specific

## Sources

### Primary (HIGH confidence)
- [aiortc API Reference](https://aiortc.readthedocs.io/en/latest/api.html) - RTCPeerConnection, RTCDataChannel API
- [aiortc GitHub Examples](https://github.com/aiortc/aiortc/blob/main/examples/datachannel-cli/cli.py) - Data channel patterns
- [Signal Protocol Double Ratchet Specification](https://signal.org/docs/specifications/doubleratchet/) - Algorithm details
- [Signal Protocol X3DH Specification](https://signal.org/docs/specifications/x3dh/) - Key agreement
- [python-doubleratchet PyPI](https://pypi.org/project/DoubleRatchet/) - v1.3.0, Python 3.10-3.14
- [python-doubleratchet GitHub](https://github.com/Syndace/python-doubleratchet) - Usage, examples
- [python-x3dh GitHub](https://github.com/Syndace/python-x3dh) - X3DH implementation

### Secondary (MEDIUM confidence)
- [aiortc GitHub Issues #1344](https://github.com/aiortc/aiortc/issues/1344) - Trickle ICE limitation confirmed
- [aiortc GitHub Issues #359](https://github.com/aiortc/aiortc/issues/359) - Connection state handling
- [WebRTC for the Curious - Data Communication](https://webrtcforthecurious.com/docs/07-data-communication/) - Data channel architecture
- [RTCDataChannel MDN](https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/createDataChannel) - Channel options

### Tertiary (LOW confidence)
- Various blog posts on Signal Protocol implementation (for conceptual understanding, not implementation details)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified versions, PyPI metadata, official documentation
- Architecture: HIGH - Based on aiortc official examples and Signal spec
- WebRTC patterns: HIGH - aiortc docs + confirmed behavior from GitHub issues
- Signal Protocol integration: MEDIUM - Libraries exist but require subclassing/configuration
- Message persistence schema: HIGH - Standard patterns, SQLite/SQLCipher well understood

**Research date:** 2026-01-30
**Valid until:** 2026-03-01 (60 days - stable libraries, well-documented protocols)
