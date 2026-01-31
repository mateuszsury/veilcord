"""
Invite code generation and parsing for groups.

Invite codes are self-contained tokens that include:
- Group ID
- Group name (truncated)
- Creator's public key (for verification)
- Expiry timestamp
- Random token (prevents enumeration)

Format: discordopus://join/<base64-payload>
"""

import secrets
import base64
import json
import time
from dataclasses import dataclass
from typing import Optional

# Default invite expiry: 7 days
DEFAULT_EXPIRY_SECONDS = 7 * 24 * 3600

# Maximum group name length in invite
MAX_NAME_LENGTH = 50


@dataclass
class InviteData:
    """Parsed invite code data."""
    group_id: str
    group_name: str
    creator_public_key: str
    expires_at: int  # Unix timestamp
    token: str  # Random token for uniqueness

    @property
    def is_expired(self) -> bool:
        """Check if invite has expired."""
        return time.time() > self.expires_at


def generate_invite_code(
    group_id: str,
    group_name: str,
    creator_public_key: str,
    expiry_seconds: int = DEFAULT_EXPIRY_SECONDS
) -> str:
    """
    Generate a secure invite code for a group.

    Args:
        group_id: UUID of the group
        group_name: Display name of the group
        creator_public_key: Ed25519 public key of group creator
        expiry_seconds: Seconds until invite expires (default 7 days)

    Returns:
        Invite URL in format discordopus://join/<base64-payload>

    The payload contains:
    - g: group ID
    - n: group name (truncated to 50 chars)
    - c: creator public key
    - e: expiry timestamp
    - t: random token (16 bytes, URL-safe base64)
    """
    payload = {
        "g": group_id,
        "n": group_name[:MAX_NAME_LENGTH],
        "c": creator_public_key,
        "e": int(time.time()) + expiry_seconds,
        "t": secrets.token_urlsafe(16)  # 128 bits of entropy
    }

    payload_json = json.dumps(payload, separators=(',', ':'))  # Compact JSON
    encoded = base64.urlsafe_b64encode(payload_json.encode()).decode()

    return f"discordopus://join/{encoded}"


def generate_short_code(
    group_id: str,
    group_name: str,
    creator_public_key: str,
    expiry_seconds: int = DEFAULT_EXPIRY_SECONDS
) -> str:
    """
    Generate a short alphanumeric invite code.

    Alternative to full URL for easier manual sharing.

    Args:
        group_id: UUID of the group
        group_name: Display name of the group
        creator_public_key: Ed25519 public key of group creator
        expiry_seconds: Seconds until invite expires

    Returns:
        Full invite URL (short code is just the token part extracted)

    Note: The short code IS the full URL - we use the same format but
    the frontend can extract just the base64 portion if needed.
    """
    # Same as generate_invite_code - frontend handles display
    return generate_invite_code(group_id, group_name, creator_public_key, expiry_seconds)


def parse_invite_code(code: str) -> InviteData:
    """
    Parse and validate an invite code.

    Accepts both full URL format and raw base64 payload.

    Args:
        code: Invite code (URL or raw base64)

    Returns:
        InviteData with parsed fields

    Raises:
        ValueError: If code is invalid, malformed, or expired
    """
    # Strip whitespace
    code = code.strip()

    # Extract base64 payload
    if code.startswith("discordopus://join/"):
        encoded = code[len("discordopus://join/"):]
    elif code.startswith("discordopus://"):
        # Handle potential typos
        raise ValueError("Invalid invite URL format. Expected discordopus://join/...")
    else:
        # Assume raw base64
        encoded = code

    # Decode
    try:
        payload_json = base64.urlsafe_b64decode(encoded)
        payload = json.loads(payload_json)
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid invite code encoding: {e}")

    # Validate required fields
    required = ["g", "n", "c", "e", "t"]
    missing = [f for f in required if f not in payload]
    if missing:
        raise ValueError(f"Invalid invite: missing fields {missing}")

    invite = InviteData(
        group_id=payload["g"],
        group_name=payload["n"],
        creator_public_key=payload["c"],
        expires_at=payload["e"],
        token=payload["t"]
    )

    # Check expiry
    if invite.is_expired:
        raise ValueError("Invite code has expired")

    return invite


def validate_invite_code(code: str) -> Optional[InviteData]:
    """
    Validate an invite code without raising exceptions.

    Args:
        code: Invite code to validate

    Returns:
        InviteData if valid, None if invalid or expired
    """
    try:
        return parse_invite_code(code)
    except ValueError:
        return None
