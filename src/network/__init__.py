"""
Network module for signaling server communication.

Provides WebSocket client for presence and P2P connection establishment.
"""

from src.network.signaling_client import SignalingClient, ConnectionState
from src.network.auth import create_auth_response, verify_challenge
from src.network.stun import get_ice_servers, DEFAULT_STUN_SERVERS
from src.network.presence import PresenceManager, UserStatus
from src.network.service import (
    NetworkService,
    start_network,
    stop_network,
    get_network_service,
)

__all__ = [
    "SignalingClient",
    "ConnectionState",
    "create_auth_response",
    "verify_challenge",
    "get_ice_servers",
    "DEFAULT_STUN_SERVERS",
    "PresenceManager",
    "UserStatus",
    "NetworkService",
    "start_network",
    "stop_network",
    "get_network_service",
]
