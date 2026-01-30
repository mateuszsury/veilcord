"""File transfer module for P2P file sharing."""

from src.file_transfer.models import (
    TransferState,
    TransferDirection,
    FileTransferMetadata,
    TransferProgress,
    FileChunk
)
from src.file_transfer.protocol import (
    CHUNK_SIZE,
    BUFFER_THRESHOLD,
    EOF_MARKER,
    CANCEL_MARKER,
    FileMessageType
)
from src.file_transfer.chunker import (
    chunk_file,
    calculate_file_hash,
    get_file_info
)
from src.file_transfer.sender import FileSender

__all__ = [
    # Models
    "TransferState",
    "TransferDirection",
    "FileTransferMetadata",
    "TransferProgress",
    "FileChunk",
    # Protocol
    "CHUNK_SIZE",
    "BUFFER_THRESHOLD",
    "EOF_MARKER",
    "CANCEL_MARKER",
    "FileMessageType",
    # Chunker
    "chunk_file",
    "calculate_file_hash",
    "get_file_info",
    # Sender
    "FileSender",
]
