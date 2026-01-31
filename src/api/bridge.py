"""
PyWebView API bridge - exposes Python methods to JavaScript.

All methods in this class are available as window.pywebview.api.method_name()
in the React frontend.

IMPORTANT: All methods should return JSON-serializable values (dict, list, str, int, bool, None).
Complex objects should be converted to dicts.
"""

from typing import Optional, List, Dict, Any

from src.storage.identity_store import (
    get_or_create_identity,
    load_identity,
    update_display_name,
    save_identity
)
from src.storage.contacts import (
    get_contacts as _get_contacts,
    add_contact as _add_contact,
    remove_contact as _remove_contact,
    set_contact_verified as _set_contact_verified,
    Contact
)
from src.crypto.backup import (
    export_backup,
    import_backup,
    BackupError
)
from src.crypto.identity import Identity
from src.crypto.fingerprint import format_fingerprint
from src.network.service import get_network_service
from src.updates.service import get_update_service
from src.updates.settings import CURRENT_VERSION


class API:
    """
    PyWebView API class exposed to JavaScript.

    Usage in JavaScript:
        await window.pywebview.api.get_identity()
    """

    def _identity_to_dict(self, identity: Optional[Identity]) -> Optional[Dict[str, Any]]:
        """Convert Identity to JSON-serializable dict."""
        if identity is None:
            return None

        return {
            'publicKey': identity.shareable_id,
            'fingerprint': identity.fingerprint,
            'fingerprintFormatted': format_fingerprint(identity.fingerprint),
            'displayName': identity.display_name
        }

    def _contact_to_dict(self, contact: Contact) -> Dict[str, Any]:
        """Convert Contact to JSON-serializable dict."""
        return {
            'id': contact.id,
            'publicKey': contact.ed25519_public_pem,  # For display - could extract hex
            'fingerprint': contact.fingerprint,
            'fingerprintFormatted': format_fingerprint(contact.fingerprint),
            'displayName': contact.display_name,
            'verified': contact.verified,
            'addedAt': contact.added_at,
            'onlineStatus': contact.online_status
        }

    # ========== Identity Methods ==========

    def get_identity(self) -> Optional[Dict[str, Any]]:
        """Get current identity or None if not created."""
        identity = load_identity()
        return self._identity_to_dict(identity)

    def generate_identity(self, display_name: str = "Anonymous") -> Dict[str, Any]:
        """Generate new identity (creates if doesn't exist)."""
        identity = get_or_create_identity(display_name)
        return self._identity_to_dict(identity)

    def update_display_name(self, name: str) -> None:
        """Update identity display name."""
        update_display_name(name)

    # ========== Backup Methods ==========

    def export_backup(self, password: str) -> Dict[str, Any]:
        """
        Export identity as encrypted backup.

        Returns:
            Dict with 'backup' key containing JSON string
        """
        identity = load_identity()
        if identity is None:
            raise ValueError("No identity to backup")

        backup_json = export_backup(identity, password)
        return {'backup': backup_json}

    def import_backup(self, backup_json: str, password: str) -> Dict[str, Any]:
        """
        Import identity from encrypted backup.

        Returns:
            Imported identity dict
        """
        try:
            identity = import_backup(backup_json, password)
            save_identity(identity)
            return self._identity_to_dict(identity)
        except BackupError as e:
            raise ValueError(str(e)) from e

    # ========== Contact Methods ==========

    def get_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts."""
        contacts = _get_contacts()
        return [self._contact_to_dict(c) for c in contacts]

    def add_contact(self, public_key: str, display_name: str) -> Dict[str, Any]:
        """
        Add contact by public key.

        Args:
            public_key: Ed25519 public key as hex string (64 chars)
            display_name: Name to show for this contact
        """
        contact = _add_contact(public_key, display_name)
        return self._contact_to_dict(contact)

    def remove_contact(self, contact_id: int) -> None:
        """Remove contact by ID."""
        _remove_contact(contact_id)

    def set_contact_verified(self, contact_id: int, verified: bool) -> None:
        """Set contact verification status."""
        _set_contact_verified(contact_id, verified)

    # ========== Network Methods ==========

    def get_connection_state(self) -> str:
        """Get current signaling connection state."""
        try:
            service = get_network_service()
            return service.get_connection_state()
        except RuntimeError:
            return "disconnected"  # Service not started yet

    def get_signaling_server(self) -> str:
        """Get configured signaling server URL."""
        service = get_network_service()
        return service.get_signaling_server()

    def set_signaling_server(self, url: str) -> None:
        """Set signaling server URL (will reconnect)."""
        service = get_network_service()
        service.set_signaling_server(url)

    def get_user_status(self) -> str:
        """Get user's presence status."""
        service = get_network_service()
        return service.get_user_status()

    def set_user_status(self, status: str) -> None:
        """Set user's presence status (online/away/busy/invisible)."""
        valid_statuses = ["online", "away", "busy", "invisible"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        service = get_network_service()
        service.set_user_status(status)

    # ========== Messaging Methods ==========

    def initiate_p2p_connection(self, contact_id: int) -> None:
        """
        Initiate P2P connection to a contact.

        Sends WebRTC offer via signaling server.
        Connection state updates come via discordopus:p2p_state events.

        Args:
            contact_id: Contact database ID
        """
        service = get_network_service()
        service.initiate_p2p_connection(contact_id)

    def send_message(
        self,
        contact_id: int,
        body: str,
        reply_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send encrypted text message to a contact.

        The message is encrypted with Signal Protocol and sent over
        the P2P data channel. Also stored locally.

        Args:
            contact_id: Contact database ID
            body: Message text
            reply_to: Optional message ID being replied to

        Returns:
            Message dict with id, timestamp, etc. or None if failed
        """
        service = get_network_service()
        return service.send_text_message(contact_id, body, reply_to)

    def get_messages(
        self,
        contact_id: int,
        limit: int = 50,
        before: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            contact_id: Contact database ID
            limit: Maximum messages to return
            before: Timestamp for pagination (get older messages)

        Returns:
            List of message dicts (most recent first)
        """
        # Use MessagingService for this
        service = get_network_service()
        if service._messaging:
            return service._messaging.get_messages(contact_id, limit, before)
        return []

    def get_p2p_state(self, contact_id: int) -> str:
        """
        Get P2P connection state for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            State string: new, connecting, connected, disconnected, failed, closed
        """
        service = get_network_service()
        return service.get_p2p_connection_state(contact_id)

    def send_typing(self, contact_id: int, active: bool = True) -> None:
        """
        Send typing indicator to a contact.

        Throttled to max once per 3 seconds.

        Args:
            contact_id: Contact database ID
            active: True if typing, False if stopped
        """
        service = get_network_service()
        service.send_typing_indicator(contact_id, active)

    def edit_message(
        self,
        contact_id: int,
        message_id: str,
        new_body: str
    ) -> Dict[str, Any]:
        """
        Edit a previously sent message.

        Args:
            contact_id: Contact database ID
            message_id: ID of message to edit
            new_body: New message text

        Returns:
            Dict with success status and optional error
        """
        service = get_network_service()
        if not service._loop or not service._messaging:
            return {"success": False, "error": "Service not ready"}

        import asyncio
        future = asyncio.run_coroutine_threadsafe(
            service._messaging.edit_message(contact_id, message_id, new_body),
            service._loop
        )
        try:
            result = future.result(timeout=10.0)
            return {"success": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_message(
        self,
        contact_id: int,
        message_id: str
    ) -> Dict[str, Any]:
        """
        Delete a message (soft delete).

        Args:
            contact_id: Contact database ID
            message_id: ID of message to delete

        Returns:
            Dict with success status and optional error
        """
        service = get_network_service()
        if not service._loop or not service._messaging:
            return {"success": False, "error": "Service not ready"}

        import asyncio
        future = asyncio.run_coroutine_threadsafe(
            service._messaging.delete_message(contact_id, message_id),
            service._loop
        )
        try:
            result = future.result(timeout=10.0)
            return {"success": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_reaction(
        self,
        contact_id: int,
        message_id: str,
        emoji: str
    ) -> Dict[str, Any]:
        """
        Add an emoji reaction to a message.

        Args:
            contact_id: Contact database ID
            message_id: ID of message to react to
            emoji: Unicode emoji character

        Returns:
            Dict with success status
        """
        service = get_network_service()
        if not service._loop or not service._messaging:
            return {"success": False, "error": "Service not ready"}

        import asyncio
        future = asyncio.run_coroutine_threadsafe(
            service._messaging.send_reaction(contact_id, message_id, emoji, "add"),
            service._loop
        )
        try:
            result = future.result(timeout=10.0)
            return {"success": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_reaction(
        self,
        contact_id: int,
        message_id: str,
        emoji: str
    ) -> Dict[str, Any]:
        """
        Remove an emoji reaction from a message.

        Args:
            contact_id: Contact database ID
            message_id: ID of message to unreact
            emoji: Unicode emoji character to remove

        Returns:
            Dict with success status
        """
        service = get_network_service()
        if not service._loop or not service._messaging:
            return {"success": False, "error": "Service not ready"}

        import asyncio
        future = asyncio.run_coroutine_threadsafe(
            service._messaging.send_reaction(contact_id, message_id, emoji, "remove"),
            service._loop
        )
        try:
            result = future.result(timeout=10.0)
            return {"success": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_reactions(self, message_id: str) -> List[Dict[str, Any]]:
        """
        Get all reactions for a message.

        Args:
            message_id: ID of message

        Returns:
            List of reaction dicts with emoji, senderId, timestamp
        """
        from src.storage.messages import get_reactions as storage_get_reactions
        reactions = storage_get_reactions(message_id)
        return [{
            "id": r.id,
            "messageId": r.message_id,
            "senderId": r.sender_id,
            "emoji": r.emoji,
            "timestamp": r.timestamp
        } for r in reactions]

    # ========== File Transfer Methods ==========

    def send_file(self, contact_id: int, file_path: str) -> Dict[str, Any]:
        """
        Send a file to a contact.

        Args:
            contact_id: Contact database ID
            file_path: Absolute path to file

        Returns:
            Dict with transferId on success or error on failure
        """
        try:
            service = get_network_service()
            transfer_id = service.send_file(contact_id, file_path)
            if transfer_id:
                return {"transferId": transfer_id}
            else:
                return {"error": "Failed to start transfer (no P2P connection?)"}
        except Exception as e:
            return {"error": str(e)}

    def cancel_transfer(
        self,
        contact_id: int,
        transfer_id: str,
        direction: str = "send"
    ) -> Dict[str, Any]:
        """
        Cancel a file transfer.

        Args:
            contact_id: Contact database ID
            transfer_id: Transfer UUID
            direction: "send" or "receive"

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.cancel_transfer(contact_id, transfer_id, direction)
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resume_transfer(
        self,
        contact_id: int,
        transfer_id: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Resume an interrupted file transfer.

        Args:
            contact_id: Contact database ID
            transfer_id: Original transfer UUID
            file_path: Path to the file (must be same file)

        Returns:
            Dict with new transferId on success or error on failure
        """
        try:
            service = get_network_service()
            new_transfer_id = service.resume_file(contact_id, transfer_id, file_path)
            if new_transfer_id:
                return {"transferId": new_transfer_id}
            else:
                return {"error": "Failed to resume transfer (check file path and P2P connection)"}
        except Exception as e:
            return {"error": str(e)}

    def get_transfers(self, contact_id: int) -> Dict[str, Any]:
        """
        Get all transfers for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            Dict with active and resumable transfer lists
        """
        try:
            service = get_network_service()
            active = service.get_active_transfers(contact_id)
            resumable = service.get_resumable_transfers(contact_id)
            return {
                "active": active,
                "resumable": resumable
            }
        except Exception as e:
            return {"active": [], "resumable": [], "error": str(e)}

    def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Get file data by ID.

        Args:
            file_id: File UUID from database

        Returns:
            Dict with file metadata and base64 data, or error
        """
        try:
            from src.storage.files import get_file_metadata, retrieve_file_data
            import base64

            metadata = get_file_metadata(file_id)
            if not metadata:
                return {"error": "File not found"}

            data = retrieve_file_data(file_id)
            if not data:
                return {"error": "File data not found"}

            return {
                "id": metadata.id,
                "filename": metadata.filename,
                "mimeType": metadata.mime_type,
                "size": metadata.size,
                "data": base64.b64encode(data).decode('utf-8')
            }
        except Exception as e:
            return {"error": str(e)}

    def open_file_dialog(self) -> Dict[str, Any]:
        """
        Open native file picker dialog.

        Returns:
            Dict with path, name, size on success, or cancelled: true if cancelled
        """
        try:
            import tkinter as tk
            from tkinter import filedialog
            from pathlib import Path

            # Create hidden root window
            root = tk.Tk()
            root.withdraw()

            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select file to send",
                filetypes=[("All files", "*.*")]
            )

            # Clean up
            root.destroy()

            if not file_path:
                return {"cancelled": True}

            # Get file info
            path = Path(file_path)
            size = path.stat().st_size

            return {
                "path": str(path.absolute()),
                "name": path.name,
                "size": size
            }
        except Exception as e:
            return {"error": str(e)}

    def get_file_preview(self, file_id: int) -> Dict[str, Any]:
        """
        Get preview/thumbnail for an image or video file.

        Args:
            file_id: File database ID

        Returns:
            Dict with preview data (base64 JPEG) or error
        """
        try:
            from src.storage.files import get_file
            from src.file_transfer.preview import get_preview
            import base64

            result = get_file(file_id)
            if not result:
                return {"error": "File not found"}

            metadata, data = result

            # Generate preview
            preview_data = get_preview(
                data,
                metadata.mime_type,
                file_id=str(file_id)
            )

            if not preview_data:
                return {"error": "Preview not available for this file type"}

            # Return base64-encoded JPEG
            return {
                "preview": base64.b64encode(preview_data).decode('utf-8'),
                "mimeType": "image/jpeg"
            }
        except Exception as e:
            return {"error": str(e)}

    # ========== Voice Call Methods ==========

    def start_call(self, contact_id: int) -> Dict[str, Any]:
        """
        Start voice call with contact.

        Args:
            contact_id: Contact database ID

        Returns:
            Dict with callId on success or error on failure
        """
        try:
            service = get_network_service()
            call_id = service.start_voice_call(contact_id)
            if call_id:
                return {"callId": call_id}
            return {"error": "Failed to start call (contact offline or busy)"}
        except Exception as e:
            return {"error": str(e)}

    def accept_call(self) -> Dict[str, Any]:
        """
        Accept incoming voice call.

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.accept_voice_call()
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reject_call(self) -> Dict[str, Any]:
        """
        Reject incoming voice call.

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.reject_voice_call()
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def end_call(self) -> Dict[str, Any]:
        """
        End current voice call.

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.end_voice_call()
            return {"success": success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_muted(self, muted: bool) -> None:
        """
        Mute/unmute call microphone.

        Args:
            muted: True to mute, False to unmute
        """
        service = get_network_service()
        service.set_call_muted(muted)

    def is_muted(self) -> bool:
        """
        Check if call is muted.

        Returns:
            True if muted, False otherwise
        """
        service = get_network_service()
        return service.is_call_muted()

    def get_call_state(self) -> Optional[Dict[str, Any]]:
        """
        Get current call state.

        Returns:
            Call state dict or None if no call
        """
        service = get_network_service()
        return service.get_call_state()

    # ========== Voice Message Methods ==========

    def start_voice_recording(self) -> Dict[str, Any]:
        """
        Start recording voice message.

        Returns:
            Dict with recordingPath on success or error on failure
        """
        try:
            from src.voice.voice_message import VoiceMessageRecorder
            service = get_network_service()
            if not hasattr(service, '_voice_recorder') or service._voice_recorder is None:
                service._voice_recorder = VoiceMessageRecorder()

            import asyncio
            future = asyncio.run_coroutine_threadsafe(
                service._voice_recorder.start_recording(),
                service._loop
            )
            path = future.result(timeout=5.0)
            return {"recordingPath": str(path)}
        except Exception as e:
            return {"error": str(e)}

    def stop_voice_recording(self) -> Dict[str, Any]:
        """
        Stop recording and get metadata.

        Returns:
            Dict with duration and path on success
        """
        try:
            service = get_network_service()
            if not hasattr(service, '_voice_recorder') or service._voice_recorder is None:
                return {"error": "No recording in progress"}

            import asyncio
            future = asyncio.run_coroutine_threadsafe(
                service._voice_recorder.stop_recording(),
                service._loop
            )
            metadata = future.result(timeout=5.0)
            service._voice_recorder = None

            if metadata is None:
                return {"error": "Recording too short"}

            return {
                "id": metadata.id,
                "duration": metadata.duration_seconds,
                "path": str(metadata.file_path)
            }
        except Exception as e:
            return {"error": str(e)}

    def cancel_voice_recording(self) -> Dict[str, Any]:
        """
        Cancel current voice recording.

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            if hasattr(service, '_voice_recorder') and service._voice_recorder:
                import asyncio
                future = asyncio.run_coroutine_threadsafe(
                    service._voice_recorder.cancel(),
                    service._loop
                )
                future.result(timeout=5.0)
                service._voice_recorder = None
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recording_duration(self) -> float:
        """
        Get current recording duration in seconds.

        Returns:
            Duration in seconds (0 if not recording)
        """
        service = get_network_service()
        if hasattr(service, '_voice_recorder') and service._voice_recorder:
            return service._voice_recorder.get_duration()
        return 0.0

    def get_audio_devices(self) -> Dict[str, Any]:
        """
        Get available audio input and output devices.

        Returns:
            Dict with inputs and outputs lists
        """
        try:
            from src.voice import get_input_devices, get_output_devices
            return {
                "inputs": get_input_devices(),
                "outputs": get_output_devices()
            }
        except Exception as e:
            return {"inputs": [], "outputs": [], "error": str(e)}

    def set_audio_devices(self, input_id: Optional[int], output_id: Optional[int]) -> None:
        """
        Set audio devices to use for calls.

        Args:
            input_id: Input (microphone) device ID, or None for default
            output_id: Output (speaker) device ID, or None for default
        """
        service = get_network_service()
        if service._voice_call:
            service._voice_call.set_audio_devices(input_id, output_id)

    # ========== Video Call Methods ==========

    def enable_video(self, source: str = "camera") -> Dict:
        """
        Enable video during call.

        Args:
            source: "camera" or "screen"

        Returns:
            {"success": True} or {"error": str}
        """
        try:
            service = get_network_service()
            success = service.enable_video(source)
            if success:
                return {"success": True, "source": source}
            return {"error": "Failed to enable video"}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def disable_video(self) -> Dict:
        """
        Disable video during call.

        Returns:
            {"success": True} or {"error": str}
        """
        try:
            service = get_network_service()
            success = service.disable_video()
            if success:
                return {"success": True}
            return {"error": "Failed to disable video"}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def set_camera(self, device_id: int) -> Dict:
        """
        Set camera device for video calls.

        Args:
            device_id: Camera device ID from get_cameras()

        Returns:
            {"success": True} or {"error": str}
        """
        try:
            service = get_network_service()
            service.set_camera_device(device_id)
            return {"success": True}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def set_screen_monitor(self, monitor_index: int) -> Dict:
        """
        Set monitor for screen sharing.

        Args:
            monitor_index: Monitor index from get_monitors()

        Returns:
            {"success": True} or {"error": str}
        """
        try:
            service = get_network_service()
            service.set_screen_monitor(monitor_index)
            return {"success": True}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def get_video_state(self) -> Dict:
        """
        Get current video state.

        Returns:
            Video state dict with videoEnabled, videoSource, remoteVideo
        """
        try:
            service = get_network_service()
            state = service.get_video_state()
            if state:
                return state
            return {"videoEnabled": False, "videoSource": None, "remoteVideo": False}
        except RuntimeError:
            return {"videoEnabled": False, "videoSource": None, "remoteVideo": False}
        except Exception as e:
            return {"error": str(e)}

    def get_cameras(self) -> Dict:
        """
        List available cameras.

        Returns:
            {"cameras": [...]} with list of camera info dicts
        """
        try:
            from src.voice import get_available_cameras
            cameras = get_available_cameras()
            return {"cameras": cameras}
        except Exception as e:
            return {"cameras": [], "error": str(e)}

    def get_monitors(self) -> Dict:
        """
        List available monitors for screen sharing.

        Returns:
            {"monitors": [...]} with list of monitor info dicts
        """
        try:
            from src.voice import get_available_monitors
            monitors = get_available_monitors()
            return {"monitors": monitors}
        except Exception as e:
            return {"monitors": [], "error": str(e)}

    # ========== Video Frame Methods ==========

    def get_local_video_frame(self) -> Dict:
        """Get current local video frame as base64."""
        try:
            service = get_network_service()
            frame = service.get_local_video_frame()
            if frame:
                return {"frame": frame}
            return {"frame": None}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def get_remote_video_frame(self) -> Dict:
        """Get current remote video frame as base64."""
        try:
            service = get_network_service()
            frame = service.get_remote_video_frame()
            if frame:
                return {"frame": frame}
            return {"frame": None}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    # ========== Group Methods ==========

    def create_group(self, name: str) -> Dict[str, Any]:
        """
        Create a new group.

        Args:
            name: Group display name

        Returns:
            Created group object
        """
        try:
            service = get_network_service()
            return service.create_group(name)
        except RuntimeError:
            return {"error": "Network not initialized"}
        except Exception as e:
            return {"error": str(e)}

    def get_groups(self) -> List[Dict[str, Any]]:
        """
        Get all groups the user is in.

        Returns:
            List of group objects
        """
        try:
            service = get_network_service()
            return service.get_groups()
        except RuntimeError:
            return []
        except Exception as e:
            return []

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific group by ID.

        Args:
            group_id: Group UUID

        Returns:
            Group object or None
        """
        try:
            service = get_network_service()
            return service.get_group(group_id)
        except RuntimeError:
            return None
        except Exception as e:
            return None

    def generate_group_invite(self, group_id: str) -> Dict[str, Any]:
        """
        Generate invite code for a group.

        Args:
            group_id: Group UUID

        Returns:
            Dict with invite URL or error
        """
        try:
            service = get_network_service()
            invite = service.generate_invite(group_id)
            return {"invite": invite}
        except RuntimeError:
            return {"error": "Network not initialized"}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def join_group(self, invite_code: str) -> Dict[str, Any]:
        """
        Join a group via invite code.

        Args:
            invite_code: Invite URL or raw code

        Returns:
            Joined group object or error
        """
        try:
            service = get_network_service()
            return service.join_group(invite_code)
        except RuntimeError:
            return {"error": "Network not initialized"}
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def leave_group(self, group_id: str) -> Dict[str, Any]:
        """
        Leave a group.

        Args:
            group_id: Group UUID

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.leave_group(group_id)
            return {"success": success}
        except RuntimeError:
            return {"success": False, "error": "Network not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a group.

        Args:
            group_id: Group UUID

        Returns:
            List of member objects
        """
        try:
            service = get_network_service()
            return service.get_group_members(group_id)
        except RuntimeError:
            return []
        except Exception as e:
            return []

    def remove_group_member(self, group_id: str, public_key: str) -> Dict[str, Any]:
        """
        Remove a member from a group (admin only).

        Args:
            group_id: Group UUID
            public_key: Member's public key to remove

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.remove_group_member(group_id, public_key)
            return {"success": success}
        except RuntimeError:
            return {"success": False, "error": "Network not initialized"}
        except PermissionError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========== Group Messaging Methods ==========

    def send_group_message(self, group_id: str, message_id: str, text: str) -> Dict[str, Any]:
        """
        Send a message to a group.

        Args:
            group_id: Group UUID
            message_id: Unique message ID
            text: Message text

        Returns:
            Sent message object or error
        """
        try:
            import asyncio
            service = get_network_service()
            if not service._loop:
                return {"error": "Network not initialized"}
            future = asyncio.run_coroutine_threadsafe(
                service.send_group_message(group_id, message_id, text),
                service._loop
            )
            return future.result(timeout=10.0)
        except RuntimeError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    # ========== Group Call Methods ==========

    def start_group_call(self, group_id: str, call_id: str) -> Dict[str, Any]:
        """
        Start a group voice call.

        Args:
            group_id: Group UUID
            call_id: Unique call ID

        Returns:
            Call status object
        """
        try:
            service = get_network_service()
            return service.start_group_call(group_id, call_id)
        except RuntimeError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def join_group_call(self, group_id: str, call_id: str) -> Dict[str, Any]:
        """
        Join an existing group call.

        Args:
            group_id: Group UUID
            call_id: Call ID to join

        Returns:
            Call status object
        """
        try:
            service = get_network_service()
            return service.join_group_call(group_id, call_id)
        except RuntimeError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def leave_group_call(self, group_id: str) -> Dict[str, Any]:
        """
        Leave a group call.

        Args:
            group_id: Group UUID

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.leave_group_call(group_id)
            return {"success": success}
        except RuntimeError:
            return {"success": False, "error": "Network not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_group_call_muted(self, group_id: str, muted: bool) -> Dict[str, Any]:
        """
        Mute/unmute microphone in group call.

        Args:
            group_id: Group UUID
            muted: True to mute

        Returns:
            Dict with success status
        """
        try:
            service = get_network_service()
            success = service.set_group_call_muted(group_id, muted)
            return {"success": success}
        except RuntimeError:
            return {"success": False, "error": "Network not initialized"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_group_call_bandwidth(self, participant_count: int) -> Dict[str, Any]:
        """
        Estimate bandwidth requirements for group call.

        Args:
            participant_count: Number of participants

        Returns:
            Bandwidth estimate with warning if needed
        """
        try:
            from src.groups import GroupCallMesh
            estimate = GroupCallMesh.estimate_bandwidth(participant_count)
            return {
                "upload_kbps": estimate.upload_kbps,
                "download_kbps": estimate.download_kbps,
                "total_kbps": estimate.total_kbps,
                "participant_count": estimate.participant_count,
                "warning": estimate.warning,
                "message": estimate.message
            }
        except Exception as e:
            return {"error": str(e)}

    # ========== Update Methods ==========

    def get_app_version(self) -> str:
        """Get current application version."""
        return CURRENT_VERSION

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check for available updates.

        Returns:
            Dict with version and changelog if available, None otherwise
        """
        try:
            service = get_update_service()
            version = service.check_for_updates()
            if version:
                return service.get_available_update()
            return None
        except Exception as e:
            print(f"Update check failed: {e}")
            return None

    def download_update(self) -> Dict[str, Any]:
        """
        Download and install available update.

        Returns:
            Dict with 'success' bool and optional 'error' message
        """
        try:
            service = get_update_service()
            success = service.download_and_install()
            if success:
                return {
                    'success': True,
                    'message': 'Update downloaded. Please restart the app to apply.'
                }
            return {
                'success': False,
                'error': 'Update download failed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_update_status(self) -> Dict[str, Any]:
        """
        Get current update status.

        Returns:
            Dict with available update info or None
        """
        try:
            service = get_update_service()
            return {
                'currentVersion': service.get_current_version(),
                'updateAvailable': service.is_update_available(),
                'availableUpdate': service.get_available_update()
            }
        except Exception as e:
            return {
                'currentVersion': CURRENT_VERSION,
                'updateAvailable': False,
                'availableUpdate': None,
                'error': str(e)
            }

    # ========== System Methods ==========

    def ping(self) -> str:
        """Test method to verify bridge is working."""
        return "pong"
