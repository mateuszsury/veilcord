"""
File transfer service for orchestrating send/receive operations.

Manages multiple concurrent transfers per contact, handles message routing,
persists transfer state for resume capability.

IMPORTANT: This service is responsible for:
- Creating and tracking FileSender/FileReceiver instances
- Routing incoming messages to the correct receiver
- Enforcing concurrency limits per contact
- Persisting transfer state to database
- Providing callbacks for frontend notifications
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from src.file_transfer.sender import FileSender
from src.file_transfer.receiver import FileReceiver
from src.file_transfer.protocol import (
    EOF_MARKER,
    CANCEL_MARKER,
    ACK_MARKER,
    ERROR_MARKER,
    FileMessageType
)
from src.file_transfer.models import (
    TransferState,
    TransferDirection,
    TransferProgress,
    FileTransferMetadata
)
from src.storage.db import (
    save_transfer_state,
    get_transfer_state,
    get_pending_transfers,
    update_transfer_progress,
    delete_transfer
)
from src.storage.files import FileMetadata

logger = logging.getLogger(__name__)


@dataclass
class FileTransferService:
    """
    Orchestrates file transfers for all contacts.

    Usage:
        service = FileTransferService()
        service.on_transfer_progress = lambda contact_id, progress: update_ui(progress)
        service.on_file_received = lambda contact_id, file_meta: show_notification(file_meta)

        # Send file
        transfer_id = await service.send_file(contact_id, peer, file_path)

        # Handle incoming messages
        await service.handle_incoming_message(contact_id, peer, message)

        # Get active transfers
        transfers = service.get_active_transfers(contact_id)
    """
    max_concurrent_per_contact: int = 3

    # Active transfers: (contact_id, transfer_id) -> (sender/receiver, task)
    _senders: Dict[Tuple[int, str], Tuple[FileSender, asyncio.Task]] = field(
        default_factory=dict, init=False
    )
    _receivers: Dict[Tuple[int, str], FileReceiver] = field(
        default_factory=dict, init=False
    )

    # Callbacks
    on_transfer_progress: Optional[Callable[[int, TransferProgress], None]] = None
    on_file_received: Optional[Callable[[int, FileMetadata], None]] = None
    on_transfer_complete: Optional[Callable[[int, str], None]] = None
    on_transfer_error: Optional[Callable[[int, str, str], None]] = None

    async def send_file(
        self,
        contact_id: int,
        peer: "PeerConnection",
        file_path: Path,
        resume_offset: int = 0
    ) -> str:
        """
        Start sending a file to a contact.

        Args:
            contact_id: Contact database ID
            peer: PeerConnection instance
            file_path: Path to file to send
            resume_offset: Byte offset to resume from

        Returns:
            Transfer ID (UUID)

        Raises:
            ValueError: If max concurrent transfers reached
        """
        # Check concurrency limit
        active_sends = [
            k for k in self._senders.keys() if k[0] == contact_id
        ]
        if len(active_sends) >= self.max_concurrent_per_contact:
            raise ValueError(
                f"Max concurrent transfers ({self.max_concurrent_per_contact}) reached for contact {contact_id}"
            )

        # Create sender
        sender = FileSender(
            peer=peer,
            file_path=file_path,
            resume_offset=resume_offset
        )

        # Set up callbacks
        sender.on_progress = lambda p: self._handle_progress(contact_id, p)
        sender.on_complete = lambda tid: self._handle_complete(contact_id, tid)
        sender.on_error = lambda tid, err: self._handle_error(contact_id, tid, err)

        # Save initial state to database
        from src.file_transfer.chunker import get_file_info, calculate_file_hash
        file_info = await get_file_info(file_path)
        file_hash = await calculate_file_hash(file_path)

        save_transfer_state(
            transfer_id=sender.transfer_id,
            contact_id=contact_id,
            direction=TransferDirection.SEND.value,
            filename=file_info["filename"],
            size=file_info["size"],
            hash_value=file_hash,
            bytes_transferred=resume_offset,
            state=TransferState.PENDING.value
        )

        # Start send task
        task = asyncio.create_task(sender.send())
        self._senders[(contact_id, sender.transfer_id)] = (sender, task)

        logger.info(
            f"Started file send: {file_info['filename']} to contact {contact_id}, transfer_id={sender.transfer_id}"
        )

        return sender.transfer_id

    async def cancel_send(self, contact_id: int, transfer_id: str) -> bool:
        """
        Cancel an outgoing transfer.

        Args:
            contact_id: Contact database ID
            transfer_id: Transfer UUID

        Returns:
            True if cancelled, False if not found
        """
        key = (contact_id, transfer_id)
        if key not in self._senders:
            return False

        sender, task = self._senders[key]
        sender.cancel()

        # Wait for task to complete
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"Send task {transfer_id} did not complete gracefully")

        # Clean up
        del self._senders[key]

        # Update database
        update_transfer_progress(transfer_id, sender._bytes_sent, TransferState.CANCELLED.value)

        logger.info(f"Cancelled file send: transfer_id={transfer_id}")
        return True

    async def handle_incoming_message(
        self,
        contact_id: int,
        peer: "PeerConnection",
        message: bytes
    ) -> None:
        """
        Handle incoming file transfer message from a contact.

        Routes message to appropriate receiver based on type.

        Args:
            contact_id: Contact database ID
            peer: PeerConnection instance
            message: Raw message bytes
        """
        # Check for special markers
        if message == EOF_MARKER:
            await self._handle_eof(contact_id)
            return
        elif message == CANCEL_MARKER:
            await self._handle_cancel(contact_id)
            return
        elif message == ACK_MARKER:
            # Receiver acknowledged - not currently used
            return
        elif message == ERROR_MARKER:
            # Receiver reported error - not currently used
            return

        # Check for metadata (JSON message)
        if message.startswith(b'{'):
            try:
                msg_str = message.decode('utf-8')
                data = json.loads(msg_str)

                if data.get("type") == FileMessageType.METADATA.value:
                    await self._handle_metadata(contact_id, msg_str)
                    return
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass

        # Check for chunk (prefixed with 'C')
        if message.startswith(b'C'):
            chunk_data = message[1:]  # Strip type prefix
            await self._handle_chunk(contact_id, chunk_data)
            return

        logger.warning(f"Unknown file transfer message type from contact {contact_id}")

    async def cancel_receive(self, contact_id: int, transfer_id: str) -> bool:
        """
        Cancel an incoming transfer.

        Args:
            contact_id: Contact database ID
            transfer_id: Transfer UUID

        Returns:
            True if cancelled, False if not found
        """
        key = (contact_id, transfer_id)
        if key not in self._receivers:
            return False

        receiver = self._receivers[key]
        await receiver.cancel()

        # Clean up
        del self._receivers[key]

        # Update database
        update_transfer_progress(
            transfer_id,
            receiver.get_resume_offset(),
            TransferState.CANCELLED.value
        )

        logger.info(f"Cancelled file receive: transfer_id={transfer_id}")
        return True

    def get_resumable_transfers(self, contact_id: int) -> List[dict]:
        """
        Get list of incomplete transfers that can be resumed.

        Args:
            contact_id: Contact database ID

        Returns:
            List of transfer state dictionaries
        """
        return get_pending_transfers(contact_id)

    def get_active_transfers(self, contact_id: int) -> List[TransferProgress]:
        """
        Get list of currently active transfers for a contact.

        Args:
            contact_id: Contact database ID

        Returns:
            List of TransferProgress objects
        """
        progress_list = []

        # Get sending transfers
        for (cid, tid), (sender, _) in self._senders.items():
            if cid == contact_id:
                progress_list.append(sender.progress)

        # Get receiving transfers
        for (cid, tid), receiver in self._receivers.items():
            if cid == contact_id:
                prog = receiver.progress
                if prog:
                    progress_list.append(prog)

        return progress_list

    # Internal message handlers

    async def _handle_metadata(self, contact_id: int, message: str) -> None:
        """Handle incoming file metadata."""
        try:
            data = json.loads(message)
            transfer_id = data["id"]

            # Check concurrency limit
            active_receives = [
                k for k in self._receivers.keys() if k[0] == contact_id
            ]
            if len(active_receives) >= self.max_concurrent_per_contact:
                logger.warning(
                    f"Max concurrent transfers reached for contact {contact_id}, rejecting receive"
                )
                return

            # Create receiver
            receiver = FileReceiver(transfer_id=transfer_id)

            # Set up callbacks
            receiver.on_progress = lambda p: self._handle_progress(contact_id, p)
            receiver.on_complete = lambda fm: self._handle_file_received(contact_id, fm)
            receiver.on_error = lambda tid, err: self._handle_error(contact_id, tid, err)

            # Handle metadata
            success = await receiver.handle_metadata(message)
            if not success:
                return

            # Store receiver
            self._receivers[(contact_id, transfer_id)] = receiver

            # Save initial state to database
            save_transfer_state(
                transfer_id=transfer_id,
                contact_id=contact_id,
                direction=TransferDirection.RECEIVE.value,
                filename=receiver._metadata.filename,
                size=receiver._metadata.size,
                hash_value=receiver._metadata.hash,
                bytes_transferred=0,
                state=TransferState.ACTIVE.value
            )

            logger.info(
                f"Started file receive: {receiver._metadata.filename} from contact {contact_id}"
            )

        except Exception as e:
            logger.error(f"Failed to handle metadata: {e}")

    async def _handle_chunk(self, contact_id: int, chunk: bytes) -> None:
        """Handle incoming file chunk."""
        # Find the active receiver for this contact
        # In a real implementation, we'd track which receiver is active
        # For now, assume one active receive per contact
        for (cid, tid), receiver in self._receivers.items():
            if cid == contact_id and receiver.state == TransferState.ACTIVE:
                await receiver.handle_chunk(chunk)
                return

        logger.warning(f"Received chunk for unknown transfer from contact {contact_id}")

    async def _handle_eof(self, contact_id: int) -> None:
        """Handle incoming EOF marker."""
        # Find the active receiver for this contact
        for (cid, tid), receiver in self._receivers.items():
            if cid == contact_id and receiver.state == TransferState.ACTIVE:
                await receiver.handle_eof()
                # Clean up
                del self._receivers[(cid, tid)]
                return

        logger.warning(f"Received EOF for unknown transfer from contact {contact_id}")

    async def _handle_cancel(self, contact_id: int) -> None:
        """Handle incoming cancel marker."""
        # Find the active receiver for this contact
        for (cid, tid), receiver in self._receivers.items():
            if cid == contact_id and receiver.state == TransferState.ACTIVE:
                await receiver.handle_cancel()
                # Clean up
                del self._receivers[(cid, tid)]
                return

        logger.warning(f"Received cancel for unknown transfer from contact {contact_id}")

    # Callback handlers

    def _handle_progress(self, contact_id: int, progress: TransferProgress) -> None:
        """Handle progress update from sender/receiver."""
        # Update database
        update_transfer_progress(
            progress.transfer_id,
            progress.bytes_transferred,
            progress.state.value
        )

        # Notify frontend
        if self.on_transfer_progress:
            self.on_transfer_progress(contact_id, progress)

    def _handle_complete(self, contact_id: int, transfer_id: str) -> None:
        """Handle transfer completion from sender."""
        # Update database
        state = get_transfer_state(transfer_id)
        if state:
            update_transfer_progress(transfer_id, state["size"], TransferState.COMPLETE.value)

        # Clean up sender
        key = (contact_id, transfer_id)
        if key in self._senders:
            del self._senders[key]

        # Notify frontend
        if self.on_transfer_complete:
            self.on_transfer_complete(contact_id, transfer_id)

        logger.info(f"Transfer complete: {transfer_id}")

    def _handle_file_received(self, contact_id: int, file_meta: FileMetadata) -> None:
        """Handle file reception completion."""
        # Update database
        update_transfer_progress(
            file_meta.transfer_id,
            file_meta.size,
            TransferState.COMPLETE.value
        )

        # Notify frontend
        if self.on_file_received:
            self.on_file_received(contact_id, file_meta)

        logger.info(f"File received: {file_meta.filename}, id={file_meta.id}")

    def _handle_error(self, contact_id: int, transfer_id: str, error: str) -> None:
        """Handle transfer error."""
        # Update database
        state = get_transfer_state(transfer_id)
        if state:
            update_transfer_progress(
                transfer_id,
                state["bytes_transferred"],
                TransferState.FAILED.value
            )

        # Clean up
        key = (contact_id, transfer_id)
        if key in self._senders:
            del self._senders[key]
        if key in self._receivers:
            del self._receivers[key]

        # Notify frontend
        if self.on_transfer_error:
            self.on_transfer_error(contact_id, transfer_id, error)

        logger.error(f"Transfer error: {transfer_id} - {error}")
