"""Auto-update service for DiscordOpus."""
from src.updates.service import UpdateService, get_update_service
from src.updates.settings import (
    APP_NAME,
    CURRENT_VERSION,
    UPDATE_SERVER_URL,
    METADATA_DIR,
    TARGET_DIR,
)

__all__ = [
    'UpdateService',
    'get_update_service',
    'APP_NAME',
    'CURRENT_VERSION',
    'UPDATE_SERVER_URL',
    'METADATA_DIR',
    'TARGET_DIR',
]
