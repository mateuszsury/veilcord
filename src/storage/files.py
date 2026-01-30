"""
Encrypted file storage with hybrid BLOB/filesystem strategy.

Small files (<100KB): Stored as BLOBs in SQLCipher database
Large files (>=100KB): Stored encrypted on filesystem, path in database

Uses Fernet (AES-128-CBC) for filesystem encryption. SQLCipher provides
database-level encryption, so BLOBs don't need additional encryption.
"""

import os
import hashlib
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

from src.storage.db import get_database
from src.storage.paths import get_data_dir

# Threshold for BLOB vs filesystem storage
BLOB_THRESHOLD = 102400  # 100KB


@dataclass
class FileMetadata:
    """File record from database."""
    id: int
    filename: str
    mime_type: str
    size: int
    hash: str
    created_at: int
    transfer_id: Optional[str]


class FileStorage:
    """Encrypted file storage manager."""

    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Args:
            encryption_key: 32-byte key for Fernet. If None, generates new key.
                           In production, derive from master key via DPAPI.
        """
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
        self._cipher = Fernet(encryption_key)
        self._storage_dir = get_data_dir() / "files"
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        data: bytes,
        filename: str,
        transfer_id: Optional[str] = None
    ) -> FileMetadata:
        """
        Save file with automatic BLOB/filesystem routing.

        Args:
            data: File content bytes
            filename: Original filename
            transfer_id: Optional link to file_transfers record

        Returns:
            FileMetadata with database ID
        """
        conn = get_database()

        file_hash = hashlib.sha256(data).hexdigest()
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        size = len(data)
        created_at = int(time.time() * 1000)

        if size < BLOB_THRESHOLD:
            # Small file: store in database BLOB
            cursor = conn.execute("""
                INSERT INTO files (filename, mime_type, size, hash, data, created_at, transfer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (filename, mime_type, size, file_hash, data, created_at, transfer_id))
        else:
            # Large file: encrypt and store on filesystem
            file_id = hashlib.sha256(f"{filename}{time.time()}{os.urandom(16).hex()}".encode()).hexdigest()[:16]
            file_path = self._storage_dir / f"{file_id}.enc"

            encrypted_data = self._cipher.encrypt(data)
            file_path.write_bytes(encrypted_data)

            cursor = conn.execute("""
                INSERT INTO files (filename, mime_type, size, hash, file_path, created_at, transfer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (filename, mime_type, size, file_hash, str(file_path), created_at, transfer_id))

        conn.commit()

        return FileMetadata(
            id=cursor.lastrowid,
            filename=filename,
            mime_type=mime_type,
            size=size,
            hash=file_hash,
            created_at=created_at,
            transfer_id=transfer_id
        )

    def get_file(self, file_id: int) -> Optional[tuple[FileMetadata, bytes]]:
        """
        Retrieve file by database ID.

        Returns:
            Tuple of (metadata, data) or None if not found
        """
        conn = get_database()
        row = conn.execute("""
            SELECT id, filename, mime_type, size, hash, data, file_path, created_at, transfer_id
            FROM files WHERE id = ?
        """, (file_id,)).fetchone()

        if not row:
            return None

        metadata = FileMetadata(
            id=row[0],
            filename=row[1],
            mime_type=row[2],
            size=row[3],
            hash=row[4],
            created_at=row[7],
            transfer_id=row[8]
        )

        if row[5]:  # BLOB data
            data = row[5]
        elif row[6]:  # Filesystem path
            file_path = Path(row[6])
            if file_path.exists():
                encrypted_data = file_path.read_bytes()
                data = self._cipher.decrypt(encrypted_data)
            else:
                return None
        else:
            return None

        return (metadata, data)

    def get_metadata(self, file_id: int) -> Optional[FileMetadata]:
        """Get file metadata without loading content."""
        conn = get_database()
        row = conn.execute("""
            SELECT id, filename, mime_type, size, hash, created_at, transfer_id
            FROM files WHERE id = ?
        """, (file_id,)).fetchone()

        if not row:
            return None

        return FileMetadata(
            id=row[0],
            filename=row[1],
            mime_type=row[2],
            size=row[3],
            hash=row[4],
            created_at=row[5],
            transfer_id=row[6]
        )

    def delete_file(self, file_id: int) -> bool:
        """
        Delete file from database and filesystem.

        Returns:
            True if deleted, False if not found
        """
        conn = get_database()

        # Get file path first
        row = conn.execute("SELECT file_path FROM files WHERE id = ?", (file_id,)).fetchone()
        if not row:
            return False

        # Delete from filesystem if applicable
        if row[0]:
            file_path = Path(row[0])
            if file_path.exists():
                file_path.unlink()

        # Delete from database
        cursor = conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()

        return cursor.rowcount > 0


# Module-level convenience functions
_storage: Optional[FileStorage] = None


def get_file_storage(encryption_key: Optional[bytes] = None) -> FileStorage:
    """Get or create singleton FileStorage instance."""
    global _storage
    if _storage is None:
        _storage = FileStorage(encryption_key)
    return _storage


def save_file(data: bytes, filename: str, transfer_id: Optional[str] = None) -> FileMetadata:
    """Save file using singleton storage."""
    return get_file_storage().save_file(data, filename, transfer_id)


def get_file(file_id: int) -> Optional[tuple[FileMetadata, bytes]]:
    """Get file using singleton storage."""
    return get_file_storage().get_file(file_id)


def delete_file(file_id: int) -> bool:
    """Delete file using singleton storage."""
    return get_file_storage().delete_file(file_id)
