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

# Database operations
from src.storage.db import init_database, get_database, close_database

# Identity storage
from src.storage.identity_store import (
    has_identity,
    save_identity,
    load_identity,
    update_display_name,
    get_or_create_identity,
)

# Contact storage
from src.storage.contacts import (
    get_contacts,
    get_contact,
    add_contact,
    remove_contact,
    set_contact_verified,
    update_contact_display_name,
    Contact,
)

# Settings storage
from src.storage.settings import (
    Settings,
    get_setting,
    set_setting,
    get_all_settings,
    delete_setting,
)

# Message storage
from src.storage.messages import (
    Message,
    Reaction,
    save_message,
    get_messages,
    get_message,
    update_message,
    delete_message,
    add_reaction,
    remove_reaction,
    get_reactions,
    save_signal_session,
    get_signal_session,
    delete_signal_session,
)

__all__ = [
    # Paths
    'get_app_data_dir',
    'get_db_path',
    'get_key_path',
    'get_identity_key_path',
    # DPAPI
    'dpapi_encrypt',
    'dpapi_decrypt',
    # Database
    'init_database',
    'get_database',
    'close_database',
    # Identity storage
    'has_identity',
    'save_identity',
    'load_identity',
    'update_display_name',
    'get_or_create_identity',
    # Contact storage
    'get_contacts',
    'get_contact',
    'add_contact',
    'remove_contact',
    'set_contact_verified',
    'update_contact_display_name',
    'Contact',
    # Settings storage
    'Settings',
    'get_setting',
    'set_setting',
    'get_all_settings',
    'delete_setting',
    # Message storage
    'Message',
    'Reaction',
    'save_message',
    'get_messages',
    'get_message',
    'update_message',
    'delete_message',
    'add_reaction',
    'remove_reaction',
    'get_reactions',
    'save_signal_session',
    'get_signal_session',
    'delete_signal_session',
]
