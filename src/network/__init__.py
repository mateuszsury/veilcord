"""
Network module for signaling server communication and P2P connections.

Provides WebSocket client for presence, P2P connection establishment,
and WebRTC data channel messaging.
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
from src.network.peer_connection import (
    PeerConnectionManager,
    PeerConnection,
    P2PConnectionState,
)
from src.network.data_channel import MessageChannel, MessageType, ChannelMessage

__all__ = [
    # Signaling
    "SignalingClient",
    "ConnectionState",
    "create_auth_response",
    "verify_challenge",
    # STUN
    "get_ice_servers",
    "DEFAULT_STUN_SERVERS",
    # Presence
    "PresenceManager",
    "UserStatus",
    # Network service
    "NetworkService",
    "start_network",
    "stop_network",
    "get_network_service",
    # P2P connections
    "PeerConnectionManager",
    "PeerConnection",
    "P2PConnectionState",
    # Messaging
    "MessageChannel",
    "MessageType",
    "ChannelMessage",
]
