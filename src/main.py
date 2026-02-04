"""
Veilcord - Secure P2P Messenger

Main application entry point.
"""

import sys
import webview

from src.api.bridge import API
from src.storage.db import init_database, close_database
from src.network.service import start_network, stop_network
from src.updates.service import get_update_service

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
        'Veilcord',
        url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        background_color='#0a0a0f'  # Cosmic dark background
    )

    # Check for updates in background after short delay
    def check_updates_background():
        import time
        time.sleep(3)  # Wait for app to fully initialize
        try:
            update_service = get_update_service()
            available = update_service.check_for_updates()
            if available:
                # Notify frontend about available update
                window.evaluate_js(f'''
                    window.dispatchEvent(new CustomEvent('veilcord:update_available', {{
                        detail: {{ version: "{available}" }}
                    }}));
                ''')
        except Exception as e:
            print(f"Update check failed: {e}")

    import threading
    update_thread = threading.Thread(target=check_updates_background, daemon=True)
    update_thread.start()

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
