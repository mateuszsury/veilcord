---
phase: 04-file-transfer
plan: 01
subsystem: storage
status: complete
tags: [storage, encryption, database, file-transfer]

dependency_graph:
  requires:
    - 01-02: SQLCipher database with DPAPI encryption
    - 01-03: Cryptographic identity (for future E2E encryption)
  provides:
    - Encrypted file storage with hybrid BLOB/filesystem strategy
    - File metadata tracking in SQLCipher database
    - Transfer state persistence
    - Data models for file transfer protocol
  affects:
    - 04-02: File transfer protocol will use FileStorage for persistence
    - 04-03: Chunking service will reference transfer state models
    - Future phases: Any feature needing file attachment storage

tech_stack:
  added:
    - cryptography.fernet: AES-128-CBC encryption for filesystem files
    - mimetypes: MIME type detection
  patterns:
    - Hybrid storage: <100KB in database BLOB, >=100KB encrypted on filesystem
    - Singleton pattern: Module-level get_file_storage() for shared instance
    - Database schema extension: files and file_transfers tables

key_files:
  created:
    - src/storage/files.py: FileStorage class with save/get/delete operations
    - src/file_transfer/__init__.py: Package marker
    - src/file_transfer/models.py: Transfer protocol data classes
  modified:
    - src/storage/db.py: Added files and file_transfers tables
    - src/storage/paths.py: Added get_data_dir() helper

decisions:
  - slug: hybrid-storage-threshold
    title: 100KB threshold for BLOB vs filesystem storage
    rationale: Research (04-RESEARCH.md) recommends 100KB as optimal balance between database size and filesystem overhead
    impact: Small files benefit from database transactionality, large files avoid database bloat
  - slug: fernet-for-filesystem
    title: Use Fernet (AES-128-CBC) for filesystem encryption
    rationale: SQLCipher already encrypts BLOBs, only filesystem files need additional encryption; Fernet provides authenticated encryption
    impact: Defense-in-depth for large files on disk
  - slug: transfer-state-enum
    title: TransferState enum with 6 states
    rationale: Comprehensive state tracking (pending, active, paused, complete, cancelled, failed) enables resume and error handling
    impact: Future plans can implement pause/resume and failure recovery

metrics:
  duration: "3 minutes"
  tasks: 2
  commits: 2
  files_created: 3
  files_modified: 2
  completed: 2026-01-30
---

# Phase 4 Plan 01: File Storage Infrastructure Summary

**One-liner:** Encrypted at-rest file storage with hybrid BLOB/filesystem strategy using SQLCipher and Fernet.

## What Was Built

Created secure file storage infrastructure for P2P file transfers:

1. **Database Schema Extensions:**
   - `files` table: Stores file metadata with either BLOB data (small files) or filesystem path (large files)
   - `file_transfers` table: Tracks transfer state, progress, and metadata for ongoing transfers

2. **FileStorage Class:**
   - Hybrid storage: Files <100KB stored as BLOBs in SQLCipher, >=100KB encrypted with Fernet on filesystem
   - Operations: `save_file()`, `get_file()`, `delete_file()`, `get_metadata()`
   - Automatic MIME type detection and SHA256 hash verification
   - Singleton pattern with module-level convenience functions

3. **Transfer Protocol Models:**
   - `TransferState` enum: pending, active, paused, complete, cancelled, failed
   - `TransferDirection` enum: send, receive
   - `FileTransferMetadata`: Metadata exchanged before transfer
   - `TransferProgress`: Real-time progress tracking with speed and ETA
   - `FileChunk`: Individual chunk representation for chunked transfers

## Success Criteria Met

- [x] Database has files and file_transfers tables
- [x] TransferState enum has all required states
- [x] FileTransferMetadata, TransferProgress, FileChunk dataclasses work
- [x] FileStorage saves small files as BLOBs
- [x] FileStorage saves large files encrypted on filesystem
- [x] Files can be retrieved and decrypted correctly

## Technical Details

**Encryption Strategy:**
- Small files (<100KB): Stored in SQLCipher database as BLOBs (database-level encryption, no double encryption)
- Large files (>=100KB): Encrypted with Fernet (AES-128-CBC with HMAC) before writing to `%APPDATA%/DiscordOpus/files/`
- Each FileStorage instance has its own Fernet key (in production, will derive from master key via DPAPI)

**Hash Verification:**
- SHA256 hash calculated during save
- Stored in database for integrity verification
- Can be verified against received file hash from peer

**Storage Layout:**
```
%APPDATA%/DiscordOpus/
├── data.db              (SQLCipher database)
│   └── files table      (metadata + small file BLOBs)
└── files/               (encrypted large files)
    └── {file_id}.enc    (Fernet-encrypted file data)
```

## Files Changed

**Created:**
- `src/storage/files.py` (221 lines): FileStorage class and convenience functions
- `src/file_transfer/__init__.py` (3 lines): Package marker
- `src/file_transfer/models.py` (55 lines): Transfer protocol data classes

**Modified:**
- `src/storage/db.py`: Added files and file_transfers table schema
- `src/storage/paths.py`: Added get_data_dir() helper function

## Deviations from Plan

None - plan executed exactly as written.

## Testing Performed

**Manual verification tests:**
1. Small file storage (13 bytes): Verified BLOB storage and retrieval
2. Large file storage (150KB): Verified filesystem encryption and decryption
3. Database schema: Verified tables created with correct structure
4. Data models: Verified all enums and dataclasses importable

**All tests passed.**

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| 100KB threshold for BLOB/filesystem split | Research recommends this as optimal balance | Small files in DB, large files on filesystem |
| Fernet for filesystem encryption | Authenticated encryption (AES + HMAC), simple API | Defense-in-depth for large files |
| No double encryption for BLOBs | SQLCipher already encrypts database | Better performance, same security |
| Singleton FileStorage instance | Matches pattern from existing modules (db.py, identity_store.py) | Consistent codebase patterns |
| SHA256 hash in metadata | Standard cryptographic hash for integrity | Can verify against peer's hash |

## Next Phase Readiness

**Blockers:** None

**Prerequisites for next plan (04-02 - File Transfer Protocol):**
- [x] File storage layer available
- [x] Transfer state models defined
- [x] Database schema ready

**Concerns:** None

**What's working well:**
- Hybrid storage strategy minimizes database bloat while maintaining transactionality for small files
- Fernet provides simple, audited encryption for filesystem files
- Transfer state models are comprehensive enough for pause/resume/cancel

## Integration Points

**Upstream dependencies:**
- `src.storage.db.get_database()`: For SQLCipher connection
- `src.storage.paths.get_data_dir()`: For filesystem storage location
- `cryptography.fernet.Fernet`: For large file encryption

**Downstream consumers (future plans):**
- 04-02 (File Transfer Protocol): Will use save_file() and get_file() for transferred files
- 04-03 (Chunking Service): Will use FileChunk model and TransferProgress tracking
- 04-04+ (UI integration): Will query file_transfers table for progress display

**API surface:**
```python
# Module-level convenience functions
from src.storage.files import save_file, get_file, delete_file

# Direct class usage (for custom encryption key)
from src.storage.files import FileStorage, get_file_storage

# Transfer protocol models
from src.file_transfer.models import (
    TransferState,
    TransferDirection,
    FileTransferMetadata,
    TransferProgress,
    FileChunk
)
```

## Commits

1. `e49fbac` - feat(04-01): extend database schema for file storage and transfers
2. `5f8337b` - feat(04-01): create FileStorage class with encryption

**Total duration:** 3 minutes

---

*Summary created: 2026-01-30*
*Plan status: Complete*
