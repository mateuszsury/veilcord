"""
Async file chunking for transfer over WebRTC data channels.

Reads files in fixed-size chunks without loading entire file into memory.
Calculates SHA256 hash during reading for verification.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import AsyncIterator, Tuple, Optional
import aiofiles

from src.file_transfer.protocol import CHUNK_SIZE


async def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of file without loading into memory.

    Args:
        file_path: Path to file

    Returns:
        Hex-encoded SHA256 hash
    """
    sha256 = hashlib.sha256()
    async with aiofiles.open(file_path, 'rb') as fp:
        while True:
            chunk = await fp.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


async def chunk_file(
    file_path: Path,
    chunk_size: int = CHUNK_SIZE,
    start_offset: int = 0
) -> AsyncIterator[Tuple[int, bytes, bool]]:
    """
    Async generator yielding file chunks.

    Args:
        file_path: Path to file
        chunk_size: Size of each chunk in bytes
        start_offset: Byte offset to start from (for resume)

    Yields:
        Tuple of (offset, chunk_data, is_last)
    """
    file_size = file_path.stat().st_size
    offset = start_offset

    async with aiofiles.open(file_path, 'rb') as fp:
        if start_offset > 0:
            await fp.seek(start_offset)

        while True:
            chunk = await fp.read(chunk_size)
            if not chunk:
                break

            is_last = (offset + len(chunk)) >= file_size
            yield (offset, chunk, is_last)
            offset += len(chunk)


async def get_file_info(file_path: Path) -> dict:
    """
    Get file metadata for transfer.

    Returns:
        Dict with filename, size, mime_type
    """
    import mimetypes

    stat = file_path.stat()
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    return {
        "filename": file_path.name,
        "size": stat.st_size,
        "mime_type": mime_type
    }
