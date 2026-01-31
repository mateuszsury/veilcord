"""
Tufup configuration settings for auto-update.

These paths and URLs are used by the UpdateService to locate
update metadata and download new versions.

IMPORTANT: For production:
1. Update UPDATE_SERVER_URL to your actual update server
2. Bundle root.json in PyInstaller .spec file
3. Sign updates with your private key
"""

import sys
from pathlib import Path

# Application identity
APP_NAME = "DiscordOpus"
CURRENT_VERSION = "1.0.0"  # Update this for each release

# Update server URL - replace with production URL when ready
# For development, can use `python -m http.server 8000` in update repo
UPDATE_SERVER_URL = "https://updates.discordopus.app"

# Paths for tufup metadata and downloaded updates
# In frozen app, use _MEIPASS for bundled files
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BUNDLE_DIR = Path(sys._MEIPASS)
    METADATA_DIR = BUNDLE_DIR / "tufup_metadata"
    # Install dir is where the exe lives
    TARGET_DIR = Path(sys.executable).parent
else:
    # Running from source
    METADATA_DIR = Path(__file__).parent.parent.parent / "tufup_metadata"
    TARGET_DIR = Path(__file__).parent.parent.parent

# Ensure metadata dir exists (for development)
METADATA_DIR.mkdir(parents=True, exist_ok=True)
