"""
Settings key-value storage in SQLCipher database.

Provides persistent storage for user preferences and app configuration.
All values are stored as strings - callers must handle type conversion.
"""

from typing import Optional

from src.storage.db import get_database


class Settings:
    """Known setting keys as constants."""

    USER_STATUS = "user_status"
    """User's presence status (online, away, busy, invisible, offline)."""

    SIGNALING_SERVER_URL = "signaling_server_url"
    """WebSocket URL for signaling server."""

    # Default values
    _defaults = {
        USER_STATUS: "online",
        SIGNALING_SERVER_URL: "ws://localhost:8765",  # Local dev server
    }

    @classmethod
    def get_default(cls, key: str) -> Optional[str]:
        """Get default value for a setting key."""
        return cls._defaults.get(key)


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a setting value.

    Args:
        key: Setting key
        default: Default value if setting not found (takes precedence over
                 Settings class defaults)

    Returns:
        Setting value, or default if not found
    """
    db = get_database()
    row = db.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,)
    ).fetchone()

    if row is not None:
        return row[0]

    # Check class defaults if no explicit default provided
    if default is None:
        return Settings.get_default(key)

    return default


def set_setting(key: str, value: str) -> None:
    """
    Set a setting value.

    Uses INSERT OR REPLACE to handle both new and existing settings.

    Args:
        key: Setting key
        value: Setting value (must be string)
    """
    db = get_database()
    db.execute(
        """
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
        (key, value)
    )
    db.commit()


def get_all_settings() -> dict[str, str]:
    """
    Get all settings as a dictionary.

    Returns:
        Dict mapping setting keys to values
    """
    db = get_database()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    return {row[0]: row[1] for row in rows}


def delete_setting(key: str) -> None:
    """
    Delete a setting.

    Args:
        key: Setting key to remove
    """
    db = get_database()
    db.execute("DELETE FROM settings WHERE key = ?", (key,))
    db.commit()
