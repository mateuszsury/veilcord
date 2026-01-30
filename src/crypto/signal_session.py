"""
Signal Protocol session management using X3DH and Double Ratchet.

Implements the Signal Protocol for E2E encrypted messaging:
1. X3DH establishes initial shared secret (key agreement)
2. Double Ratchet provides ongoing encryption with forward secrecy

Session state must be persisted after every encrypt/decrypt operation
to maintain synchronization with the peer.

This implementation uses the python-doubleratchet and python-x3dh libraries.

References:
- https://signal.org/docs/specifications/x3dh/
- https://signal.org/docs/specifications/doubleratchet/
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Double Ratchet imports
from doubleratchet import DoubleRatchet as DoubleRatchetBase, EncryptedMessage, Header
from doubleratchet.recommended.diffie_hellman_ratchet_curve25519 import (
    DiffieHellmanRatchet as DiffieHellmanRatchetCurve25519
)
from doubleratchet.recommended.aead_aes_hmac import AEAD as AEADBase
from doubleratchet.recommended.kdf_hkdf import KDF as KDFBase
from doubleratchet.recommended.crypto_provider import HashFunction


# Constants for the application
INFO_ROOT_CHAIN = b"DiscordOpus_RootChain_v1"
INFO_MESSAGE_CHAIN = b"DiscordOpus_MessageChain_v1"
INFO_AEAD = b"DiscordOpus_AEAD_v1"
ASSOCIATED_DATA = b"DiscordOpus_v1"
MESSAGE_CHAIN_CONSTANT = b"DiscordOpus_MessageChainConstant"

# Ratchet configuration
# DOS_PROTECTION_THRESHOLD must be <= MAX_SKIPPED_MESSAGE_KEYS
MAX_SKIPPED_MESSAGE_KEYS = 1000  # Max skipped keys to store
DOS_PROTECTION_THRESHOLD = 1000  # Max skipped message keys to calculate


class RootChainKDF(KDFBase):
    """KDF for the Double Ratchet root chain using HKDF-SHA256."""

    @staticmethod
    def _get_hash_function() -> HashFunction:
        return HashFunction.SHA_256

    @staticmethod
    def _get_info() -> bytes:
        return INFO_ROOT_CHAIN


class MessageChainKDF(KDFBase):
    """KDF for the Double Ratchet message chains using HKDF-SHA256."""

    @staticmethod
    def _get_hash_function() -> HashFunction:
        return HashFunction.SHA_256

    @staticmethod
    def _get_info() -> bytes:
        return INFO_MESSAGE_CHAIN


class MessageAEAD(AEADBase):
    """AEAD for message encryption using AES-256-CBC + HMAC-SHA256."""

    @staticmethod
    def _get_hash_function() -> HashFunction:
        return HashFunction.SHA_256

    @staticmethod
    def _get_info() -> bytes:
        return INFO_AEAD


class DoubleRatchet(DoubleRatchetBase):
    """
    Concrete Double Ratchet implementation for DiscordOpus.

    Implements the required _build_associated_data method to encode
    associated data and header into a unique byte sequence.
    """

    @staticmethod
    def _build_associated_data(associated_data: bytes, header: Header) -> bytes:
        """
        Build associated data by concatenating AD with encoded header.

        Format: [4-byte AD length][AD][32-byte ratchet pub][4-byte prev_chain_len][4-byte chain_len]

        This ensures the output is parseable as a unique pair (associated data, header).
        """
        # Encode header components
        ratchet_pub = header.ratchet_pub
        prev_chain_len = header.previous_sending_chain_length.to_bytes(4, 'big')
        chain_len = header.sending_chain_length.to_bytes(4, 'big')

        # Prepend AD length to make it parseable
        ad_len = len(associated_data).to_bytes(4, 'big')

        return ad_len + associated_data + ratchet_pub + prev_chain_len + chain_len


@dataclass
class SerializedEncryptedMessage:
    """
    Serializable container for an encrypted message.

    Uses base64-safe JSON for transmission over data channels.
    """
    header_json: Dict[str, Any]  # Header as JSON dict
    ciphertext_hex: str  # Ciphertext as hex string


class SignalSession:
    """
    Manages an encrypted messaging session with a single contact.

    Uses X3DH for initial key agreement and Double Ratchet for ongoing
    message encryption with perfect forward secrecy.

    Typical flow:
    1. Sender calls initialize_as_sender() with recipient's X25519 public key
    2. Sender gets initial message with their ephemeral public key
    3. Recipient calls initialize_as_receiver() with sender's ephemeral key
    4. Both parties can now encrypt/decrypt messages

    State must be serialized and persisted after every operation.

    Note: All encrypt/decrypt methods are async due to the underlying library.
    Use asyncio.run() or await in an async context.
    """

    def __init__(self):
        self._ratchet: Optional[DoubleRatchet] = None
        self._initialized = False
        self._shared_secret: Optional[bytes] = None

    @property
    def initialized(self) -> bool:
        """Check if session is ready for encryption/decryption."""
        return self._initialized and self._ratchet is not None

    async def initialize_as_sender(
        self,
        our_x25519_private: X25519PrivateKey,
        their_x25519_public: X25519PublicKey,
        initial_message: bytes
    ) -> Tuple[bytes, EncryptedMessage]:
        """
        Initialize session as the sender (Alice role in X3DH).

        Performs simplified X3DH key agreement and sets up Double Ratchet.

        Args:
            our_x25519_private: Our long-term X25519 private key
            their_x25519_public: Recipient's X25519 public key
            initial_message: First message to encrypt

        Returns:
            Tuple of (ephemeral_public_key, encrypted_initial_message)
            The ephemeral key must be sent to recipient for their initialization.
        """
        # Generate ephemeral key pair for this session
        ephemeral_private = X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()

        # Simplified X3DH: DH between our ephemeral and their identity
        # In full X3DH, there would be additional DH operations with pre-keys
        dh_output = ephemeral_private.exchange(their_x25519_public)

        # Derive shared secret using HKDF
        shared_secret = self._derive_shared_secret(dh_output)

        # Initialize Double Ratchet as sender (Alice)
        # We use their public key as the initial remote ratchet key
        self._ratchet, encrypted_msg = await DoubleRatchet.encrypt_initial_message(
            diffie_hellman_ratchet_class=DiffieHellmanRatchetCurve25519,
            root_chain_kdf=RootChainKDF,
            message_chain_kdf=MessageChainKDF,
            message_chain_constant=MESSAGE_CHAIN_CONSTANT,
            dos_protection_threshold=DOS_PROTECTION_THRESHOLD,
            max_num_skipped_message_keys=MAX_SKIPPED_MESSAGE_KEYS,
            aead=MessageAEAD,
            shared_secret=shared_secret,
            recipient_ratchet_pub=their_x25519_public.public_bytes_raw(),
            message=initial_message,
            associated_data=ASSOCIATED_DATA
        )

        self._initialized = True
        self._shared_secret = shared_secret

        return ephemeral_public.public_bytes_raw(), encrypted_msg

    async def initialize_as_receiver(
        self,
        our_x25519_private: X25519PrivateKey,
        their_ephemeral_public: bytes,
        initial_message: EncryptedMessage
    ) -> bytes:
        """
        Initialize session as the receiver (Bob role in X3DH).

        Args:
            our_x25519_private: Our X25519 private key
            their_ephemeral_public: Sender's ephemeral public key (from initial message)
            initial_message: The encrypted initial message

        Returns:
            Decrypted initial message plaintext
        """
        # Reconstruct their ephemeral key
        their_ephemeral = X25519PublicKey.from_public_bytes(their_ephemeral_public)

        # Simplified X3DH: DH between our identity and their ephemeral
        dh_output = our_x25519_private.exchange(their_ephemeral)

        # Derive shared secret using HKDF
        shared_secret = self._derive_shared_secret(dh_output)

        # Initialize Double Ratchet as receiver (Bob)
        self._ratchet, plaintext = await DoubleRatchet.decrypt_initial_message(
            diffie_hellman_ratchet_class=DiffieHellmanRatchetCurve25519,
            root_chain_kdf=RootChainKDF,
            message_chain_kdf=MessageChainKDF,
            message_chain_constant=MESSAGE_CHAIN_CONSTANT,
            dos_protection_threshold=DOS_PROTECTION_THRESHOLD,
            max_num_skipped_message_keys=MAX_SKIPPED_MESSAGE_KEYS,
            aead=MessageAEAD,
            shared_secret=shared_secret,
            own_ratchet_priv=our_x25519_private.private_bytes_raw(),
            message=initial_message,
            associated_data=ASSOCIATED_DATA
        )

        self._initialized = True
        self._shared_secret = shared_secret

        return plaintext

    async def encrypt(self, plaintext: bytes) -> EncryptedMessage:
        """
        Encrypt a message.

        Args:
            plaintext: Message bytes to encrypt

        Returns:
            EncryptedMessage with header and ciphertext

        Raises:
            RuntimeError: If session not initialized
        """
        if not self.initialized:
            raise RuntimeError("Session not initialized")

        return await self._ratchet.encrypt_message(plaintext, ASSOCIATED_DATA)

    async def decrypt(self, message: EncryptedMessage) -> bytes:
        """
        Decrypt a message.

        Args:
            message: EncryptedMessage to decrypt

        Returns:
            Decrypted plaintext bytes

        Raises:
            RuntimeError: If session not initialized
            Exception: If decryption fails (wrong key, tampered message)
        """
        if not self.initialized:
            raise RuntimeError("Session not initialized")

        return await self._ratchet.decrypt_message(message, ASSOCIATED_DATA)

    def serialize(self) -> bytes:
        """
        Serialize session state for persistence.

        MUST be called after every encrypt/decrypt and saved to database.

        Returns:
            Serialized state as JSON bytes
        """
        if not self._ratchet:
            return b""

        state = {
            "ratchet": self._ratchet.json,
            "shared_secret": self._shared_secret.hex() if self._shared_secret else None,
            "version": 1
        }
        return json.dumps(state).encode('utf-8')

    @classmethod
    def deserialize(cls, data: bytes) -> "SignalSession":
        """
        Restore session from serialized state.

        Args:
            data: Previously serialized state bytes

        Returns:
            Restored SignalSession
        """
        session = cls()
        if not data:
            return session

        state = json.loads(data.decode('utf-8'))

        if state.get("shared_secret"):
            session._shared_secret = bytes.fromhex(state["shared_secret"])

        if state.get("ratchet"):
            session._ratchet = DoubleRatchet.from_json(
                state["ratchet"],
                diffie_hellman_ratchet_class=DiffieHellmanRatchetCurve25519,
                root_chain_kdf=RootChainKDF,
                message_chain_kdf=MessageChainKDF,
                message_chain_constant=MESSAGE_CHAIN_CONSTANT,
                dos_protection_threshold=DOS_PROTECTION_THRESHOLD,
                max_num_skipped_message_keys=MAX_SKIPPED_MESSAGE_KEYS,
                aead=MessageAEAD
            )
            session._initialized = True

        return session

    def _derive_shared_secret(self, dh_output: bytes) -> bytes:
        """Derive 32-byte shared secret from DH output using HKDF."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"DiscordOpus_X3DH_SharedSecret_v1",
        )
        return hkdf.derive(dh_output)


def header_to_dict(header: Header) -> Dict[str, Any]:
    """Convert Header namedtuple to JSON-serializable dict."""
    return {
        "ratchet_pub": header.ratchet_pub.hex(),
        "prev_chain_length": header.previous_sending_chain_length,
        "chain_length": header.sending_chain_length
    }


def header_from_dict(data: Dict[str, Any]) -> Header:
    """Reconstruct Header from dict."""
    return Header(
        ratchet_pub=bytes.fromhex(data["ratchet_pub"]),
        previous_sending_chain_length=data["prev_chain_length"],
        sending_chain_length=data["chain_length"]
    )


def encrypted_message_to_dict(msg: EncryptedMessage) -> Dict[str, Any]:
    """Convert EncryptedMessage to JSON-serializable dict."""
    return {
        "header": header_to_dict(msg.header),
        "ciphertext": msg.ciphertext.hex()
    }


def encrypted_message_from_dict(data: Dict[str, Any]) -> EncryptedMessage:
    """Reconstruct EncryptedMessage from dict."""
    return EncryptedMessage(
        header=header_from_dict(data["header"]),
        ciphertext=bytes.fromhex(data["ciphertext"])
    )
