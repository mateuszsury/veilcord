"""
Simple WebSocket signaling server for P2P connection establishment.

Run with: python -m src.server.signaling_server

Features:
- Ed25519 challenge-response authentication
- Presence broadcasting (online/offline/away/busy)
- P2P offer/answer relay for WebRTC connection
- Multiple client support

This is a development/testing server. For production, deploy a proper
signaling infrastructure with load balancing and persistence.
"""

import asyncio
import base64
import json
import logging
import os
import secrets
from dataclasses import dataclass, field
from typing import Dict, Optional

import websockets
from websockets.asyncio.server import ServerConnection

from src.network.auth import verify_challenge


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Client:
    """Connected client state."""
    websocket: ServerConnection
    public_key: str  # Base64-encoded Ed25519 public key
    authenticated: bool = False
    challenge: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    status: str = "online"


class SignalingServer:
    """
    WebSocket signaling server for DiscordOpus P2P connections.

    Protocol:
    1. Client connects
    2. Server sends auth_challenge with random bytes
    3. Client signs challenge and sends auth_response with public_key + signature
    4. Server verifies and sends auth_success or auth_failure
    5. Authenticated clients can:
       - Send presence updates (broadcast to all)
       - Send p2p_offer/p2p_answer to specific targets
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: Dict[ServerConnection, Client] = {}
        self._clients_by_key: Dict[str, Client] = {}  # public_key -> Client

    async def start(self):
        """Start the signaling server."""
        logger.info(f"Starting signaling server on ws://{self.host}:{self.port}")
        async with websockets.serve(
            self._handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=20
        ):
            logger.info("Signaling server running. Press Ctrl+C to stop.")
            await asyncio.Future()  # Run forever

    async def _handle_connection(self, websocket: ServerConnection):
        """Handle a new WebSocket connection."""
        client = Client(websocket=websocket, public_key="")
        self._clients[websocket] = client

        logger.info(f"New connection from {websocket.remote_address}")

        try:
            # Send auth challenge
            await self._send_auth_challenge(client)

            # Process messages
            async for message in websocket:
                await self._handle_message(client, message)

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Connection closed: {e.code} {e.reason}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            await self._cleanup_client(client)

    async def _send_auth_challenge(self, client: Client):
        """Send authentication challenge to client."""
        challenge_b64 = base64.b64encode(client.challenge).decode('ascii')
        await client.websocket.send(json.dumps({
            "type": "auth_challenge",
            "challenge": challenge_b64
        }))
        logger.debug(f"Sent auth challenge to {client.websocket.remote_address}")

    async def _handle_message(self, client: Client, data: str):
        """Route incoming message to appropriate handler."""
        try:
            message = json.loads(data)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received")
            return

        msg_type = message.get("type")

        if msg_type == "auth_response":
            await self._handle_auth_response(client, message)
        elif not client.authenticated:
            logger.warning("Unauthenticated client tried to send message")
            return
        elif msg_type == "presence":
            await self._handle_presence(client, message)
        elif msg_type == "p2p_offer":
            await self._relay_to_target(client, message)
        elif msg_type == "p2p_answer":
            await self._relay_to_target(client, message)
        else:
            logger.debug(f"Unknown message type: {msg_type}")

    async def _handle_auth_response(self, client: Client, message: dict):
        """Verify authentication response."""
        public_key_b64 = message.get("public_key")
        signature_b64 = message.get("signature")

        if not public_key_b64 or not signature_b64:
            await client.websocket.send(json.dumps({
                "type": "auth_failure",
                "reason": "Missing public_key or signature"
            }))
            return

        # Verify signature
        if verify_challenge(client.challenge, signature_b64, public_key_b64):
            client.authenticated = True
            client.public_key = public_key_b64
            self._clients_by_key[public_key_b64] = client

            await client.websocket.send(json.dumps({
                "type": "auth_success"
            }))

            logger.info(f"Client authenticated: {public_key_b64[:16]}...")

            # Broadcast presence to other clients
            await self._broadcast_presence(client)

            # Send current online users to new client
            await self._send_online_users(client)
        else:
            await client.websocket.send(json.dumps({
                "type": "auth_failure",
                "reason": "Invalid signature"
            }))
            logger.warning(f"Auth failed for {client.websocket.remote_address}")

    async def _handle_presence(self, client: Client, message: dict):
        """Handle presence update and broadcast to others."""
        status = message.get("status", "online")
        client.status = status

        logger.debug(f"Presence update: {client.public_key[:16]}... -> {status}")

        await self._broadcast_presence(client)

    async def _broadcast_presence(self, client: Client):
        """Broadcast client's presence to all other authenticated clients."""
        presence_msg = json.dumps({
            "type": "presence",
            "public_key": client.public_key,
            "status": client.status
        })

        for other in self._clients.values():
            if other.authenticated and other.public_key != client.public_key:
                try:
                    await other.websocket.send(presence_msg)
                except Exception:
                    pass

    async def _send_online_users(self, client: Client):
        """Send list of currently online users to a client."""
        for other in self._clients.values():
            if other.authenticated and other.public_key != client.public_key:
                await client.websocket.send(json.dumps({
                    "type": "presence",
                    "public_key": other.public_key,
                    "status": other.status
                }))

    async def _relay_to_target(self, client: Client, message: dict):
        """Relay P2P offer/answer to target client."""
        target_key = message.get("target")
        if not target_key:
            logger.warning("P2P message missing target")
            return

        target = self._clients_by_key.get(target_key)
        if not target:
            logger.debug(f"Target {target_key[:16]}... not online")
            # Notify sender that target is offline
            await client.websocket.send(json.dumps({
                "type": "error",
                "error": "target_offline",
                "target": target_key
            }))
            return

        # Add sender info and relay
        relay_msg = {**message, "from": client.public_key}
        await target.websocket.send(json.dumps(relay_msg))

        logger.debug(f"Relayed {message.get('type')} from {client.public_key[:16]}... to {target_key[:16]}...")

    async def _cleanup_client(self, client: Client):
        """Clean up disconnected client."""
        if client.websocket in self._clients:
            del self._clients[client.websocket]

        if client.public_key and client.public_key in self._clients_by_key:
            del self._clients_by_key[client.public_key]

            # Broadcast offline status
            if client.authenticated:
                client.status = "offline"
                await self._broadcast_presence(client)

        logger.info(f"Client disconnected: {client.public_key[:16] if client.public_key else 'unauthenticated'}...")


async def main():
    """Run the signaling server."""
    host = os.environ.get("SIGNALING_HOST", "0.0.0.0")
    port = int(os.environ.get("SIGNALING_PORT", "8765"))

    server = SignalingServer(host=host, port=port)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
