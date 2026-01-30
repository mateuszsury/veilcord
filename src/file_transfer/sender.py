"""
File transfer sender with backpressure control.

Sends files over WebRTC data channel respecting buffer limits.
Uses event-driven chunk sending triggered by bufferedAmountLow.

IMPORTANT: This expects a PeerConnection object with a `data_channel` attribute
that is an aiortc RTCDataChannel. The RTCDataChannel has a `bufferedAmount`
property that tracks bytes queued for sending.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from src.file_transfer.protocol import (
    CHUNK_SIZE,
    BUFFER_THRESHOLD,
    EOF_MARKER,
    CANCEL_MARKER,
    FileMessageType
)
from src.file_transfer.chunker import chunk_file, calculate_file_hash, get_file_info
from src.file_transfer.models import TransferState, TransferProgress, FileTransferMetadata

logger = logging.getLogger(__name__)


@dataclass
class FileSender:
    """
    Sends a file over a data channel with backpressure control.

    Usage:
        sender = FileSender(peer_connection, file_path)
        sender.on_progress = lambda p: print(f"{p.bytes_transferred}/{p.total_bytes}")
        await sender.send()

    Args:
        peer: PeerConnection instance (from src/network/peer_connection.py)
              Must have `data_channel` attribute (RTCDataChannel from aiortc)
    """
    peer: "PeerConnection"  # Forward reference to src/network/peer_connection.PeerConnection
    file_path: Path
    transfer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resume_offset: int = 0

    # State
    _state: TransferState = field(default=TransferState.PENDING, init=False)
    _bytes_sent: int = field(default=0, init=False)
    _total_bytes: int = field(default=0, init=False)
    _file_hash: str = field(default="", init=False)
    _start_time: float = field(default=0.0, init=False)
    _cancelled: bool = field(default=False, init=False)
    _send_event: asyncio.Event = field(default_factory=asyncio.Event, init=False)

    # Callbacks
    on_progress: Optional[Callable[[TransferProgress], None]] = None
    on_complete: Optional[Callable[[str], None]] = None
    on_error: Optional[Callable[[str, str], None]] = None

    def __post_init__(self):
        self.file_path = Path(self.file_path)
        self._send_event.set()  # Start ready to send

    @property
    def state(self) -> TransferState:
        return self._state

    @property
    def progress(self) -> TransferProgress:
        elapsed = time.time() - self._start_time if self._start_time else 0
        speed = self._bytes_sent / elapsed if elapsed > 0 else 0
        remaining = self._total_bytes - self._bytes_sent
        eta = remaining / speed if speed > 0 else 0

        return TransferProgress(
            transfer_id=self.transfer_id,
            bytes_transferred=self._bytes_sent,
            total_bytes=self._total_bytes,
            state=self._state,
            speed_bps=speed,
            eta_seconds=eta
        )

    async def send(self) -> bool:
        """
        Send the file with backpressure control.

        Returns:
            True if completed successfully, False if cancelled/failed
        """
        try:
            self._state = TransferState.ACTIVE
            self._start_time = time.time()
            self._bytes_sent = self.resume_offset

            # Calculate hash and get info
            logger.info(f"Starting file transfer: {self.file_path.name}")
            self._file_hash = await calculate_file_hash(self.file_path)
            file_info = await get_file_info(self.file_path)
            self._total_bytes = file_info["size"]

            # Send metadata
            metadata = FileTransferMetadata(
                id=self.transfer_id,
                filename=file_info["filename"],
                size=file_info["size"],
                hash=self._file_hash,
                mime_type=file_info["mime_type"]
            )
            await self._send_metadata(metadata)

            # Send chunks with backpressure
            async for offset, chunk, is_last in chunk_file(
                self.file_path,
                CHUNK_SIZE,
                self.resume_offset
            ):
                if self._cancelled:
                    await self._send_cancel()
                    self._state = TransferState.CANCELLED
                    return False

                # Wait for buffer to drain if needed
                await self._wait_for_buffer()

                # Send chunk
                self._send_chunk(chunk)
                self._bytes_sent = offset + len(chunk)

                # Report progress
                self._report_progress()

            # Send EOF
            self._send_eof()
            self._state = TransferState.COMPLETE

            if self.on_complete:
                self.on_complete(self.transfer_id)

            logger.info(f"File transfer complete: {self.file_path.name}")
            return True

        except asyncio.CancelledError:
            await self._send_cancel()
            self._state = TransferState.CANCELLED
            raise

        except Exception as e:
            logger.error(f"File transfer failed: {e}")
            self._state = TransferState.FAILED
            if self.on_error:
                self.on_error(self.transfer_id, str(e))
            return False

    def cancel(self) -> None:
        """Request cancellation of the transfer."""
        self._cancelled = True
        self._send_event.set()  # Wake up any waiting send

    async def _wait_for_buffer(self) -> None:
        """
        Wait until buffer has capacity for more data.

        Uses peer.data_channel.bufferedAmount from aiortc RTCDataChannel.
        This property tracks bytes queued for transmission.
        When it exceeds BUFFER_THRESHOLD (64KB), we pause and poll until it drains.
        """
        # Access the data_channel from PeerConnection
        # PeerConnection.data_channel is RTCDataChannel from aiortc
        data_channel = getattr(self.peer, 'data_channel', None)

        if not data_channel:
            return  # No channel, proceed (will fail on send)

        while data_channel.bufferedAmount > BUFFER_THRESHOLD:
            # Wait a bit for buffer to drain
            # aiortc doesn't expose bufferedAmountLow event, so we poll
            await asyncio.sleep(0.01)

            if self._cancelled:
                return

    def _send_chunk(self, chunk: bytes) -> None:
        """Send a data chunk over the channel."""
        # Prefix with message type byte for receiver routing
        message = bytes([ord('C')]) + chunk  # 'C' for Chunk
        self.peer.send(message)

    def _send_eof(self) -> None:
        """Send end-of-file marker."""
        self.peer.send(EOF_MARKER)

    async def _send_cancel(self) -> None:
        """Send cancellation marker."""
        self.peer.send(CANCEL_MARKER)

    async def _send_metadata(self, metadata: FileTransferMetadata) -> None:
        """Send file metadata as JSON."""
        msg = {
            "type": FileMessageType.METADATA.value,
            "id": metadata.id,
            "filename": metadata.filename,
            "size": metadata.size,
            "hash": metadata.hash,
            "mime_type": metadata.mime_type
        }
        self.peer.send(json.dumps(msg))

    def _report_progress(self) -> None:
        """Report current progress via callback."""
        if self.on_progress:
            self.on_progress(self.progress)
