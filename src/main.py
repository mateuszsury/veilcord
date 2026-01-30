"""
DiscordOpus - Secure P2P Messenger

Main application entry point.
"""

import sys
import webview

from src.api.bridge import API
from src.storage.db import init_database, close_database
from src.network.service import start_network, stop_network

# Debug mode - set to False for production
DEBUG = '--dev' in sys.argv


def main():
    # Initialize database
    init_database()

    # Create API instance
    api = API()

    # Determine URL
    if DEBUG:
        url = 'http://localhost:5173'  # Vite dev server
    else:
        url = 'frontend/dist/index.html'

    # Create window
    window = webview.create_window(
        'DiscordOpus',
        url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        background_color='#0a0a0f'  # Cosmic dark background
    )

    # Start application with network service in background thread
    try:
        # start_network runs in background thread with asyncio event loop
        webview.start(
            func=lambda: start_network(window),
            debug=DEBUG
        )
    finally:
        stop_network()
        close_database()


if __name__ == '__main__':
    main()
