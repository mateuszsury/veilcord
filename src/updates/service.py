"""
Auto-update service using tufup for secure, cryptographically-verified updates.

Provides update checking, download, and installation with:
- TUF framework security (prevents replay, MITM, freeze attacks)
- Patch-based updates (bandwidth efficient)
- Cryptographic verification before install
- Rollback capability on failure

IMPORTANT: Tufup requires:
1. root.json bundled with app (via PyInstaller .spec datas)
2. Update server with signed metadata (timestamp, snapshot, targets)
3. Proper version numbering in CURRENT_VERSION

Usage:
    service = get_update_service()
    version = service.check_for_updates()
    if version:
        success = service.download_and_install()
        if success:
            # Prompt user to restart app
"""

import logging
from pathlib import Path
from threading import Lock
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from src.updates.settings import (
    APP_NAME,
    CURRENT_VERSION,
    UPDATE_SERVER_URL,
    METADATA_DIR,
    TARGET_DIR,
)

logger = logging.getLogger(__name__)


@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    changelog: str = ""
    size_bytes: int = 0
    is_patch: bool = False


class UpdateService:
    """
    Secure auto-update service using tufup.

    Checks for updates, downloads patches/archives, and installs
    new versions with cryptographic verification.

    The service is designed to:
    1. Check for updates on app launch (non-blocking)
    2. Download updates in background
    3. Install on next app restart (to avoid file lock issues)

    Callbacks:
        on_update_available: Called when update found (version, changelog)
        on_download_progress: Called during download (bytes, total)
        on_update_ready: Called when update downloaded and verified
        on_error: Called on any error (error_message)
    """

    def __init__(self):
        """Initialize update service."""
        self._client = None
        self._lock = Lock()
        self._available_update: Optional[UpdateInfo] = None

        # Callbacks for UI integration
        self.on_update_available: Optional[Callable[[UpdateInfo], None]] = None
        self.on_download_progress: Optional[Callable[[int, int], None]] = None
        self.on_update_ready: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def _get_client(self):
        """Get or create tufup client (lazy initialization)."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    try:
                        from tufup.client import Client

                        # Check if root.json exists
                        root_path = METADATA_DIR / "root.json"
                        if not root_path.exists():
                            logger.warning(
                                f"root.json not found at {root_path}. "
                                "Updates will not work until TUF repository is initialized."
                            )
                            # Return None - will fail gracefully
                            return None

                        self._client = Client(
                            app_name=APP_NAME,
                            app_version=CURRENT_VERSION,
                            update_server_url=UPDATE_SERVER_URL,
                            metadata_dir=str(METADATA_DIR),
                            target_dir=str(TARGET_DIR),
                        )
                        logger.info(
                            f"Initialized tufup client: {APP_NAME} v{CURRENT_VERSION}"
                        )
                    except ImportError:
                        logger.error("tufup not installed")
                        return None
                    except Exception as e:
                        logger.error(f"Failed to initialize tufup client: {e}")
                        return None
        return self._client

    def check_for_updates(self, include_prereleases: bool = False) -> Optional[str]:
        """
        Check if updates are available.

        Args:
            include_prereleases: Include release candidates (rc versions)

        Returns:
            Version string if update available, None otherwise
        """
        client = self._get_client()
        if client is None:
            logger.debug("Update client not available")
            return None

        try:
            pre = "rc" if include_prereleases else None
            available = client.check_for_updates(pre=pre)

            if available:
                logger.info(f"Update available: {available}")
                self._available_update = UpdateInfo(
                    version=available,
                    changelog=self._fetch_changelog(available),
                )
                if self.on_update_available:
                    self.on_update_available(self._available_update)
                return available
            else:
                logger.debug("No updates available")
                return None

        except Exception as e:
            error_msg = f"Update check failed: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return None

    def _fetch_changelog(self, version: str) -> str:
        """
        Fetch changelog for a version.

        In production, this would fetch from update server.
        For now, returns placeholder.
        """
        # TODO: Fetch actual changelog from server
        return f"Version {version} is available with bug fixes and improvements."

    def download_and_install(self) -> bool:
        """
        Download and install available update.

        Downloads the update (full archive or patch), verifies
        cryptographic signatures, and stages for installation.

        The actual installation happens on next app restart to
        avoid file locking issues on Windows.

        Returns:
            True if update downloaded and ready to install, False on error
        """
        client = self._get_client()
        if client is None:
            return False

        if self._available_update is None:
            logger.error("No update available to install")
            return False

        try:
            logger.info(f"Downloading update {self._available_update.version}...")

            # tufup handles:
            # 1. Download (patch if available, full archive otherwise)
            # 2. Cryptographic verification
            # 3. Staging for installation
            client.update()

            logger.info("Update downloaded and verified successfully")
            if self.on_update_ready:
                self.on_update_ready()
            return True

        except Exception as e:
            error_msg = f"Update installation failed: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return False

    def get_current_version(self) -> str:
        """Get current application version."""
        return CURRENT_VERSION

    def get_available_update(self) -> Optional[Dict[str, Any]]:
        """
        Get info about available update.

        Returns:
            Dict with version, changelog, etc. or None
        """
        if self._available_update is None:
            return None
        return {
            "version": self._available_update.version,
            "changelog": self._available_update.changelog,
            "size_bytes": self._available_update.size_bytes,
            "is_patch": self._available_update.is_patch,
        }

    def is_update_available(self) -> bool:
        """Check if an update has been found."""
        return self._available_update is not None


# ========== Module-level singleton ==========

_service: Optional[UpdateService] = None
_service_lock = Lock()


def get_update_service() -> UpdateService:
    """
    Get the update service singleton.

    Creates service on first call (lazy initialization).

    Returns:
        UpdateService instance
    """
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = UpdateService()
    return _service
