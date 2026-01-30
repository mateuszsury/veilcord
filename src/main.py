"""
DiscordOpus - Main Application Entry Point

This module initializes the PyWebView window and exposes the Python API
to the React frontend via the JavaScript bridge.
"""

import webview
import os
import sys

# Debug mode: True = dev server, False = production dist
DEBUG = os.environ.get("DISCORDOPUS_DEBUG", "false").lower() == "true"

# Development server URL (Vite default)
DEV_SERVER_URL = "http://localhost:5173"

# Production frontend path (relative to this file)
DIST_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")


class Api:
    """
    Python API exposed to React frontend via window.pywebview.api

    All public methods are callable from JavaScript:
    window.pywebview.api.ping().then(result => console.log(result))
    """

    def ping(self) -> str:
        """Health check - returns 'pong' to verify bridge is working."""
        return "pong"

    def get_version(self) -> str:
        """Return application version."""
        return "0.0.1"


def get_frontend_url() -> str:
    """
    Determine the frontend URL based on debug mode.

    In development: Use Vite dev server for hot reload
    In production: Use bundled dist/index.html
    """
    if DEBUG:
        return DEV_SERVER_URL

    # Resolve absolute path to dist
    dist_path = os.path.abspath(DIST_PATH)

    if not os.path.exists(dist_path):
        raise FileNotFoundError(
            f"Frontend not built. Run 'npm run build' in frontend/ directory.\n"
            f"Expected: {dist_path}"
        )

    return dist_path


def main():
    """
    Application entry point.

    Creates PyWebView window with React frontend and Python API bridge.
    """
    api = Api()
    url = get_frontend_url()

    # Create main window
    window = webview.create_window(
        title="DiscordOpus",
        url=url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600),
        background_color="#0a0a0a",  # Match frontend dark theme
    )

    # Start the application
    # debug=DEBUG enables dev tools in the webview
    webview.start(debug=DEBUG)


if __name__ == "__main__":
    main()
