"""
WebSocket signaling client with auto-reconnection and Ed25519 authentication.

Connects to signaling server for:
- Presence (online/offline status)
- P2P connection establishment (ICE candidate exchange)
- Friend request delivery

Auto-reconnects with exponential backoff on disconnect.
"""

import asyncio
import base64
import json
import logging
from enum import Enum
from typing import Callable, Optional

import websockets
from websockets.asyncio.client import ClientConnection

from src.network.auth import create_auth_response
from src.storage.identity_store import load_identity


logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"


class SignalingClient:
    """
    WebSocket client for signaling server communication.

    Features:
    - Auto-reconnection with exponential backoff
    - Ed25519 challenge-response authentication
    - Thread-safe state management
    - Graceful shutdown

    Usage:
        client = SignalingClient(
            server_url="wss://signal.example.com",
            on_state_change=lambda state: print(f"State: {state}"),
            on_message=lambda msg: print(f"Message: {msg}")
        )
        await client.start()
        await client.send({"type": "presence", "status": "online"})
        await client.stop()
    """

    def __init__(
        self,
        server_url: str,
        on_state_change: Callable[[ConnectionState], None],
        on_message: Callable[[dict], None]
    ):
        """
        Initialize signaling client.

        Args:
            server_url: WebSocket server URL (wss://...)
            on_state_change: Callback for connection state changes
            on_message: Callback for incoming messages (except auth messages)
        """
        self.server_url = server_url
        self._on_state_change = on_state_change
        self._on_message = on_message

        self._state = ConnectionState.DISCONNECTED
        self._websocket: Optional[ClientConnection] = None
        self._connection_task: Optional[asyncio.Task] = None
        self._should_run = False
        self._state_lock = asyncio.Lock()

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    async def _set_state(self, state: ConnectionState) -> None:
        """Set state and notify callback (thread-safe)."""
        async with self._state_lock:
            if self._state != state:
                old_state = self._state
                self._state = state
                logger.info(f"Connection state: {old_state.value} -> {state.value}")
                try:
                    self._on_state_change(state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")

    async def start(self) -> None:
        """
        Start the connection loop.

        Connects to server and maintains connection with auto-reconnect.
        Call this from an async context (event loop must be running).
        """
        if self._should_run:
            logger.warning("SignalingClient already running")
            return

        self._should_run = True
        self._connection_task = asyncio.create_task(self._connect_loop())
        # Keep strong reference to prevent GC
        logger.info(f"Starting signaling client for {self.server_url}")

    async def stop(self) -> None:
        """
        Stop the connection gracefully.

        Sends offline status before disconnecting.
        """
        if not self._should_run:
            return

        logger.info("Stopping signaling client...")
        self._should_run = False

        # Send offline status if connected
        if self._websocket and self._state == ConnectionState.CONNECTED:
            try:
                await self.send({"type": "presence", "status": "offline"})
            except Exception as e:
                logger.debug(f"Could not send offline status: {e}")

        # Close websocket
        if self._websocket:
            await self._websocket.close()

        # Cancel connection task
        if self._connection_task:
            self._connection_task.cancel()
            try:
                await self._connection_task
            except asyncio.CancelledError:
                pass

        await self._set_state(ConnectionState.DISCONNECTED)
        logger.info("Signaling client stopped")

    async def send(self, message: dict) -> None:
        """
        Send a JSON message to the server.

        Args:
            message: Dictionary to send as JSON

        Raises:
            RuntimeError: If not connected
        """
        if self._state != ConnectionState.CONNECTED or not self._websocket:
            raise RuntimeError("Not connected to signaling server")

        data = json.dumps(message)
        await self._websocket.send(data)
        logger.debug(f"Sent: {message.get('type', 'unknown')}")

    async def _connect_loop(self) -> None:
        """
        Main connection loop with auto-reconnect.

        Uses websockets async iterator pattern which provides:
        - Automatic reconnection on disconnect
        - Exponential backoff between attempts
        """
        backoff = 1.0  # Initial backoff in seconds
        max_backoff = 60.0

        while self._should_run:
            try:
                await self._set_state(ConnectionState.CONNECTING)

                async with websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=20
                ) as websocket:
                    self._websocket = websocket
                    backoff = 1.0  # Reset backoff on successful connection

                    # Wait for auth challenge and authenticate
                    await self._set_state(ConnectionState.AUTHENTICATING)

                    # Process messages
                    async for message in websocket:
                        if not self._should_run:
                            break
                        await self._handle_message(message)

            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"Connection closed: {e.code} {e.reason}")
            except Exception as e:
                logger.error(f"Connection error: {e}")

            self._websocket = None

            # Reconnect with exponential backoff
            if self._should_run:
                await self._set_state(ConnectionState.DISCONNECTED)
                logger.info(f"Reconnecting in {backoff:.1f}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    async def _handle_message(self, data: str) -> None:
        """
        Handle incoming WebSocket message.

        Routes auth messages internally, passes others to callback.
        """
        try:
            message = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return

        msg_type = message.get("type")
        logger.debug(f"Received: {msg_type}")

        if msg_type == "auth_challenge":
            await self._authenticate(message)
        elif msg_type == "auth_success":
            await self._set_state(ConnectionState.CONNECTED)
            logger.info("Authentication successful")
        elif msg_type == "auth_failure":
            logger.error(f"Authentication failed: {message.get('reason', 'unknown')}")
            # Close connection to trigger reconnect
            if self._websocket:
                await self._websocket.close()
        else:
            # Pass to user callback
            try:
                self._on_message(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")

    async def _authenticate(self, challenge_msg: dict) -> None:
        """
        Handle authentication challenge from server.

        Args:
            challenge_msg: Message containing auth challenge
        """
        if not self._websocket:
            return

        # Get challenge bytes (base64 encoded from server)
        challenge_b64 = challenge_msg.get("challenge")
        if not challenge_b64:
            logger.error("No challenge in auth_challenge message")
            return

        try:
            challenge = base64.b64decode(challenge_b64)
        except Exception as e:
            logger.error(f"Invalid challenge encoding: {e}")
            return

        # Load identity for signing
        identity = load_identity()
        if identity is None:
            logger.error("No identity found - cannot authenticate")
            return

        # Create and send auth response
        try:
            response = create_auth_response(challenge, identity.ed25519_private_key)
            await self._websocket.send(json.dumps(response))
            logger.debug("Sent auth response")
        except Exception as e:
            logger.error(f"Failed to send auth response: {e}")
