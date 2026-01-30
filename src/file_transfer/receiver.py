"""
File transfer receiver with chunk reassembly and hash verification.

Receives files over WebRTC data channel, assembles chunks into temp file,
verifies hash, then saves to encrypted storage.

IMPORTANT: Uses aiofiles for non-blocking I/O to prevent event loop stalling.
Chunks are written directly to disk - not held in memory.
"""

import asyncio
import hashlib
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

import aiofiles

from src.file_transfer.protocol import (
    EOF_MARKER,
    CANCEL_MARKER,
    FileMessageType
)
from src.file_transfer.models import (
    FileTransferMetadata,
    TransferState,
    TransferProgress
)
from src.storage.files import save_file, FileMetadata

logger = logging.getLogger(__name__)


@dataclass
class FileReceiver:
    """
    Receives a file over a data channel with hash verification.

    Usage:
        receiver = FileReceiver(transfer_id="some-uuid")
        receiver.on_progress = lambda p: print(f"{p.bytes_transferred}/{p.total_bytes}")

        # Process incoming messages
        await receiver.handle_metadata(metadata_json)
        await receiver.handle_chunk(chunk_bytes)
        result = await receiver.handle_eof()

        if result:
            print(f"File saved: {result.filename}")

    Flow:
    1. handle_metadata() - Parse metadata, open temp file, start hash
    2. handle_chunk() - Write chunks to temp file, update hash
    3. handle_eof() - Verify hash, save to encrypted storage
    """
    transfer_id: str

    # State
    _state: TransferState = field(default=TransferState.PENDING, init=False)
    _metadata: Optional[FileTransferMetadata] = field(default=None, init=False)
    _temp_file: Optional[Path] = field(default=None, init=False)
    _temp_fd: Optional[object] = field(default=None, init=False)  # aiofiles file handle
    _hasher: object = field(default_factory=lambda: hashlib.sha256(), init=False)
    _bytes_received: int = field(default=0, init=False)
    _start_time: float = field(default=0.0, init=False)
    _cancelled: bool = field(default=False, init=False)

    # Callbacks
    on_progress: Optional[Callable[[TransferProgress], None]] = None
    on_complete: Optional[Callable[[FileMetadata], None]] = None
    on_error: Optional[Callable[[str, str], None]] = None

    @property
    def state(self) -> TransferState:
        return self._state

    @property
    def progress(self) -> Optional[TransferProgress]:
        """Get current transfer progress."""
        if not self._metadata:
            return None

        elapsed = time.time() - self._start_time if self._start_time else 0
        speed = self._bytes_received / elapsed if elapsed > 0 else 0
        remaining = self._metadata.size - self._bytes_received
        eta = remaining / speed if speed > 0 else 0

        return TransferProgress(
            transfer_id=self.transfer_id,
            bytes_transferred=self._bytes_received,
            total_bytes=self._metadata.size,
            state=self._state,
            speed_bps=speed,
            eta_seconds=eta
        )

    async def handle_metadata(self, message: str) -> bool:
        """
        Parse incoming metadata JSON and initialize reception.

        Args:
            message: JSON string with file metadata

        Returns:
            True if metadata parsed successfully

        Raises:
            ValueError: If metadata is invalid
        """
        try:
            data = json.loads(message)

            # Validate message type
            if data.get("type") != FileMessageType.METADATA.value:
                raise ValueError(f"Invalid message type: {data.get('type')}")

            # Parse metadata
            self._metadata = FileTransferMetadata(
                id=data["id"],
                filename=data["filename"],
                size=data["size"],
                hash=data["hash"],
                mime_type=data["mime_type"]
            )

            # Create temp file for reception
            # Use mkstemp to get a secure temp file with proper permissions
            fd, temp_path = tempfile.mkstemp(suffix=".tmp", prefix="ft_")
            os.close(fd)  # Close OS-level fd, we'll use aiofiles
            self._temp_file = Path(temp_path)

            # Open with aiofiles for async I/O
            self._temp_fd = await aiofiles.open(self._temp_file, mode='wb')

            self._state = TransferState.ACTIVE
            self._start_time = time.time()

            logger.info(f"Starting file reception: {self._metadata.filename} ({self._metadata.size} bytes)")
            return True

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse metadata: {e}")
            self._state = TransferState.FAILED
            if self.on_error:
                self.on_error(self.transfer_id, f"Invalid metadata: {e}")
            return False

    async def handle_chunk(self, chunk: bytes) -> None:
        """
        Process incoming chunk - write to temp file and update hash.

        Args:
            chunk: Raw chunk bytes (already stripped of type prefix)

        Raises:
            RuntimeError: If called before metadata received
        """
        if not self._metadata or not self._temp_fd:
            raise RuntimeError("Cannot handle chunk before metadata")

        if self._cancelled:
            return

        # Write chunk to temp file (async I/O)
        await self._temp_fd.write(chunk)

        # Update hash
        self._hasher.update(chunk)

        # Update progress
        self._bytes_received += len(chunk)

        # Report progress
        self._report_progress()

    async def handle_eof(self) -> Optional[FileMetadata]:
        """
        Handle end-of-file marker, verify hash, save to storage.

        Returns:
            FileMetadata if successful, None if failed

        Raises:
            RuntimeError: If called before metadata received
        """
        if not self._metadata or not self._temp_fd:
            raise RuntimeError("Cannot handle EOF before metadata")

        try:
            # Close temp file
            await self._temp_fd.close()
            self._temp_fd = None

            # Verify hash
            calculated_hash = self._hasher.hexdigest()
            if calculated_hash != self._metadata.hash:
                logger.error(
                    f"Hash mismatch! Expected {self._metadata.hash}, got {calculated_hash}"
                )
                self._state = TransferState.FAILED
                if self.on_error:
                    self.on_error(
                        self.transfer_id,
                        f"Hash verification failed: {calculated_hash} != {self._metadata.hash}"
                    )
                return None

            # Read complete file from temp
            async with aiofiles.open(self._temp_file, mode='rb') as f:
                file_data = await f.read()

            # Save to encrypted storage
            file_metadata = save_file(
                data=file_data,
                filename=self._metadata.filename,
                transfer_id=self.transfer_id
            )

            # Clean up temp file
            self._temp_file.unlink()
            self._temp_file = None

            self._state = TransferState.COMPLETE

            if self.on_complete:
                self.on_complete(file_metadata)

            logger.info(f"File reception complete: {self._metadata.filename}")
            return file_metadata

        except Exception as e:
            logger.error(f"Failed to finalize file reception: {e}")
            self._state = TransferState.FAILED
            if self.on_error:
                self.on_error(self.transfer_id, str(e))
            return None
        finally:
            # Ensure cleanup
            await self._cleanup()

    async def handle_cancel(self) -> None:
        """Handle sender-side cancellation."""
        logger.info(f"File transfer cancelled by sender: {self.transfer_id}")
        self._cancelled = True
        self._state = TransferState.CANCELLED
        await self._cleanup()

    async def cancel(self) -> None:
        """Cancel reception from receiver side."""
        logger.info(f"Cancelling file reception: {self.transfer_id}")
        self._cancelled = True
        self._state = TransferState.CANCELLED
        await self._cleanup()

    def get_resume_offset(self) -> int:
        """
        Get current byte offset for resume capability.

        Returns:
            Number of bytes successfully received
        """
        return self._bytes_received

    async def _cleanup(self) -> None:
        """Clean up temp file and handles."""
        try:
            if self._temp_fd:
                await self._temp_fd.close()
                self._temp_fd = None

            if self._temp_file and self._temp_file.exists():
                self._temp_file.unlink()
                self._temp_file = None
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def _report_progress(self) -> None:
        """Report current progress via callback."""
        if self.on_progress:
            progress = self.progress
            if progress:
                self.on_progress(progress)
