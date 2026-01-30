"""
Windows DPAPI encryption for secure key storage.

DPAPI (Data Protection API) encrypts data using the Windows user's credentials.
Keys encrypted with DPAPI can only be decrypted by the same Windows user account.

Security properties:
- User-scoped encryption: Only the logged-in Windows user can decrypt
- No key management: Windows handles the master key automatically
- Automatic key rotation: Windows rotates master keys periodically

WARNING: DPAPI keys are tied to the Windows user profile. If the user reinstalls
Windows or the profile is corrupted, DPAPI-encrypted data becomes unrecoverable.
Always implement password-based backup (see crypto/backup.py).
"""

import win32crypt


def dpapi_encrypt(plaintext: bytes) -> bytes:
    """
    Encrypt data using Windows DPAPI (current user scope).

    The encryption is tied to the current Windows user account.
    The encrypted blob includes internal metadata for decryption.

    Args:
        plaintext: Raw bytes to encrypt (e.g., 32-byte database key)

    Returns:
        DPAPI-encrypted blob (includes internal metadata for decryption)

    Raises:
        pywintypes.error: If encryption fails (rare, usually system error)
    """
    encrypted = win32crypt.CryptProtectData(
        plaintext,
        None,  # Description (optional, stored in plaintext)
        None,  # Optional entropy (additional password)
        None,  # Reserved
        None,  # Prompt struct (None = no UI)
        0      # Flags (0 = current user scope)
    )
    return encrypted


def dpapi_decrypt(encrypted: bytes) -> bytes:
    """
    Decrypt DPAPI-protected data.

    The decryption will only succeed for the Windows user who encrypted
    the data (or a domain user with roaming credentials).

    Args:
        encrypted: DPAPI blob from dpapi_encrypt()

    Returns:
        Original plaintext bytes

    Raises:
        pywintypes.error: If decryption fails (wrong user, corrupted data,
            or data was encrypted on a different machine/user profile)
    """
    description, decrypted = win32crypt.CryptUnprotectData(
        encrypted,
        None,  # Optional entropy (must match encryption)
        None,  # Reserved
        None,  # Prompt struct
        0      # Flags
    )
    return decrypted
