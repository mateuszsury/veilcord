"""
Network service orchestrator for signaling, presence, and P2P messaging.

Manages the lifecycle of network components:
- SignalingClient for WebSocket connection
- PresenceManager for status tracking
- MessagingService for P2P encrypted messaging
- GroupService for group lifecycle
- GroupMessagingService for group messaging
- GroupCallMesh for group voice calls
- Frontend notification via window.evaluate_js()

Runs in a background thread started by webview.start(func=...).
"""

import asyncio
import json
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
from src.groups import (
    GroupService, GroupServiceCallbacks,
    GroupMessagingService, GroupMessagingCallbacks,
    GroupCallMesh, GroupCallCallbacks, GroupCallState,
    GroupMessage, SenderKeyDistribution
)
from src.groups.models import Group, GroupMember
from src.storage import groups as group_storage
from src.notifications.service import get_notification_service, NotificationService


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

        # Group services (initialized when identity is set)
        self._group_service: Optional[GroupService] = None
        self._group_messaging: Optional[GroupMessagingService] = None
        self._group_calls: Dict[str, GroupCallMesh] = {}  # group_id -> mesh
        self._identity: Optional[Any] = None  # Loaded identity for group operations

        # Notification service
        self._notifications: Optional[NotificationService] = None

        # Discovery: track discovered users (public_key -> {display_name, status})
        self._discovered_users: Dict[str, Dict[str, str]] = {}
        self._discovery_enabled = False

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
            self._identity = identity
            if identity and self._voice_call:
                self._voice_call.set_local_public_key(identity.shareable_id)

            # Initialize group services
            self._init_group_services()

            # Create notification service with callbacks
            self._notifications = get_notification_service()
            self._notifications.on_open_chat = self._on_notification_open_chat
            self._notifications.on_accept_call = self._on_notification_accept_call
            self._notifications.on_reject_call = self._on_notification_reject_call

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
                # Show Windows notification for incoming call
                if self._notifications:
                    from src.storage.contacts import get_contacts as get_all_contacts
                    contact = None
                    for c in get_all_contacts():
                        if c.ed25519_public_pem == from_key or from_key in c.ed25519_public_pem:
                            contact = c
                            break
                    caller_name = contact.display_name if contact else from_key[:16] + "..."
                    contact_id = contact.id if contact else 0
                    self._notifications.show_call_notification(caller_name, call_id, contact_id)

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

        elif msg_type == 'discovery_user':
            # User discovery update
            action = message.get('action')
            public_key = message.get('public_key')

            if action == 'join' and public_key:
                # New user discovered
                self._discovered_users[public_key] = {
                    'display_name': message.get('display_name', 'Anonymous'),
                    'status': message.get('status', 'online')
                }
                logger.info(f"Discovered user: {public_key[:16]}...")
                self._notify_frontend('discordopus:discovery_user', {
                    'action': 'join',
                    'publicKey': public_key,
                    'displayName': message.get('display_name', 'Anonymous'),
                    'status': message.get('status', 'online')
                })

            elif action == 'leave' and public_key:
                # User left discovery
                if public_key in self._discovered_users:
                    del self._discovered_users[public_key]
                    logger.info(f"User left discovery: {public_key[:16]}...")
                    self._notify_frontend('discordopus:discovery_user', {
                        'action': 'leave',
                        'publicKey': public_key
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
            msg_type = message.get('type', 'text')
            logger.debug(f"Incoming message for contact {contact_id}: {msg_type}")

            # Handle group message types
            if msg_type == "group_message":
                if self._group_messaging and self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._group_messaging.handle_group_message(message),
                        self._loop
                    )
                return

            if msg_type == "sender_key_distribution":
                if self._group_messaging and self._loop:
                    dist = SenderKeyDistribution.from_dict(message)
                    asyncio.run_coroutine_threadsafe(
                        self._group_messaging.handle_sender_key_distribution(dist),
                        self._loop
                    )
                return

            if msg_type == "group_call_start":
                self._handle_group_call_start(message)
                return

            if msg_type == "group_call_join":
                self._handle_group_call_join(message)
                return

            if msg_type == "group_call_offer":
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._handle_group_call_offer(message),
                        self._loop
                    )
                return

            if msg_type == "group_call_answer":
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._handle_group_call_answer(message),
                        self._loop
                    )
                return

            if msg_type == "group_call_leave":
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._handle_group_call_leave(message),
                        self._loop
                    )
                return

            # Regular P2P message
            self._notify_frontend('discordopus:message', {
                'contactId': contact_id,
                'message': message
            })

            # Show notification for incoming text messages
            if self._notifications and msg_type == 'text':
                from src.storage.contacts import get_contact
                contact = get_contact(contact_id)
                sender_name = contact.display_name if contact else "Unknown"
                body = message.get('body', '')[:100]
                self._notifications.show_message_notification(sender_name, body, contact_id)

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

    # ========== Group Service Methods ==========

    def _init_group_services(self) -> None:
        """Initialize group services after identity is available."""
        if not self._identity:
            return

        public_key = self._identity.ed25519_public_pem
        display_name = self._identity.display_name or "Anonymous"

        # Group service
        self._group_service = GroupService(public_key, display_name)
        self._group_service.set_callbacks(GroupServiceCallbacks(
            on_group_created=self._on_group_created,
            on_group_joined=self._on_group_joined,
            on_group_left=self._on_group_left,
            on_member_added=self._on_member_added,
            on_member_removed=self._on_member_removed,
        ))

        # Group messaging service
        self._group_messaging = GroupMessagingService(public_key)
        self._group_messaging.set_callbacks(GroupMessagingCallbacks(
            send_pairwise=self._send_pairwise_for_group,
            broadcast_group_message=self._broadcast_group_message,
            on_group_message=self._on_group_message_received,
        ))

    def _on_group_created(self, group: Group) -> None:
        """Handle group created event."""
        self._notify_frontend("discordopus:group_created", group.to_dict())

    def _on_group_joined(self, group: Group) -> None:
        """Handle group joined event."""
        self._notify_frontend("discordopus:group_joined", group.to_dict())
        # Distribute our sender key to existing members
        if self._group_messaging and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._group_messaging.distribute_sender_key(group.id),
                self._loop
            )

    def _on_group_left(self, group_id: str) -> None:
        """Handle group left event."""
        self._notify_frontend("discordopus:group_left", {"group_id": group_id})
        # Clean up group call if active
        if group_id in self._group_calls:
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._group_calls[group_id].leave_call(),
                    self._loop
                )
            del self._group_calls[group_id]

    def _on_member_added(self, group_id: str, member: GroupMember) -> None:
        """Handle member added to group."""
        self._notify_frontend("discordopus:group_member_added", {
            "group_id": group_id,
            "member": member.to_dict()
        })
        # Send our sender key to new member
        if self._group_messaging and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._group_messaging.handle_member_joined(group_id, member.public_key),
                self._loop
            )

    def _on_member_removed(self, group_id: str, public_key: str) -> None:
        """Handle member removed from group."""
        self._notify_frontend("discordopus:group_member_removed", {
            "group_id": group_id,
            "public_key": public_key
        })
        # Trigger key rotation
        if self._group_messaging and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._group_messaging.handle_member_removed(group_id, public_key),
                self._loop
            )

    # Group messaging callbacks

    def _send_pairwise_for_group(self, contact_key: str, message: dict) -> None:
        """Send pairwise encrypted message for group (sender key distribution)."""
        contact = self._find_contact_by_key(contact_key)
        if contact and self._messaging:
            peer = self._messaging._connections.get(contact.id)
            if peer and peer.data_channel and peer.data_channel.readyState == "open":
                # Encrypt with Signal Protocol and send via data channel
                if self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self._send_encrypted_pairwise(contact.id, json.dumps(message)),
                        self._loop
                    )

    async def _send_encrypted_pairwise(self, contact_id: int, plaintext: str) -> None:
        """Encrypt and send via pairwise Signal session."""
        from src.crypto.message_crypto import encrypt_message
        try:
            encrypted = await encrypt_message(contact_id, plaintext)
            # Send via data channel
            if self._messaging:
                peer = self._messaging._connections.get(contact_id)
                if peer and peer.data_channel and peer.data_channel.readyState == "open":
                    peer.data_channel.send(json.dumps(encrypted.to_dict()))
        except Exception as e:
            logger.error(f"Failed to send pairwise message: {e}")

    def _broadcast_group_message(self, group_id: str, message: dict) -> None:
        """Broadcast group message to all members."""
        members = group_storage.get_members(group_id)
        for member in members:
            if self._identity and member.public_key == self._identity.ed25519_public_pem:
                continue  # Skip self
            contact = self._find_contact_by_key(member.public_key)
            if contact and self._messaging:
                peer = self._messaging._connections.get(contact.id)
                if peer and peer.data_channel and peer.data_channel.readyState == "open":
                    peer.data_channel.send(json.dumps(message))

    def _on_group_message_received(
        self, group_id: str, sender_key: str, message_id: str, plaintext: str, timestamp: int
    ) -> None:
        """Handle decrypted group message."""
        self._notify_frontend("discordopus:group_message", {
            "group_id": group_id,
            "sender_public_key": sender_key,
            "message_id": message_id,
            "body": plaintext,
            "timestamp": timestamp
        })

    def _find_contact_by_key(self, public_key: str) -> Optional[Any]:
        """Find contact by public key."""
        from src.storage.contacts import get_all_contacts
        for contact in get_all_contacts():
            if contact.ed25519_public_pem == public_key:
                return contact
        return None

    # Group call signaling handlers

    def _handle_group_call_start(self, data: dict) -> None:
        """Handle incoming group call start."""
        group_id = data["group_id"]
        call_id = data["call_id"]
        from_key = data["from"]
        participants = data.get("participants", [])

        self._notify_frontend("discordopus:group_call_incoming", {
            "group_id": group_id,
            "call_id": call_id,
            "from": from_key,
            "participants": participants
        })

    def _handle_group_call_join(self, data: dict) -> None:
        """Handle participant joining group call."""
        group_id = data["group_id"]
        peer_key = data["from"]

        if group_id in self._group_calls and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._group_calls[group_id].handle_participant_joined(peer_key),
                self._loop
            )

    async def _handle_group_call_offer(self, data: dict) -> None:
        """Handle WebRTC offer for group call."""
        group_id = data["group_id"]
        peer_key = data["from"]
        sdp = data["sdp"]
        sdp_type = data.get("sdp_type", "offer")

        if group_id in self._group_calls:
            await self._group_calls[group_id].handle_offer(peer_key, sdp, sdp_type)

    async def _handle_group_call_answer(self, data: dict) -> None:
        """Handle WebRTC answer for group call."""
        group_id = data["group_id"]
        peer_key = data["from"]
        sdp = data["sdp"]
        sdp_type = data.get("sdp_type", "answer")

        if group_id in self._group_calls:
            await self._group_calls[group_id].handle_answer(peer_key, sdp, sdp_type)

    async def _handle_group_call_leave(self, data: dict) -> None:
        """Handle participant leaving group call."""
        group_id = data["group_id"]
        peer_key = data["from"]

        if group_id in self._group_calls:
            await self._group_calls[group_id].handle_participant_left(peer_key)

    def _send_group_call_signaling(self, peer_key: str, message: dict) -> None:
        """Send signaling message to specific peer."""
        contact = self._find_contact_by_key(peer_key)
        if contact and self._messaging:
            peer = self._messaging._connections.get(contact.id)
            if peer and peer.data_channel and peer.data_channel.readyState == "open":
                peer.data_channel.send(json.dumps(message))

    def _on_group_call_state_change(self, state: GroupCallState, group_id: str) -> None:
        """Handle group call state change."""
        self._notify_frontend("discordopus:group_call_state", {
            "group_id": group_id,
            "state": state.value
        })

    # ========== Notification Callbacks ==========

    def _on_notification_open_chat(self, contact_id: int) -> None:
        """Handle notification click to open chat."""
        logger.debug(f"Notification: open chat {contact_id}")
        # Notify frontend to switch to this chat
        self._notify_frontend('discordopus:open_chat', {
            'contactId': contact_id
        })

    def _on_notification_accept_call(self, call_id: str) -> None:
        """Handle notification accept call button."""
        logger.debug(f"Notification: accept call {call_id}")
        if self._voice_call:
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._voice_call.accept_call(),
                    self._loop
                )

    def _on_notification_reject_call(self, call_id: str) -> None:
        """Handle notification reject call button."""
        logger.debug(f"Notification: reject call {call_id}")
        if self._voice_call:
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._voice_call.reject_call(),
                    self._loop
                )

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

    def reconnect(self) -> bool:
        """
        Force reconnect to signaling server.

        Useful after identity creation or network issues.

        Returns:
            True if reconnect was initiated, False otherwise
        """
        url = self.get_signaling_server()
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._reconnect(url),
                self._loop
            )
            return True
        return False

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

    # ========== Discovery Methods ==========

    def is_discovery_enabled(self) -> bool:
        """Check if discovery is enabled."""
        return self._discovery_enabled

    def set_discovery_enabled(self, enabled: bool) -> bool:
        """
        Enable or disable discovery mode.

        When enabled, this user becomes visible to other users
        who also have discovery enabled.

        Args:
            enabled: True to enable discovery, False to disable

        Returns:
            True if operation was initiated, False otherwise
        """
        if enabled == self._discovery_enabled:
            return True

        self._discovery_enabled = enabled

        # Save to settings
        set_setting(Settings.DISCOVERY_ENABLED, "true" if enabled else "false")

        # Send to server
        if self._loop and self._signaling and self._state == ConnectionState.CONNECTED:
            if enabled:
                # Get display name from identity
                display_name = "Anonymous"
                if self._identity:
                    display_name = self._identity.display_name or "Anonymous"

                asyncio.run_coroutine_threadsafe(
                    self._send_discovery_enable(display_name),
                    self._loop
                )
            else:
                # Clear discovered users when disabling
                self._discovered_users.clear()
                asyncio.run_coroutine_threadsafe(
                    self._send_discovery_disable(),
                    self._loop
                )
            return True

        return False

    async def _send_discovery_enable(self, display_name: str) -> None:
        """Send discovery enable message to server."""
        if self._signaling:
            try:
                await self._signaling.send({
                    "type": "discovery_enable",
                    "display_name": display_name
                })
                logger.info(f"Discovery enabled as '{display_name}'")
            except Exception as e:
                logger.error(f"Failed to enable discovery: {e}")

    async def _send_discovery_disable(self) -> None:
        """Send discovery disable message to server."""
        if self._signaling:
            try:
                await self._signaling.send({
                    "type": "discovery_disable"
                })
                logger.info("Discovery disabled")
            except Exception as e:
                logger.error(f"Failed to disable discovery: {e}")

    def get_discovered_users(self) -> List[Dict[str, Any]]:
        """
        Get list of discovered users.

        Returns:
            List of dicts with publicKey, displayName, status
        """
        return [
            {
                'publicKey': pk,
                'displayName': data['display_name'],
                'status': data['status']
            }
            for pk, data in self._discovered_users.items()
        ]

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

    # ========== Group Lifecycle Methods ==========

    def create_group(self, name: str) -> dict:
        """Create a new group."""
        if not self._group_service:
            raise RuntimeError("Group service not initialized")
        group = self._group_service.create_group(name)
        return group.to_dict()

    def get_groups(self) -> List[dict]:
        """Get all groups."""
        if not self._group_service:
            return []
        return [g.to_dict() for g in self._group_service.get_all_groups()]

    def get_group(self, group_id: str) -> Optional[dict]:
        """Get a specific group."""
        if not self._group_service:
            return None
        group = self._group_service.get_group(group_id)
        return group.to_dict() if group else None

    def generate_invite(self, group_id: str) -> str:
        """Generate invite code for group."""
        if not self._group_service:
            raise RuntimeError("Group service not initialized")
        return self._group_service.generate_invite(group_id)

    def join_group(self, invite_code: str) -> dict:
        """Join group via invite code."""
        if not self._group_service:
            raise RuntimeError("Group service not initialized")
        group = self._group_service.join_group(invite_code)
        return group.to_dict()

    def leave_group(self, group_id: str) -> bool:
        """Leave a group."""
        if not self._group_service:
            return False
        return self._group_service.leave_group(group_id)

    def get_group_members(self, group_id: str) -> List[dict]:
        """Get members of a group."""
        if not self._group_service:
            return []
        return [m.to_dict() for m in self._group_service.get_members(group_id)]

    def remove_group_member(self, group_id: str, public_key: str) -> bool:
        """Remove member from group (admin only)."""
        if not self._group_service:
            return False
        return self._group_service.remove_member(group_id, public_key)

    # ========== Group Messaging Methods ==========

    async def send_group_message(self, group_id: str, message_id: str, text: str) -> dict:
        """Send message to group."""
        if not self._group_messaging:
            raise RuntimeError("Group messaging not initialized")
        message = await self._group_messaging.send_group_message(group_id, message_id, text)
        return message.to_dict()

    # ========== Group Call Methods ==========

    def start_group_call(self, group_id: str, call_id: str) -> dict:
        """Start a group voice call."""
        if not self._identity:
            raise RuntimeError("Identity not initialized")

        members = group_storage.get_members(group_id)
        participants = [m.public_key for m in members]

        mesh = GroupCallMesh(self._identity.ed25519_public_pem, group_id)
        mesh.set_callbacks(GroupCallCallbacks(
            send_signaling=self._send_group_call_signaling,
            broadcast_signaling=self._broadcast_group_message,
            on_state_change=self._on_group_call_state_change,
            on_participant_joined=lambda g, p: self._notify_frontend(
                "discordopus:group_call_participant_joined", {"group_id": g, "peer": p}
            ),
            on_participant_left=lambda g, p: self._notify_frontend(
                "discordopus:group_call_participant_left", {"group_id": g, "peer": p}
            ),
        ))

        self._group_calls[group_id] = mesh

        # Start call asynchronously
        async def start():
            estimate = await mesh.start_call(call_id, participants)
            self._notify_frontend("discordopus:group_call_started", {
                "group_id": group_id,
                "call_id": call_id,
                "bandwidth": {
                    "upload_kbps": estimate.upload_kbps,
                    "download_kbps": estimate.download_kbps,
                    "warning": estimate.warning,
                    "message": estimate.message
                }
            })

        if self._loop:
            asyncio.run_coroutine_threadsafe(start(), self._loop)
        return {"group_id": group_id, "call_id": call_id, "status": "starting"}

    def join_group_call(self, group_id: str, call_id: str) -> dict:
        """Join an existing group call."""
        if not self._identity:
            raise RuntimeError("Identity not initialized")

        members = group_storage.get_members(group_id)
        participants = [m.public_key for m in members]

        mesh = GroupCallMesh(self._identity.ed25519_public_pem, group_id)
        mesh.set_callbacks(GroupCallCallbacks(
            send_signaling=self._send_group_call_signaling,
            broadcast_signaling=self._broadcast_group_message,
            on_state_change=self._on_group_call_state_change,
            on_participant_joined=lambda g, p: self._notify_frontend(
                "discordopus:group_call_participant_joined", {"group_id": g, "peer": p}
            ),
            on_participant_left=lambda g, p: self._notify_frontend(
                "discordopus:group_call_participant_left", {"group_id": g, "peer": p}
            ),
        ))

        self._group_calls[group_id] = mesh

        async def join():
            estimate = await mesh.join_call(call_id, participants)
            self._notify_frontend("discordopus:group_call_joined", {
                "group_id": group_id,
                "call_id": call_id,
                "bandwidth": {
                    "upload_kbps": estimate.upload_kbps,
                    "download_kbps": estimate.download_kbps,
                    "warning": estimate.warning,
                    "message": estimate.message
                }
            })

        if self._loop:
            asyncio.run_coroutine_threadsafe(join(), self._loop)
        return {"group_id": group_id, "call_id": call_id, "status": "joining"}

    def leave_group_call(self, group_id: str) -> bool:
        """Leave group call."""
        if group_id not in self._group_calls:
            return False
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._group_calls[group_id].leave_call(),
                self._loop
            )
        return True

    def set_group_call_muted(self, group_id: str, muted: bool) -> bool:
        """Mute/unmute in group call."""
        if group_id not in self._group_calls:
            return False
        self._group_calls[group_id].set_muted(muted)
        return True


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
