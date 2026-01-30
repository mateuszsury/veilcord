"""
STUN server configuration for P2P connections.

STUN (Session Traversal Utilities for NAT) servers help discover
public IP addresses and port mappings for NAT traversal.

Used by aiortc RTCPeerConnection for ICE candidate gathering.
"""

from typing import Optional


# Default STUN servers (Google's free public servers)
DEFAULT_STUN_SERVERS: list[str] = [
    "stun:stun.l.google.com:19302",
    "stun:stun1.l.google.com:19302",
]


def get_ice_servers(
    custom_servers: Optional[list[str]] = None
) -> list[dict]:
    """
    Get ICE server configuration for aiortc RTCConfiguration.

    Args:
        custom_servers: Optional list of STUN/TURN server URLs.
                       If provided, replaces default servers.

    Returns:
        List of ICE server config dicts for RTCConfiguration.
        Format: [{"urls": ["stun:host:port"]}]

    Example:
        >>> from aiortc import RTCPeerConnection, RTCConfiguration
        >>> ice_servers = get_ice_servers()
        >>> config = RTCConfiguration(iceServers=ice_servers)
        >>> pc = RTCPeerConnection(config)
    """
    servers = custom_servers if custom_servers is not None else DEFAULT_STUN_SERVERS

    return [{"urls": [url]} for url in servers]
