"""
File transfer wire protocol constants.

Protocol flow:
1. Sender sends METADATA message with file info
2. Sender sends DATA chunks until complete
3. Sender sends EOF marker
4. Receiver verifies hash and sends ACK or ERROR

Messages are JSON for metadata, binary for chunks.
"""

from enum import Enum

# Chunk size for WebRTC compatibility (16KB)
# aiortc can handle 64KB but browsers fragment at 16KB
CHUNK_SIZE = 16384

# Buffer threshold for backpressure (64KB)
BUFFER_THRESHOLD = 65536

# Special markers
EOF_MARKER = b"__FILE_EOF__"
CANCEL_MARKER = b"__FILE_CANCELLED__"
ACK_MARKER = b"__FILE_ACK__"
ERROR_MARKER = b"__FILE_ERROR__"


class FileMessageType(Enum):
    """Types of file transfer messages."""
    METADATA = "file_metadata"  # JSON with filename, size, hash
    CHUNK = "file_chunk"  # Binary data chunk
    EOF = "file_eof"  # End of file
    CANCEL = "file_cancel"  # Cancel transfer
    ACK = "file_ack"  # Acknowledgment
    ERROR = "file_error"  # Error message
    PROGRESS_REQUEST = "file_progress"  # Request resume position
    RESUME = "file_resume"  # Resume from offset
