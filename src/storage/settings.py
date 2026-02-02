"""
Settings key-value storage in SQLCipher database.

Provides persistent storage for user preferences and app configuration.
All values are stored as strings - callers must handle type conversion.
"""

import json
from typing import Optional, Tuple, List

from src.storage.db import get_database


class Settings:
    """Known setting keys as constants."""

    USER_STATUS = "user_status"
    """User's presence status (online, away, busy, invisible, offline)."""

    SIGNALING_SERVER_URL = "signaling_server_url"
    """WebSocket URL for signaling server."""

    NOTIFICATIONS_ENABLED = "notifications_enabled"
    """Whether Windows notifications are enabled."""

    NOTIFICATIONS_MESSAGES = "notifications_messages"
    """Whether to show notifications for new messages."""

    NOTIFICATIONS_CALLS = "notifications_calls"
    """Whether to show notifications for incoming calls."""

    DISCOVERY_ENABLED = "discovery_enabled"
    """Whether this user is discoverable by others."""

    # Effect settings
    EFFECTS_ACTIVE_PRESET = "effects_active_preset"
    """Name of currently active effect preset."""

    EFFECTS_FAVORITE_PRESETS = "effects_favorite_presets"
    """JSON list of favorite preset names for quick access."""

    EFFECTS_AUDIO_ENABLED = "effects_audio_enabled"
    """Whether audio effects are currently enabled."""

    EFFECTS_VIDEO_ENABLED = "effects_video_enabled"
    """Whether video effects are currently enabled."""

    EFFECTS_SHOW_RESOURCE_MONITOR = "effects_show_resource_monitor"
    """Whether to show resource usage monitor."""

    EFFECTS_QUALITY_OVERRIDE = "effects_quality_override"
    """Quality override setting (low, medium, high, ultra, or null for auto)."""

    # Default values
    _defaults = {
        USER_STATUS: "online",
        SIGNALING_SERVER_URL: "ws://localhost:8765",  # Local dev server
        NOTIFICATIONS_ENABLED: "true",
        NOTIFICATIONS_MESSAGES: "true",
        NOTIFICATIONS_CALLS: "true",
        DISCOVERY_ENABLED: "false",  # Off by default for privacy
        # Effect defaults
        EFFECTS_ACTIVE_PRESET: "work",
        EFFECTS_FAVORITE_PRESETS: json.dumps(["work", "gaming", "streaming"]),
        EFFECTS_AUDIO_ENABLED: "false",  # Off by default until user enables
        EFFECTS_VIDEO_ENABLED: "false",  # Off by default until user enables
        EFFECTS_SHOW_RESOURCE_MONITOR: "false",
        EFFECTS_QUALITY_OVERRIDE: "null",  # Auto-detect by default
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


# Effect-specific setting helpers


def get_active_preset() -> str:
    """
    Get the name of the currently active effect preset.

    Returns:
        Active preset name (defaults to "work")
    """
    return get_setting(Settings.EFFECTS_ACTIVE_PRESET, "work")


def set_active_preset(name: str) -> None:
    """
    Set the currently active effect preset.

    Args:
        name: Preset name to activate
    """
    set_setting(Settings.EFFECTS_ACTIVE_PRESET, name)


def get_favorite_presets() -> List[str]:
    """
    Get list of favorite presets for quick access bar.

    Returns:
        List of preset names
    """
    json_str = get_setting(
        Settings.EFFECTS_FAVORITE_PRESETS,
        json.dumps(["work", "gaming", "streaming"])
    )
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return ["work", "gaming", "streaming"]


def set_favorite_presets(presets: List[str]) -> None:
    """
    Set favorite presets for quick access.

    Args:
        presets: List of preset names
    """
    set_setting(Settings.EFFECTS_FAVORITE_PRESETS, json.dumps(presets))


def get_effects_enabled() -> Tuple[bool, bool]:
    """
    Get whether audio and video effects are enabled.

    Returns:
        Tuple of (audio_enabled, video_enabled)
    """
    audio_enabled = get_setting(Settings.EFFECTS_AUDIO_ENABLED, "false") == "true"
    video_enabled = get_setting(Settings.EFFECTS_VIDEO_ENABLED, "false") == "true"
    return audio_enabled, video_enabled


def set_effects_enabled(audio: bool, video: bool) -> None:
    """
    Set whether audio and video effects are enabled.

    Args:
        audio: Whether audio effects are enabled
        video: Whether video effects are enabled
    """
    set_setting(Settings.EFFECTS_AUDIO_ENABLED, "true" if audio else "false")
    set_setting(Settings.EFFECTS_VIDEO_ENABLED, "true" if video else "false")


def get_quality_override() -> Optional[str]:
    """
    Get quality override setting.

    Returns:
        Quality level ("low", "medium", "high", "ultra") or None for auto
    """
    value = get_setting(Settings.EFFECTS_QUALITY_OVERRIDE, "null")
    return None if value == "null" else value


def set_quality_override(quality: Optional[str]) -> None:
    """
    Set quality override.

    Args:
        quality: Quality level ("low", "medium", "high", "ultra") or None for auto
    """
    value = "null" if quality is None else quality
    set_setting(Settings.EFFECTS_QUALITY_OVERRIDE, value)


def get_show_resource_monitor() -> bool:
    """
    Get whether to show resource usage monitor.

    Returns:
        True if resource monitor should be shown
    """
    return get_setting(Settings.EFFECTS_SHOW_RESOURCE_MONITOR, "false") == "true"


def set_show_resource_monitor(show: bool) -> None:
    """
    Set whether to show resource usage monitor.

    Args:
        show: Whether to show resource monitor
    """
    set_setting(Settings.EFFECTS_SHOW_RESOURCE_MONITOR, "true" if show else "false")
