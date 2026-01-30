"""
Network service orchestrator for signaling, presence, and P2P messaging.

Manages the lifecycle of network components:
- SignalingClient for WebSocket connection
- PresenceManager for status tracking
- MessagingService for P2P encrypted messaging
- Frontend notification via window.evaluate_js()

Runs in a background thread started by webview.start(func=...).
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any, List

import webview

from src.network.signaling_client import SignalingClient, ConnectionState
from src.network.presence import PresenceManager, UserStatus
from src.network.messaging import MessagingService
from src.network.peer_connection import P2PConnectionState
from src.storage.settings import get_setting, set_setting, Settings
from src.file_transfer.service import FileTransferService
from src.file_transfer.protocol import EOF_MARKER, CANCEL_MARKER, ACK_MARKER, ERROR_MARKER
from src.file_transfer.models import TransferProgress
from src.storage.files import FileMetadata


logger = logging.getLogger(__name__)


class NetworkService:
    """
    Orchestrates signaling client, presence management, and P2P messaging.

    Runs in a background thread with its own asyncio event loop.
    Communicates with frontend via window.evaluate_js() for:
    - Connection state changes
    - Contact presence updates
    - P2P connection state changes
    - Incoming messages

    Usage:
        service = NetworkService(window)
        service.start()  # Blocks in background thread
        ...
        service.stop()   # Call from main thread to shutdown
    """

    def __init__(self, window: webview.Window) -> None:
        """
        Initialize network service.

        Args:
            window: PyWebView window for JS callbacks
        """
        self._window = window
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._signaling: Optional[SignalingClient] = None
        self._presence: Optional[PresenceManager] = None
        self._messaging: Optional[MessagingService] = None
        self._file_transfer: Optional[FileTransferService] = None
        self._state = ConnectionState.DISCONNECTED
        self._running = False
        self._startup_task: Optional[asyncio.Task] = None
        self._pending_events: list[tuple[str, dict]] = []  # Events before window ready
        self._window_ready = False

    def start(self) -> None:
        """
        Start the network service.

        Called by webview.start(func=...) in a background thread.
        Creates asyncio event loop and runs forever.
        """
        if self._running:
            logger.warning("NetworkService already running")
            return

        self._running = True
        logger.info("Starting NetworkService in background thread")

        # Create new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Create presence manager with callback
        self._presence = PresenceManager(
            on_status_change=lambda pk, status: self._schedule_presence_notify(pk, status)
        )

        # Get signaling server URL
        server_url = get_setting(Settings.SIGNALING_SERVER_URL)
        if not server_url:
            server_url = Settings.get_default(Settings.SIGNALING_SERVER_URL)

        # Create signaling client
        self._signaling = SignalingClient(
            server_url=server_url,
            on_state_change=lambda state: self._schedule_state_notify(state),
            on_message=lambda msg: self._schedule_message_handle(msg)
        )

        # Schedule startup
        self._startup_task = self._loop.create_task(self._async_start())

        # Run event loop forever
        try:
            self._loop.run_forever()
        finally:
            # Cleanup
            if self._loop.is_running():
                self._loop.stop()
            self._loop.close()
            logger.info("NetworkService stopped")

    async def _async_start(self) -> None:
        """Async startup sequence."""
        try:
            # Wait a moment for window to be ready
            await asyncio.sleep(0.5)
            self._window_ready = True

            # Replay any pending events
            for event_type, detail in self._pending_events:
                self._notify_frontend(event_type, detail)
            self._pending_events.clear()

            # Create messaging service with callbacks
            self._messaging = MessagingService()
            self._messaging.on_message = self._on_incoming_message
            self._messaging.on_connection_state = self._on_p2p_state_change
            self._messaging.send_signaling = lambda msg: asyncio.create_task(
                self._async_send(msg)
            )

            # Create file transfer service with callbacks
            self._file_transfer = FileTransferService()
            self._file_transfer.on_transfer_progress = self._on_file_progress
            self._file_transfer.on_file_received = self._on_file_received
            self._file_transfer.on_transfer_complete = self._on_transfer_complete
            self._file_transfer.on_transfer_error = self._on_transfer_error

            # Start signaling client
            await self._signaling.start()
        except Exception as e:
            logger.error(f"Error during async startup: {e}")

    def stop(self) -> None:
        """
        Stop the network service gracefully.

        Sends offline status before disconnecting.
        Safe to call from any thread.
        """
        if not self._running:
            return

        self._running = False
        logger.info("Stopping NetworkService...")

        if self._loop and self._loop.is_running():
            # Schedule async shutdown
            future = asyncio.run_coroutine_threadsafe(
                self._async_stop(),
                self._loop
            )
            try:
                # Wait for shutdown with timeout
                future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")

            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)

    async def _async_stop(self) -> None:
        """Async shutdown sequence."""
        if self._messaging:
            await self._messaging.close_all()
        if self._signaling:
            await self._signaling.stop()

    def _schedule_state_notify(self, state: ConnectionState) -> None:
        """Schedule state change notification (thread-safe)."""
        self._state = state
        if self._loop:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._on_state_change(state))
            )

    def _schedule_presence_notify(self, public_key: str, status: str) -> None:
        """Schedule presence change notification (thread-safe)."""
        if self._loop:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._on_presence_change(public_key, status))
            )

    def _schedule_message_handle(self, message: dict) -> None:
        """Schedule message handling (thread-safe)."""
        if self._loop:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self._on_message(message))
            )

    async def _on_state_change(self, state: ConnectionState) -> None:
        """Handle connection state change."""
        logger.debug(f"Connection state changed: {state.value}")
        self._notify_frontend('discordopus:connection', {'state': state.value})

        # Send initial status when connected
        if state == ConnectionState.CONNECTED and self._signaling and self._presence:
            try:
                status_msg = self._presence.build_status_message()
                await self._signaling.send(status_msg)
                logger.info(f"Sent initial status: {status_msg['status']}")
            except Exception as e:
                logger.error(f"Failed to send initial status: {e}")

    async def _on_message(self, message: dict) -> None:
        """Handle incoming message from signaling server."""
        msg_type = message.get('type')
        logger.debug(f"Handling message: {msg_type}")

        if msg_type == 'presence_update':
            # Update contact presence
            public_key = message.get('public_key')
            status = message.get('status')
            if public_key and status and self._presence:
                self._presence.update_contact_presence(public_key, status)

        elif msg_type == 'p2p_offer':
            # Incoming P2P connection offer
            from_key = message.get('from')
            sdp = message.get('sdp')
            if from_key and sdp and self._messaging:
                await self._messaging.handle_offer(from_key, sdp)

        elif msg_type == 'p2p_answer':
            # Incoming P2P connection answer
            from_key = message.get('from')
            sdp = message.get('sdp')
            if from_key and sdp and self._messaging:
                await self._messaging.handle_answer(from_key, sdp)

        else:
            logger.debug(f"Unhandled message type: {msg_type}")

    async def _on_presence_change(self, public_key: str, status: str) -> None:
        """Handle contact presence change."""
        logger.debug(f"Presence change: {public_key[:16]}... -> {status}")
        self._notify_frontend('discordopus:presence', {
            'publicKey': public_key,
            'status': status
        })

    def _on_incoming_message(self, contact_id: int, message: Any) -> None:
        """
        Handle incoming message from MessagingService.

        Routes messages based on type:
        - Binary messages starting with 'C' -> file chunks
        - JSON messages with type starting with 'file_' -> file metadata/control
        - Special markers (EOF, CANCEL, etc.) -> file control
        - Everything else -> regular messages for frontend
        """
        # Check if it's a binary message (bytes)
        if isinstance(message, bytes):
            # Check for file control markers
            if message in (EOF_MARKER, CANCEL_MARKER, ACK_MARKER, ERROR_MARKER):
                if self._file_transfer and self._loop:
                    # Get peer connection from messaging service
                    peer = self._messaging._connections.get(contact_id)
                    if peer:
                        asyncio.run_coroutine_threadsafe(
                            self._file_transfer.handle_incoming_message(contact_id, peer, message),
                            self._loop
                        )
                return

            # Check for chunk data (starts with 'C' byte)
            if message.startswith(b'C'):
                if self._file_transfer and self._loop:
                    peer = self._messaging._connections.get(contact_id)
                    if peer:
                        asyncio.run_coroutine_threadsafe(
                            self._file_transfer.handle_incoming_message(contact_id, peer, message),
                            self._loop
                        )
                return

            # Check if it's JSON file message
            if message.startswith(b'{'):
                try:
                    import json
                    msg_str = message.decode('utf-8')
                    data = json.loads(msg_str)
                    if data.get('type', '').startswith('file_'):
                        if self._file_transfer and self._loop:
                            peer = self._messaging._connections.get(contact_id)
                            if peer:
                                asyncio.run_coroutine_threadsafe(
                                    self._file_transfer.handle_incoming_message(contact_id, peer, message),
                                    self._loop
                                )
                        return
                except (UnicodeDecodeError, json.JSONDecodeError):
                    pass

        # Regular message - should be a dict
        if isinstance(message, dict):
            logger.debug(f"Incoming message for contact {contact_id}: {message.get('type', 'text')}")
            self._notify_frontend('discordopus:message', {
                'contactId': contact_id,
                'message': message
            })

    def _on_p2p_state_change(self, contact_id: int, state: P2PConnectionState) -> None:
        """Handle P2P connection state change."""
        logger.debug(f"P2P state for contact {contact_id}: {state.value}")
        self._notify_frontend('discordopus:p2p_state', {
            'contactId': contact_id,
            'state': state.value
        })

    def _notify_frontend(self, event_type: str, detail: dict) -> None:
        """
        Notify frontend via window.evaluate_js().

        Queues events if window not ready yet.
        """
        if not self._window_ready:
            self._pending_events.append((event_type, detail))
            return

        try:
            # Build JavaScript to dispatch custom event
            detail_json = str(detail).replace("'", '"')  # Python dict to JSON
            js_code = f'''
                window.dispatchEvent(new CustomEvent('{event_type}', {{
                    detail: {detail_json}
                }}));
            '''
            self._window.evaluate_js(js_code)
        except Exception as e:
            logger.debug(f"Could not notify frontend: {e}")

    # ========== Sync methods for API bridge ==========

    def get_connection_state(self) -> str:
        """Get current connection state as string."""
        return self._state.value

    def get_signaling_server(self) -> str:
        """Get configured signaling server URL."""
        url = get_setting(Settings.SIGNALING_SERVER_URL)
        return url if url else Settings.get_default(Settings.SIGNALING_SERVER_URL)

    def set_signaling_server(self, url: str) -> None:
        """
        Set signaling server URL and reconnect.

        Args:
            url: New WebSocket URL
        """
        set_setting(Settings.SIGNALING_SERVER_URL, url)

        # Reconnect with new URL
        if self._loop and self._signaling:
            asyncio.run_coroutine_threadsafe(
                self._reconnect(url),
                self._loop
            )

    async def _reconnect(self, url: str) -> None:
        """Reconnect signaling client with new URL."""
        if self._signaling:
            await self._signaling.stop()

        self._signaling = SignalingClient(
            server_url=url,
            on_state_change=lambda state: self._schedule_state_notify(state),
            on_message=lambda msg: self._schedule_message_handle(msg)
        )
        await self._signaling.start()

    def get_user_status(self) -> str:
        """Get user's presence status."""
        if self._presence:
            return self._presence.get_user_status().value
        return UserStatus.ONLINE.value

    def set_user_status(self, status: str) -> None:
        """
        Set user's presence status and notify server.

        Args:
            status: Status string (online, away, busy, invisible)
        """
        if not self._presence:
            return

        try:
            user_status = UserStatus(status)
            self._presence.set_user_status(user_status)

            # Send update to server
            if self._loop and self._signaling and self._state == ConnectionState.CONNECTED:
                asyncio.run_coroutine_threadsafe(
                    self._send_status_update(),
                    self._loop
                )
        except ValueError:
            logger.error(f"Invalid status: {status}")

    async def _send_status_update(self) -> None:
        """Send status update to signaling server."""
        if self._signaling and self._presence:
            try:
                status_msg = self._presence.build_status_message()
                await self._signaling.send(status_msg)
            except Exception as e:
                logger.error(f"Failed to send status update: {e}")

    def send_message(self, message: dict) -> None:
        """
        Queue a message to send via signaling.

        Args:
            message: Message dict to send
        """
        if self._loop and self._signaling:
            asyncio.run_coroutine_threadsafe(
                self._async_send(message),
                self._loop
            )

    async def _async_send(self, message: dict) -> None:
        """Send message to signaling server."""
        if self._signaling and self._state == ConnectionState.CONNECTED:
            try:
                await self._signaling.send(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    # ========== P2P Messaging Methods ==========

    def initiate_p2p_connection(self, contact_id: int) -> None:
        """
        Initiate P2P connection to a contact.

        Args:
            contact_id: Contact database ID
        """
        if self._loop and self._messaging:
            asyncio.run_coroutine_threadsafe(
                self._messaging.initiate_connection(contact_id),
                self._loop
            )

    def send_text_message(
        self,
        contact_id: int,
        body: str,
        reply_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send encrypted text message to a contact.

        Args:
            contact_id: Contact database ID
            body: Message text
            reply_to: Optional message ID being replied to

        Returns:
            Message dict or None if failed
        """
        if not self._loop or not self._messaging:
            return None

        future = asyncio.run_coroutine_threadsafe(
            self._messaging.send_text_message(contact_id, body, reply_to),
            self._loop
        )
        try:
            return future.result(timeout=10.0)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None

    def get_p2p_connection_state(self, contact_id: int) -> str:
        """
        Get P2P connection state for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            P2P state as string
        """
        if self._messaging:
            return self._messaging.get_connection_state(contact_id).value
        return P2PConnectionState.DISCONNECTED.value

    def send_typing_indicator(self, contact_id: int, active: bool = True) -> None:
        """
        Send typing indicator to a contact.

        Args:
            contact_id: Contact database ID
            active: True if typing, False if stopped
        """
        if self._messaging:
            self._messaging.send_typing(contact_id, active)

    # ========== File Transfer Methods ==========

    def send_file(self, contact_id: int, file_path: str) -> Optional[str]:
        """
        Send a file to a contact.

        Args:
            contact_id: Contact database ID
            file_path: Absolute path to file

        Returns:
            Transfer ID or None if failed
        """
        if not self._loop or not self._file_transfer or not self._messaging:
            return None

        from pathlib import Path
        peer = self._messaging._connections.get(contact_id)
        if not peer:
            logger.error(f"No P2P connection to contact {contact_id}")
            return None

        future = asyncio.run_coroutine_threadsafe(
            self._file_transfer.send_file(contact_id, peer, Path(file_path)),
            self._loop
        )
        try:
            return future.result(timeout=10.0)
        except Exception as e:
            logger.error(f"Failed to start file send: {e}")
            return None

    def resume_file(self, contact_id: int, transfer_id: str, file_path: str) -> Optional[str]:
        """
        Resume an interrupted file transfer.

        Requires original file to still be at same path (or user re-selects).

        Args:
            contact_id: Contact database ID
            transfer_id: Transfer UUID from database
            file_path: Path to the file (must match original)

        Returns:
            New transfer ID or None if failed
        """
        if not self._loop or not self._file_transfer or not self._messaging:
            return None

        from pathlib import Path
        from src.storage.db import get_transfer_state

        # Get stored transfer state
        state = get_transfer_state(transfer_id)
        if not state:
            logger.error(f"Transfer {transfer_id} not found in database")
            return None

        # Can only resume SEND direction transfers
        if state['direction'] != 'send':
            logger.error(f"Cannot resume receive transfer {transfer_id}")
            return None

        # Verify file exists and matches original size
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        if path.stat().st_size != state['size']:
            logger.error(f"File size mismatch - cannot resume (original: {state['size']}, current: {path.stat().st_size})")
            return None

        # Check for P2P connection
        peer = self._messaging._connections.get(contact_id)
        if not peer:
            logger.error(f"No P2P connection to contact {contact_id}")
            return None

        # Get resume offset from stored state
        resume_offset = state['bytes_transferred']

        # Start transfer with resume offset
        future = asyncio.run_coroutine_threadsafe(
            self._file_transfer.send_file(contact_id, peer, path, resume_offset=resume_offset),
            self._loop
        )
        try:
            return future.result(timeout=10.0)
        except Exception as e:
            logger.error(f"Failed to resume file send: {e}")
            return None

    def cancel_transfer(self, contact_id: int, transfer_id: str, direction: str = "send") -> bool:
        """
        Cancel a file transfer.

        Args:
            contact_id: Contact database ID
            transfer_id: Transfer UUID
            direction: "send" or "receive"

        Returns:
            True if cancelled, False if not found
        """
        if not self._loop or not self._file_transfer:
            return False

        if direction == "send":
            future = asyncio.run_coroutine_threadsafe(
                self._file_transfer.cancel_send(contact_id, transfer_id),
                self._loop
            )
        else:
            future = asyncio.run_coroutine_threadsafe(
                self._file_transfer.cancel_receive(contact_id, transfer_id),
                self._loop
            )

        try:
            return future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to cancel transfer: {e}")
            return False

    def get_active_transfers(self, contact_id: int) -> List[Dict[str, Any]]:
        """
        Get active transfers for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            List of transfer progress dicts
        """
        if not self._file_transfer:
            return []

        transfers = self._file_transfer.get_active_transfers(contact_id)
        return [self._transfer_progress_to_dict(t) for t in transfers]

    def get_resumable_transfers(self, contact_id: int) -> List[Dict[str, Any]]:
        """
        Get resumable transfers for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            List of transfer state dicts from database
        """
        if not self._file_transfer:
            return []

        return self._file_transfer.get_resumable_transfers(contact_id)

    def _transfer_progress_to_dict(self, progress: TransferProgress) -> Dict[str, Any]:
        """Convert TransferProgress to JSON-serializable dict."""
        return {
            'transferId': progress.transfer_id,
            'bytesTransferred': progress.bytes_transferred,
            'totalBytes': progress.total_bytes,
            'state': progress.state.value,
            'speedBps': progress.speed_bps,
            'etaSeconds': progress.eta_seconds
        }

    def _on_file_progress(self, contact_id: int, progress: TransferProgress) -> None:
        """Handle file transfer progress update."""
        logger.debug(
            f"File transfer progress: {progress.transfer_id} - "
            f"{progress.bytes_transferred}/{progress.total_bytes} bytes"
        )
        self._notify_frontend('discordopus:file_progress', {
            'contactId': contact_id,
            'progress': self._transfer_progress_to_dict(progress)
        })

    def _on_file_received(self, contact_id: int, file_meta: FileMetadata) -> None:
        """Handle file reception completion."""
        logger.info(f"File received: {file_meta.filename} from contact {contact_id}")

        # Get contact public key for sender_id
        from src.storage.contacts import get_contact
        contact = get_contact(contact_id)
        if not contact:
            logger.error(f"Contact {contact_id} not found for file message")
            return

        # Create file message in database
        from src.storage.messages import save_file_message
        try:
            message = save_file_message(
                conversation_id=contact_id,
                sender_id=contact.ed25519_public_pem,
                file_id=file_meta.id,
                filename=file_meta.filename
            )
            logger.debug(f"Created file message {message.id} for file {file_meta.id}")
        except Exception as e:
            logger.error(f"Failed to create file message: {e}")

        # Notify frontend with file data
        self._notify_frontend('discordopus:file_received', {
            'contactId': contact_id,
            'file': {
                'id': file_meta.id,
                'filename': file_meta.filename,
                'size': file_meta.size,
                'mimeType': file_meta.mime_type,
                'transferId': file_meta.transfer_id
            }
        })

        # Also send message event so it appears in chat
        self._notify_frontend('discordopus:message', {
            'contactId': contact_id,
            'message': {
                'id': message.id,
                'conversationId': message.conversation_id,
                'senderId': message.sender_id,
                'type': message.type,
                'body': message.body,
                'replyTo': message.reply_to,
                'edited': message.edited,
                'deleted': message.deleted,
                'timestamp': message.timestamp,
                'receivedAt': message.received_at,
                'fileId': message.file_id
            }
        })

    def _on_transfer_complete(self, contact_id: int, transfer_id: str) -> None:
        """Handle file transfer completion."""
        logger.info(f"File transfer complete: {transfer_id}")
        self._notify_frontend('discordopus:transfer_complete', {
            'contactId': contact_id,
            'transferId': transfer_id
        })

    def _on_transfer_error(self, contact_id: int, transfer_id: str, error: str) -> None:
        """Handle file transfer error."""
        logger.error(f"File transfer error: {transfer_id} - {error}")
        self._notify_frontend('discordopus:transfer_error', {
            'contactId': contact_id,
            'transferId': transfer_id,
            'error': error
        })


# ========== Module-level singleton ==========

_service: Optional[NetworkService] = None
_service_lock = threading.Lock()


def start_network(window: webview.Window) -> None:
    """
    Start the network service singleton.

    Called by webview.start(func=...) in background thread.

    Args:
        window: PyWebView window for JS callbacks
    """
    global _service
    with _service_lock:
        if _service is not None:
            logger.warning("Network service already started")
            return
        _service = NetworkService(window)

    # This blocks in the background thread
    _service.start()


def stop_network() -> None:
    """
    Stop the network service.

    Safe to call from any thread.
    """
    global _service
    with _service_lock:
        if _service is not None:
            _service.stop()
            _service = None


def get_network_service() -> NetworkService:
    """
    Get the network service singleton.

    Returns:
        NetworkService instance

    Raises:
        RuntimeError: If service not started
    """
    if _service is None:
        raise RuntimeError("Network service not started")
    return _service
