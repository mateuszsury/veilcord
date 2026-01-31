"""Group-related data models."""
from dataclasses import dataclass
from typing import Optional
import time
import uuid


@dataclass
class Group:
    """Represents a group conversation."""
    id: str
    name: str
    creator_public_key: str
    created_at: int  # Unix timestamp ms
    updated_at: int
    invite_code: Optional[str] = None
    is_active: bool = True

    @classmethod
    def create(cls, name: str, creator_public_key: str) -> "Group":
        """Create a new group with generated ID and timestamps."""
        now = int(time.time() * 1000)
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            creator_public_key=creator_public_key,
            created_at=now,
            updated_at=now,
            invite_code=None,
            is_active=True
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_public_key": self.creator_public_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "invite_code": self.invite_code,
            "is_active": self.is_active
        }


@dataclass
class GroupMember:
    """Represents a member of a group."""
    id: Optional[int]  # None for new members
    group_id: str
    public_key: str
    display_name: str
    joined_at: int  # Unix timestamp ms
    is_admin: bool = False

    @classmethod
    def create(cls, group_id: str, public_key: str, display_name: str, is_admin: bool = False) -> "GroupMember":
        """Create a new group member."""
        return cls(
            id=None,
            group_id=group_id,
            public_key=public_key,
            display_name=display_name,
            joined_at=int(time.time() * 1000),
            is_admin=is_admin
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "group_id": self.group_id,
            "public_key": self.public_key,
            "display_name": self.display_name,
            "joined_at": self.joined_at,
            "is_admin": self.is_admin
        }


@dataclass
class SenderKeyState:
    """Sender Key state for a group member."""
    id: Optional[int]
    group_id: str
    sender_public_key: str
    chain_key: bytes  # 32 bytes
    signature_public: bytes  # 32 bytes Ed25519 public key
    message_index: int
    updated_at: int

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary (keys as hex)."""
        return {
            "id": self.id,
            "group_id": self.group_id,
            "sender_public_key": self.sender_public_key,
            "chain_key": self.chain_key.hex(),
            "signature_public": self.signature_public.hex(),
            "message_index": self.message_index,
            "updated_at": self.updated_at
        }
