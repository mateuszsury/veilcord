"""
Network module for signaling server communication.

Provides WebSocket client for presence and P2P connection establishment.
"""

from src.network.signaling_client import SignalingClient, ConnectionState
from src.network.auth import create_auth_response, verify_challenge

__all__ = [
    "SignalingClient",
    "ConnectionState",
    "create_auth_response",
    "verify_challenge",
]
