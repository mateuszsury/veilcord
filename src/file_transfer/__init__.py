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
from src.file_transfer.receiver import FileReceiver
from src.file_transfer.service import FileTransferService

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
    # Receiver
    "FileReceiver",
    # Service
    "FileTransferService",
]
