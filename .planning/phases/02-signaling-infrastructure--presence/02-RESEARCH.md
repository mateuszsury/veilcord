# Phase 2: Signaling Infrastructure & Presence - Research

**Researched:** 2026-01-30
**Domain:** WebSocket client/server, Ed25519 authentication, presence protocol, STUN integration
**Confidence:** HIGH

## Summary

Phase 2 establishes the signaling infrastructure required for P2P connections in Phase 3. The standard approach uses the **websockets** library (v16.0) for Python asyncio-based WebSocket client connections, **FastAPI** for the signaling server with WSS support, and **aiortc** for ICE candidate generation via STUN servers.

For authentication, Ed25519 signature-based challenge-response authentication is the modern standard over JWT/password schemes, using the existing **cryptography** library from Phase 1. Presence is managed via JSON message protocol with server-side state tracking and broadcast to connected clients.

The ecosystem is mature and well-documented. The websockets library provides built-in exponential backoff reconnection, FastAPI offers native WebSocket support with dependency injection for authentication, and free public STUN servers (Google's stun.l.google.com:19302) are production-ready for development.

**Primary recommendation:** Use websockets library's async iterator pattern for auto-reconnection, FastAPI ConnectionManager pattern for presence broadcasting, Ed25519 challenge-response for authentication, and Google STUN servers for Phase 3 ICE candidate gathering.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| websockets | 16.0+ | WebSocket client (asyncio) | Official Python WebSocket library, built-in reconnection with exponential backoff, maintained by IETF contributor |
| FastAPI | Latest | WebSocket signaling server | Native WebSocket support, dependency injection for auth, excellent performance with uvicorn |
| cryptography | 46.0.4+ | Ed25519 signing/verification | Already in use from Phase 1, official Python crypto library, hazmat module for Ed25519 |
| aiortc | Latest | WebRTC/ICE candidate generation | Pure Python WebRTC implementation, STUN integration for Phase 3 P2P setup |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uvicorn | Latest | ASGI server for FastAPI | Required to run FastAPI WebSocket server, production-ready |
| ssl (stdlib) | N/A | WSS certificate handling | Secure WebSocket connections (wss://), TLS context for production |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| websockets | aiohttp | aiohttp is heavier (full HTTP client/server), websockets is focused and lighter for client-only use |
| FastAPI | aiohttp server | aiohttp offers more low-level control but lacks FastAPI's dependency injection and automatic docs |
| Ed25519 auth | JWT tokens | JWT requires session management and token refresh complexity, Ed25519 signatures are stateless |

**Installation:**

```bash
# Client-side (Python backend)
pip install websockets>=16.0

# Server-side (separate signaling server project)
pip install fastapi uvicorn websockets

# Already installed from Phase 1
# cryptography>=46.0.4
# aiortc (for Phase 3, but configure STUN in Phase 2)
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── network/
│   ├── signaling_client.py   # WebSocket client with auto-reconnect
│   ├── presence.py            # Presence state management
│   ├── auth.py                # Ed25519 challenge-response auth
│   └── stun.py                # STUN server configuration (for Phase 3)
├── api/
│   └── bridge.py              # Add network status callbacks for UI
└── storage/
    └── contacts.py            # Update contact online status

# Separate signaling server repository (deployed independently)
signaling-server/
├── main.py                    # FastAPI app with WebSocket routes
├── auth.py                    # Ed25519 signature verification
├── presence.py                # Presence state tracking & broadcast
└── requirements.txt           # fastapi, uvicorn, cryptography
```

### Pattern 1: WebSocket Client with Auto-Reconnection

**What:** Use websockets library's async iterator pattern for automatic exponential backoff reconnection
**When to use:** All WebSocket client connections requiring resilience
**Example:**

```python
# Source: https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html
from websockets.asyncio.client import connect
import asyncio

async def signaling_client():
    uri = "wss://signaling.example.com/ws"

    async for websocket in connect(uri):
        try:
            # Authenticate on connection
            await authenticate(websocket)

            # Receive messages in loop
            async for message in websocket:
                await process_message(message)

        except websockets.exceptions.ConnectionClosed:
            # Auto-reconnect with exponential backoff
            continue
```

**Key config:**
- `ping_interval=20` (default): Sends ping every 20s
- `ping_timeout=20` (default): Expects pong within 20s
- `open_timeout=10` (default): Connection establishment deadline
- Built-in exponential backoff retries transient errors (EOFError, OSError, asyncio.TimeoutError)

### Pattern 2: Ed25519 Challenge-Response Authentication

**What:** Server sends random challenge, client signs with private key, server verifies with public key
**When to use:** WebSocket authentication without JWT/session complexity
**Example:**

```python
# Source: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import json
import base64

# Client-side authentication
async def authenticate(websocket):
    # Receive challenge from server
    msg = json.loads(await websocket.recv())
    challenge = base64.b64decode(msg['challenge'])

    # Sign challenge with Ed25519 identity key (from Phase 1)
    private_key = load_identity_key()  # From storage
    signature = private_key.sign(challenge)

    # Send response with public key + signature
    public_bytes = private_key.public_key().public_bytes_raw()
    response = {
        'type': 'auth_response',
        'public_key': base64.b64encode(public_bytes).decode(),
        'signature': base64.b64encode(signature).decode()
    }
    await websocket.send(json.dumps(response))

    # Wait for auth confirmation
    confirm = json.loads(await websocket.recv())
    if confirm['type'] != 'auth_success':
        raise AuthenticationError("Auth failed")

# Server-side verification
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def verify_challenge(challenge: bytes, public_key_bytes: bytes, signature: bytes) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, challenge)
        return True
    except Exception:
        return False
```

### Pattern 3: Presence Broadcasting with FastAPI ConnectionManager

**What:** Track active WebSocket connections and broadcast presence changes to all clients
**When to use:** Signaling server managing online/offline status for multiple clients
**Example:**

```python
# Source: https://fastapi.tiangolo.com/advanced/websockets/
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import json

class PresenceManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # public_key -> websocket
        self.presence: Dict[str, str] = {}  # public_key -> status (online/away/busy)

    async def connect(self, public_key: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[public_key] = websocket
        self.presence[public_key] = "online"
        await self.broadcast_presence(public_key, "online")

    def disconnect(self, public_key: str):
        if public_key in self.active_connections:
            del self.active_connections[public_key]
        self.presence[public_key] = "offline"
        # Note: Cannot await in non-async, handle in disconnect handler

    async def update_status(self, public_key: str, status: str):
        self.presence[public_key] = status
        await self.broadcast_presence(public_key, status)

    async def broadcast_presence(self, public_key: str, status: str):
        message = json.dumps({
            'type': 'presence_update',
            'public_key': public_key,
            'status': status
        })
        # Broadcast to all connected clients
        disconnected = []
        for pk, ws in self.active_connections.items():
            try:
                await ws.send_text(message)
            except:
                disconnected.append(pk)

        # Cleanup disconnected
        for pk in disconnected:
            self.disconnect(pk)

manager = PresenceManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Authenticate first (get public_key)
    public_key = await authenticate_websocket(websocket)

    await manager.connect(public_key, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg['type'] == 'status_update':
                await manager.update_status(public_key, msg['status'])

    except WebSocketDisconnect:
        manager.disconnect(public_key)
        await manager.broadcast_presence(public_key, "offline")
```

### Pattern 4: STUN Configuration for ICE Candidates (Phase 3 Prep)

**What:** Configure aiortc RTCPeerConnection with STUN servers for NAT traversal
**When to use:** Phase 3 P2P connection establishment via WebRTC
**Example:**

```python
# Source: https://aiortc.readthedocs.io/en/latest/api.html
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer

# Configure STUN servers (Google's free public STUN)
ice_servers = [
    RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
    RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
]

config = RTCConfiguration(iceServers=ice_servers)
pc = RTCPeerConnection(configuration=config)

# ICE candidates will be gathered automatically when creating offer/answer
# and sent via signaling channel to peer
```

### Pattern 5: Background Task for WebSocket Client in PyWebView

**What:** Run WebSocket client in background thread since PyWebView blocks main thread
**When to use:** Integrating asyncio WebSocket client with PyWebView desktop app
**Example:**

```python
# Source: https://pywebview.flowrl.com/guide/usage.html
import asyncio
import threading
import webview

class SignalingService:
    def __init__(self):
        self.loop = None
        self.task = None
        self.websocket = None

    def start(self):
        """Called by webview.start(func=...) - runs in separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Start WebSocket client as background task
        self.task = self.loop.create_task(self._run_client())

        # Keep strong reference to prevent GC
        self.task.add_done_callback(lambda t: None)

        # Run event loop forever
        self.loop.run_forever()

    async def _run_client(self):
        async for websocket in connect("wss://signaling.example.com/ws"):
            try:
                self.websocket = websocket
                await self.authenticate(websocket)

                async for message in websocket:
                    # Update UI via api.call() from main thread
                    self.notify_ui(message)

            except websockets.exceptions.ConnectionClosed:
                self.websocket = None
                continue

    def notify_ui(self, message):
        # Thread-safe UI update via PyWebView API
        # Will be implemented using existing api.call() pattern
        pass

# In main.py
signaling = SignalingService()
webview.start(signaling.start)  # Runs in background thread
```

### Anti-Patterns to Avoid

- **Blocking the asyncio event loop:** Never use `time.sleep()` in async functions - always use `asyncio.sleep()`
- **Manual reconnection logic:** Don't hand-roll exponential backoff - use websockets library's async iterator pattern
- **JWT for WebSocket auth:** Adds session management complexity - Ed25519 signatures are stateless and simpler
- **Plain ws:// in production:** Always use wss:// (WSS) for encrypted connections
- **Ignoring ping/pong failures:** Default 20s ping timeout is essential for detecting dead connections
- **Single connection for all messages:** WebSocket is for signaling only - actual P2P data goes over WebRTC (Phase 3)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket reconnection | Custom retry logic with timers | websockets async iterator | Built-in exponential backoff, handles transient vs fatal errors, battle-tested |
| Connection pooling | Custom WebSocket pool | Single websockets.connect() | WebSocket is persistent - only need one connection per server |
| Heartbeat/keepalive | Custom ping/pong messages | websockets ping_interval | Protocol-level ping/pong built-in, measures latency, detects connection loss |
| Presence state sync | Custom polling | Server-side broadcast on state change | Real-time updates via WebSocket, no polling overhead |
| Ed25519 signatures | Custom crypto | cryptography library | Constant-time operations prevent timing attacks, audited implementation |
| Message queuing | Custom buffer | asyncio.Queue | Thread-safe, backpressure handling, integrates with asyncio |

**Key insight:** WebSocket libraries handle 90% of edge cases (reconnection, keepalive, TLS, backpressure). Authentication and presence logic is where custom code should focus.

## Common Pitfalls

### Pitfall 1: Forgetting Strong References to Background Tasks

**What goes wrong:** asyncio.create_task() returns a Task that gets garbage collected if not referenced, causing background WebSocket client to stop unexpectedly

**Why it happens:** Python GC collects unreferenced objects, and background tasks don't have implicit references

**How to avoid:**
```python
# Create a set to hold strong references
background_tasks = set()

task = asyncio.create_task(websocket_client())
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)  # Auto-cleanup when done
```

**Warning signs:** WebSocket client stops running with no error messages, connection drops silently

### Pitfall 2: Blocking asyncio with PyWebView Main Thread

**What goes wrong:** PyWebView's webview.start() blocks the main thread, preventing asyncio event loop from running in the same thread

**Why it happens:** GUI frameworks require running on main thread, but asyncio also needs an event loop

**How to avoid:** Use webview.start(func=...) to run WebSocket client in a separate thread with its own event loop

**Warning signs:** WebSocket client never connects, asyncio tasks never execute, app hangs

### Pitfall 3: Using ws:// Instead of wss:// in Production

**What goes wrong:** Unencrypted WebSocket traffic is visible to network observers, violates E2E encryption promise

**Why it happens:** Development often uses ws://localhost, easy to forget to switch to wss:// for production

**How to avoid:**
- Always use wss:// URIs for remote servers
- Set up SSL context for production servers
- For development, use self-signed cert with custom SSL context

**Warning signs:** Authentication messages visible in network traffic, no TLS handshake in logs

### Pitfall 4: Not Handling WebSocket Disconnects in UI

**What goes wrong:** UI shows contacts as "online" after WebSocket disconnects, leading to stale presence data

**Why it happens:** No callback to notify UI layer when connection drops

**How to avoid:** Implement connection state callbacks to UI:
```python
# In signaling_client.py
async def on_disconnect():
    api.call('signaling_disconnected')  # Notify React UI

# In React
api.on('signaling_disconnected', () => {
    // Mark all contacts as "unknown" status
    // Show reconnecting indicator
})
```

**Warning signs:** Contacts stuck in "online" state after network loss, no reconnecting indicator

### Pitfall 5: Using Incorrect Ed25519 Key for Authentication

**What goes wrong:** Using X25519 (encryption) key instead of Ed25519 (signing) key for authentication, causing signature verification to fail

**Why it happens:** Phase 1 generates both Ed25519 and X25519 keys, easy to confuse them

**How to avoid:**
- Ed25519PrivateKey is for signing (authentication, identity)
- X25519PrivateKey is for encryption (P2P message encryption in Phase 3)
- Use load_identity_key() helper that explicitly returns Ed25519 key

**Warning signs:** All authentication attempts fail, "InvalidSignature" exceptions from server

### Pitfall 6: Not Setting Presence to Offline on Clean Shutdown

**What goes wrong:** App closes but server keeps user marked as "online" until ping timeout (20s)

**Why it happens:** No explicit offline message sent before disconnecting

**How to avoid:**
```python
async def shutdown_signaling():
    if websocket:
        await websocket.send(json.dumps({'type': 'status_update', 'status': 'offline'}))
        await websocket.close()
```

**Warning signs:** Users appear online for 20s after app closes, contacts see delayed "offline" status

### Pitfall 7: Synchronous Database Calls in Async WebSocket Handler

**What goes wrong:** Calling SQLite (synchronous) from async WebSocket message handler blocks the event loop

**Why it happens:** storage.contacts.add_contact() is synchronous but called from async context

**How to avoid:** Use asyncio.to_thread() to run sync DB operations in thread pool:
```python
async def handle_presence_update(public_key, status):
    # Run sync DB update in thread pool
    await asyncio.to_thread(
        storage.contacts.update_online_status,
        public_key, status
    )
```

**Warning signs:** WebSocket becomes unresponsive during DB operations, ping timeouts

## Code Examples

Verified patterns from official sources:

### Secure WebSocket Client Connection

```python
# Source: https://websockets.readthedocs.io/en/stable/howto/encryption.html
import ssl
from websockets.asyncio.client import connect

# Production: Use wss:// with valid CA certificate (automatic)
async with connect("wss://signaling.example.com/ws") as websocket:
    await websocket.send("Hello")

# Development: Use self-signed certificate
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_verify_locations("signaling-cert.pem")

async with connect("wss://localhost:8765/ws", ssl=ssl_context) as websocket:
    await websocket.send("Hello")
```

### Ed25519 Key Serialization for Storage

```python
# Source: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

# Generate and save Ed25519 key (done in Phase 1)
private_key = Ed25519PrivateKey.generate()
private_bytes = private_key.private_bytes_raw()  # 32 bytes

# Save to file (DPAPI encrypted)
save_to_secure_storage(private_bytes)

# Load from storage
loaded_private = Ed25519PrivateKey.from_private_bytes(private_bytes)

# Public key for sharing
public_bytes = private_key.public_key().public_bytes_raw()  # 32 bytes
loaded_public = Ed25519PublicKey.from_public_bytes(public_bytes)
```

### JSON Message Protocol for Signaling

```python
# Source: https://supabase.com/docs/guides/realtime/protocol (adapted)
import json
from enum import Enum

class MessageType(Enum):
    AUTH_CHALLENGE = "auth_challenge"
    AUTH_RESPONSE = "auth_response"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    STATUS_UPDATE = "status_update"
    PRESENCE_UPDATE = "presence_update"
    CONTACT_REQUEST = "contact_request"
    CONTACT_ACCEPT = "contact_accept"
    # Phase 3: offer, answer, ice_candidate

# Server sends challenge
def create_challenge(challenge_bytes: bytes) -> str:
    return json.dumps({
        'type': MessageType.AUTH_CHALLENGE.value,
        'challenge': base64.b64encode(challenge_bytes).decode()
    })

# Client sends response
def create_auth_response(public_key: bytes, signature: bytes) -> str:
    return json.dumps({
        'type': MessageType.AUTH_RESPONSE.value,
        'public_key': base64.b64encode(public_key).decode(),
        'signature': base64.b64encode(signature).decode()
    })

# Server broadcasts presence
def create_presence_update(public_key: str, status: str) -> str:
    return json.dumps({
        'type': MessageType.PRESENCE_UPDATE.value,
        'public_key': public_key,
        'status': status,  # online/away/busy/invisible/offline
        'timestamp': int(time.time())
    })
```

### Handling Multiple WebSocket Message Types

```python
# Source: FastAPI WebSocket best practices
async def handle_message(websocket, data: str):
    try:
        msg = json.loads(data)
        msg_type = msg.get('type')

        handlers = {
            'status_update': handle_status_update,
            'contact_request': handle_contact_request,
            'contact_accept': handle_contact_accept,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(websocket, msg)
        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Unknown message type: {msg_type}'
            }))

    except json.JSONDecodeError:
        await websocket.send(json.dumps({
            'type': 'error',
            'message': 'Invalid JSON'
        }))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual reconnection loops | websockets async iterator | websockets 11.0 (2023) | Built-in exponential backoff, cleaner code |
| Legacy asyncio API | New asyncio implementation | websockets 14.0 (2024) | Legacy deprecated, will be removed by 2030 |
| JWT/session tokens | Ed25519 challenge-response | Growing adoption 2024-2026 | Stateless auth, no token refresh, simpler server |
| HTTP long-polling for presence | WebSocket real-time push | Standard since WebSocket RFC 6455 (2011) | Real-time updates, lower latency |
| Custom keepalive messages | Protocol-level ping/pong | Built into WebSocket spec | Automatic latency measurement, standard |

**Deprecated/outdated:**
- **websockets legacy asyncio API**: Use `websockets.asyncio.client` instead of `websockets.client` (deprecated in 14.0)
- **HTTP polling for presence**: WebSocket push is standard for real-time status updates
- **Plain ws:// for production**: wss:// (WSS) is mandatory for secure communication

## Open Questions

Things that couldn't be fully resolved:

1. **PyWebView + asyncio integration pattern**
   - What we know: PyWebView requires main thread, webview.start() blocks execution
   - What's unclear: Best practice for running asyncio event loop alongside PyWebView in production
   - Recommendation: Use webview.start(func=...) to run WebSocket client in separate thread with its own event loop. This is standard pattern but needs testing with Phase 1 codebase.

2. **Signaling server deployment**
   - What we know: FastAPI + uvicorn is production-ready, requires separate deployment from desktop app
   - What's unclear: Whether to deploy on cloud service (AWS, DigitalOcean) or self-host
   - Recommendation: Start with cloud deployment (DigitalOcean $5/month droplet is sufficient for testing), document deployment in Phase 2 planning. Consider self-hosting for zero ongoing costs but requires static IP and uptime.

3. **STUN server reliability**
   - What we know: Google STUN servers are free and widely used, but no SLA for commercial use
   - What's unclear: Whether free Google STUN servers will remain available long-term
   - Recommendation: Use Google STUN for Phase 2/3 development and initial release. Monitor for deprecation announcements. Fallback options: self-host STUN server (coturn) or use Open Relay Project (claims 99.999% uptime).

4. **Contact discovery mechanism**
   - What we know: Users add contacts by public key (Phase 1), need to see if contact is online
   - What's unclear: Whether signaling server should maintain a global "public key -> online status" lookup or only notify mutual contacts
   - Recommendation: Privacy-first approach - server only relays presence to mutual contacts (users who have added each other). This requires contact list sync on connection. Document as requirement in planning.

## Sources

### Primary (HIGH confidence)

- [websockets 16.0 documentation - Client (asyncio)](https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html) - WebSocket client patterns, auto-reconnection, keepalive
- [websockets 16.0 documentation - Authentication](https://websockets.readthedocs.io/en/stable/topics/authentication.html) - Authentication patterns for WebSocket
- [websockets 16.0 documentation - Keepalive](https://websockets.readthedocs.io/en/stable/topics/keepalive.html) - Ping/pong intervals, timeout configuration
- [websockets 16.0 documentation - Encryption](https://websockets.readthedocs.io/en/stable/howto/encryption.html) - WSS setup, SSL context
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - ConnectionManager pattern, WebSocket routes
- [cryptography - Ed25519 signing](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) - Ed25519 API, sign/verify, serialization
- [Python asyncio - Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html) - create_task, background tasks, strong references
- [aiortc API Reference](https://aiortc.readthedocs.io/en/latest/api.html) - RTCPeerConnection, RTCConfiguration, RTCIceServer
- [PyWebView Usage](https://pywebview.flowrl.com/guide/usage.html) - Threading requirements, background tasks

### Secondary (MEDIUM confidence)

- [Supabase Realtime Protocol](https://supabase.com/docs/guides/realtime/protocol) - Presence state/diff message format (WebSearch verified)
- [VideoSDK - Ping Pong Frame WebSocket](https://www.videosdk.live/developer-hub/websocket/ping-pong-frame-websocket) - Heartbeat best practices (WebSearch verified)
- [Scaling WebSockets with PUB/SUB using Redis & FastAPI](https://medium.com/@nandagopal05/scaling-websockets-with-pub-sub-using-python-redis-fastapi-b16392ffe291) - Broadcast pattern for multi-server (WebSearch verified)
- [Google STUN server list](https://dev.to/alakkadshaw/google-stun-server-list-21n4) - Free public STUN servers (WebSearch verified)
- [Challenge-Response Protocol with Digital Signatures](https://www.radwin.org/michael/projects/jnfs/paper/node32.html) - Ed25519 auth pattern (WebSearch verified)

### Tertiary (LOW confidence)

- Various WebSearch results about WebSocket best practices, presence systems, and reconnection strategies - used for ecosystem discovery, all key findings verified with primary sources above

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - websockets, FastAPI, cryptography are official/well-maintained libraries with current documentation
- Architecture: HIGH - Patterns verified from official docs (websockets async iterator, FastAPI ConnectionManager, Ed25519 challenge-response)
- Pitfalls: MEDIUM - Based on common issues in GitHub issues and community discussions, verified with official docs where possible

**Research date:** 2026-01-30
**Valid until:** 2026-03-30 (60 days - stable ecosystem, libraries have long release cycles)
