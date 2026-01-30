"""
Data classes for file transfer protocol.

Models for file transfer metadata, progress tracking, and chunked transfer.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TransferState(Enum):
    """File transfer state."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TransferDirection(Enum):
    """File transfer direction."""
    SEND = "send"
    RECEIVE = "receive"


@dataclass
class FileTransferMetadata:
    """Metadata sent before file chunks."""
    id: str  # Transfer UUID
    filename: str
    size: int  # Total bytes
    hash: str  # SHA256 hex
    mime_type: str


@dataclass
class TransferProgress:
    """Current transfer progress."""
    transfer_id: str
    bytes_transferred: int
    total_bytes: int
    state: TransferState
    speed_bps: float = 0.0  # Bytes per second
    eta_seconds: float = 0.0


@dataclass
class FileChunk:
    """A single chunk of file data."""
    transfer_id: str
    offset: int  # Byte offset in file
    data: bytes
    is_last: bool = False
