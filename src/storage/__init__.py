"""
Storage module for DiscordOpus.

This module provides secure local storage using:
- Windows DPAPI for key encryption (keys tied to Windows user account)
- SQLCipher for database encryption (256-bit AES)

All sensitive data is encrypted at rest. No plaintext secrets on disk.
"""

# Path utilities
from src.storage.paths import (
    get_app_data_dir,
    get_db_path,
    get_key_path,
    get_identity_key_path,
)

# DPAPI encryption
from src.storage.dpapi import dpapi_encrypt, dpapi_decrypt

# Database operations (available after Task 3)
# from src.storage.db import init_database, get_database

__all__ = [
    # Paths
    'get_app_data_dir',
    'get_db_path',
    'get_key_path',
    'get_identity_key_path',
    # DPAPI
    'dpapi_encrypt',
    'dpapi_decrypt',
    # Database (uncomment after Task 3)
    # 'init_database',
    # 'get_database',
]
