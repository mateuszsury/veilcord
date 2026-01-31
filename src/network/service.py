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
from src.voice.call_service import VoiceCallService
from src.voice.models import CallState, CallEvent, CallEndReason
from src.voice import get_available_cameras, get_available_monitors


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
        self._voice_call: Optional[VoiceCallService] = None
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

            # Create voice call service with callbacks
            self._voice_call = VoiceCallService()
            self._voice_call.on_state_change = self._on_call_state_change
            self._voice_call.on_remote_video = self._on_remote_video
            self._voice_call.send_signaling = lambda msg: asyncio.create_task(
                self._async_send(msg)
            )

            # Set local public key for voice call service
            from src.storage.identity_store import load_identity
            identity = load_identity()
            if identity and self._voice_call:
                self._voice_call.set_local_public_key(identity.shareable_id)

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
        # End any active voice call
        if self._voice_call and self._voice_call._current_call:
            await self._voice_call.end_call()
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

        elif msg_type == 'call_offer':
            # Incoming voice call offer
            from_key = message.get('from')
            call_id = message.get('call_id')
            sdp = message.get('sdp')
            if self._voice_call and from_key and call_id and sdp:
                event = CallEvent(
                    type='call_offer',
                    call_id=call_id,
                    from_key=from_key,
                    to_key=message.get('to', ''),
                    sdp=sdp
                )
                await self._voice_call.handle_call_offer(event)
                # Notify frontend of incoming call
                self._notify_frontend('discordopus:incoming_call', {
                    'callId': call_id,
                    'fromKey': from_key
                })

        elif msg_type == 'call_answer':
            # Answer to our outgoing call
            call_id = message.get('call_id')
            sdp = message.get('sdp')
            from_key = message.get('from')
            if self._voice_call and call_id and sdp:
                event = CallEvent(
                    type='call_answer',
                    call_id=call_id,
                    from_key=from_key or '',
                    to_key=message.get('to', ''),
                    sdp=sdp
                )
                await self._voice_call.handle_call_answer(event)
                # Notify frontend call was answered
                self._notify_frontend('discordopus:call_answered', {
                    'callId': call_id
                })

        elif msg_type == 'call_reject':
            # Our call was rejected
            call_id = message.get('call_id')
            reason = message.get('reason', 'rejected')
            from_key = message.get('from')
            if self._voice_call and call_id:
                event = CallEvent(
                    type='call_reject',
                    call_id=call_id,
                    from_key=from_key or '',
                    to_key=message.get('to', ''),
                    reason=CallEndReason.REJECTED
                )
                await self._voice_call.handle_call_reject(event)
                # Notify frontend call was rejected
                self._notify_frontend('discordopus:call_rejected', {
                    'callId': call_id,
                    'reason': reason
                })

        elif msg_type == 'call_end':
            # Call ended by remote party
            call_id = message.get('call_id')
            reason = message.get('reason', 'completed')
            if self._voice_call:
                # Map string reason to CallEndReason enum
                end_reason = CallEndReason.COMPLETED
                if reason == 'busy':
                    end_reason = CallEndReason.CANCELLED
                elif reason == 'timeout':
                    end_reason = CallEndReason.NO_ANSWER
                elif reason == 'error':
                    end_reason = CallEndReason.FAILED
                elif reason == 'rejected':
                    end_reason = CallEndReason.REJECTED

                await self._voice_call.end_call(end_reason)
                # Notify frontend call ended
                self._notify_frontend('discordopus:call_ended', {
                    'callId': call_id,
                    'reason': reason
                })

        elif msg_type == 'call_ice_candidate':
            # ICE candidate from remote party (for trickle ICE support in future)
            call_id = message.get('call_id')
            candidate = message.get('candidate')
            sdp_mid = message.get('sdpMid')
            sdp_mline_index = message.get('sdpMLineIndex')
            if self._voice_call and call_id and candidate:
                # Note: Currently using full ICE gathering before signaling
                # This handler is for future trickle ICE support
                logger.debug(f"Received ICE candidate for call {call_id}")

        elif msg_type == 'call_mute':
            # Remote mute status change
            call_id = message.get('call_id')
            muted = message.get('muted', False)
            if self._voice_call:
                event = CallEvent(
                    type='call_mute',
                    call_id=call_id or '',
                    from_key=message.get('from', ''),
                    to_key=message.get('to', ''),
                    muted=muted
                )
                await self._voice_call.handle_call_mute(event)
                # Notify frontend of remote mute status
                self._notify_frontend('discordopus:remote_mute', {
                    'callId': call_id,
                    'muted': muted
                })

        elif msg_type == 'call_video_renegotiate':
            # Video renegotiation from remote party
            call_id = message.get('call_id')
            sdp = message.get('sdp')
            sdp_type = message.get('sdp_type', 'offer')  # 'offer' or 'answer'
            video_enabled = message.get('video_enabled', False)
            video_source = message.get('video_source')
            from_key = message.get('from')

            if self._voice_call and call_id and sdp:
                event = CallEvent(
                    type='call_video_renegotiate',
                    call_id=call_id,
                    from_key=from_key or '',
                    to_key=message.get('to', ''),
                    sdp=sdp,
                    video_enabled=video_enabled,
                    video_source=video_source
                )

                if sdp_type == 'offer':
                    # Remote is adding/changing video - handle offer
                    await self._voice_call.handle_video_renegotiate_offer(event)
                else:
                    # Response to our video change - handle answer
                    await self._voice_call.handle_video_renegotiate_answer(event)

                # Notify frontend of video state change
                self._notify_frontend('discordopus:video_state', {
                    'videoEnabled': self._voice_call.current_call.video_enabled if self._voice_call.current_call else False,
                    'videoSource': self._voice_call.current_call.video_source if self._voice_call.current_call else None,
                    'remoteVideo': self._voice_call.current_call.remote_video if self._voice_call.current_call else False
                })

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

    def _on_call_state_change(self, contact_id: int, state: CallState) -> None:
        """Handle voice call state change."""
        logger.debug(f"Call state for contact {contact_id}: {state.value}")
        self._notify_frontend('discordopus:call_state', {
            'contactId': contact_id,
            'state': state.value
        })

    def _on_remote_video(self, has_video: bool, track=None) -> None:
        """
        Handle remote video state change.

        Called by VoiceCallService when remote party enables/disables video.

        Args:
            has_video: Whether remote now has video enabled
            track: The video track (for frame access), or None if disabled
        """
        logger.debug(f"Remote video changed: has_video={has_video}")
        # Store track reference for potential frame access
        if self._voice_call and self._voice_call.current_call:
            self._voice_call.current_call.remote_video = has_video

        self._notify_frontend('discordopus:remote_video_changed', {
            'hasVideo': has_video
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

    # ========== Voice Call Methods ==========

    def start_voice_call(self, contact_id: int) -> Optional[str]:
        """
        Start voice call with contact.

        Args:
            contact_id: Contact database ID

        Returns:
            Call ID on success, None if failed
        """
        if not self._loop or not self._voice_call:
            return None

        # Get contact public key
        from src.storage.contacts import get_contact
        contact = get_contact(contact_id)
        if not contact:
            return None

        future = asyncio.run_coroutine_threadsafe(
            self._voice_call.start_call(contact_id, contact.ed25519_public_pem),
            self._loop
        )
        try:
            return future.result(timeout=35.0)  # Allow time for ICE gathering
        except Exception as e:
            logger.error(f"Failed to start call: {e}")
            return None

    def accept_voice_call(self) -> bool:
        """
        Accept incoming voice call.

        Returns:
            True on success, False if no incoming call
        """
        if not self._loop or not self._voice_call:
            return False
        future = asyncio.run_coroutine_threadsafe(
            self._voice_call.accept_call(),
            self._loop
        )
        try:
            return future.result(timeout=35.0)
        except Exception as e:
            logger.error(f"Failed to accept call: {e}")
            return False

    def reject_voice_call(self) -> bool:
        """
        Reject incoming voice call.

        Returns:
            True on success, False if no incoming call
        """
        if not self._loop or not self._voice_call:
            return False
        future = asyncio.run_coroutine_threadsafe(
            self._voice_call.reject_call(),
            self._loop
        )
        try:
            return future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to reject call: {e}")
            return False

    def end_voice_call(self) -> bool:
        """
        End current voice call.

        Returns:
            True on success, False if no call to end
        """
        if not self._loop or not self._voice_call:
            return False
        future = asyncio.run_coroutine_threadsafe(
            self._voice_call.end_call(CallEndReason.COMPLETED),
            self._loop
        )
        try:
            return future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to end call: {e}")
            return False

    def set_call_muted(self, muted: bool) -> None:
        """
        Mute/unmute call microphone.

        Args:
            muted: True to mute, False to unmute
        """
        if self._voice_call:
            self._voice_call.set_muted(muted)

    def is_call_muted(self) -> bool:
        """
        Check if call is muted.

        Returns:
            True if muted, False otherwise
        """
        if self._voice_call:
            return self._voice_call.is_muted()
        return False

    def get_call_state(self) -> Optional[Dict[str, Any]]:
        """
        Get current call state.

        Returns:
            Call state dict or None if no call
        """
        if not self._voice_call or not self._voice_call._current_call:
            return None
        call = self._voice_call._current_call
        return {
            'callId': call.call_id,
            'contactId': call.contact_id,
            'state': call.state.value,
            'direction': call.direction,
            'muted': call.muted,
            'duration': self._voice_call.get_call_duration()
        }

    # ========== Video Call Methods ==========

    def enable_video(self, source: str = "camera") -> bool:
        """
        Enable video (camera or screen) during active call.

        Args:
            source: "camera" or "screen"

        Returns:
            True on success, False on failure
        """
        if not self._voice_call:
            return False
        if not self._loop:
            return False

        try:
            result = asyncio.run_coroutine_threadsafe(
                self._voice_call.enable_video(source),
                self._loop
            ).result(timeout=10.0)

            # Notify frontend of video state change
            if result and self._voice_call.current_call:
                self._notify_frontend('discordopus:video_state', {
                    'videoEnabled': self._voice_call.current_call.video_enabled,
                    'videoSource': self._voice_call.current_call.video_source,
                    'remoteVideo': self._voice_call.current_call.remote_video
                })

            return result
        except Exception as e:
            logger.error(f"Failed to enable video: {e}")
            return False

    def disable_video(self) -> bool:
        """
        Disable video during call.

        Returns:
            True on success, False on failure
        """
        if not self._voice_call:
            return False
        if not self._loop:
            return False

        try:
            result = asyncio.run_coroutine_threadsafe(
                self._voice_call.disable_video(),
                self._loop
            ).result(timeout=10.0)

            # Notify frontend of video state change
            if result and self._voice_call.current_call:
                self._notify_frontend('discordopus:video_state', {
                    'videoEnabled': self._voice_call.current_call.video_enabled,
                    'videoSource': self._voice_call.current_call.video_source,
                    'remoteVideo': self._voice_call.current_call.remote_video
                })

            return result
        except Exception as e:
            logger.error(f"Failed to disable video: {e}")
            return False

    def set_camera_device(self, device_id: int) -> None:
        """
        Set camera device for video calls.

        Args:
            device_id: Camera device ID from get_available_cameras()
        """
        if self._voice_call:
            self._voice_call.set_camera_device(device_id)

    def set_screen_monitor(self, monitor_index: int) -> None:
        """
        Set monitor for screen sharing.

        Args:
            monitor_index: Monitor index from get_available_monitors()
        """
        if self._voice_call:
            self._voice_call.set_screen_monitor(monitor_index)

    def get_video_state(self) -> Optional[Dict]:
        """
        Get current video state.

        Returns:
            Video state dict or None if no call
        """
        if not self._voice_call or not self._voice_call.current_call:
            return None
        call = self._voice_call.current_call
        return {
            'videoEnabled': call.video_enabled,
            'videoSource': call.video_source,
            'remoteVideo': call.remote_video
        }

    def list_cameras(self) -> List[Dict]:
        """
        List available cameras.

        Returns:
            List of camera info dicts with keys:
            - index: Camera device ID
            - name: Human-readable name
            - backend: OpenCV backend ID
            - path: Device path
        """
        return get_available_cameras()

    def list_monitors(self) -> List[Dict]:
        """
        List available monitors for screen sharing.

        Returns:
            List of monitor info dicts with keys:
            - index: Monitor index (1-based, 0 = all screens combined)
            - width: Width in pixels
            - height: Height in pixels
            - left: Left position
            - top: Top position
        """
        return get_available_monitors()

    def get_local_video_frame(self) -> Optional[str]:
        """
        Get current local video frame as base64 JPEG.

        Returns base64-encoded JPEG for efficient transmission to frontend.
        Returns None if no local video active.
        """
        if not self._voice_call or not self._voice_call._video_track:
            return None

        try:
            # Calls VoiceCallService.get_local_video_frame() (implemented in 06-02)
            frame = self._voice_call.get_local_video_frame()
            if frame is None:
                return None

            # Convert to JPEG base64
            import cv2
            import base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            logger.debug(f"Error getting local video frame: {e}")
            return None

    def get_remote_video_frame(self) -> Optional[str]:
        """
        Get current remote video frame as base64 JPEG.

        Returns base64-encoded JPEG for display in frontend.
        Returns None if no remote video active.
        """
        if not self._voice_call:
            return None

        try:
            # Calls VoiceCallService.get_remote_video_frame() (implemented in 06-02)
            frame = self._voice_call.get_remote_video_frame()
            if frame is None:
                return None

            import cv2
            import base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            logger.debug(f"Error getting remote video frame: {e}")
            return None


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
