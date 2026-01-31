---
phase: 07-group-features
plan: 02
name: Sender Keys Protocol Implementation
completed: 2026-01-31
duration: 3m

subsystem: encryption
tags: [sender-keys, cryptography, aes-gcm, ed25519, hkdf, forward-secrecy]

dependency-graph:
  requires: [07-01]
  provides: [sender-keys-encryption, group-message-crypto]
  affects: [07-03, 07-04]

tech-stack:
  added: []
  patterns: [sender-keys-protocol, chain-key-ratchet, symmetric-ratchet]

key-files:
  created:
    - src/groups/sender_keys.py
  modified:
    - src/groups/__init__.py

decisions:
  - id: sender-keys-domain-separation
    choice: "Unique info strings for HKDF: DiscordOpus_SenderKey_*"
    rationale: "Domain separation prevents key reuse across different derivation purposes"
  - id: max-skip-1000
    choice: "Maximum 1000 messages can be skipped ahead"
    rationale: "Prevents memory exhaustion from malicious senders while allowing reasonable out-of-order handling"
  - id: signature-before-decrypt
    choice: "Verify Ed25519 signature before attempting decryption"
    rationale: "Fail fast on tampered messages, avoid wasted decryption effort"

metrics:
  tasks: 2
  files-created: 1
  files-modified: 1
  lines-added: ~410
---

# Phase 07 Plan 02: Sender Keys Protocol Implementation Summary

**One-liner:** Symmetric chain-key ratchet with Ed25519 signing for O(1) group broadcast encryption

## What Was Built

Implemented the Sender Keys protocol for efficient group message encryption, allowing broadcast encryption where each sender maintains their own chain key that ratchets forward with each message.

### Key Components

1. **SenderKey Class** (sender side)
   - Generates 32-byte random chain key and Ed25519 signing key pair
   - `encrypt()` derives message key via HKDF, encrypts with AES-256-GCM, signs with Ed25519
   - Chain key advances after each encryption (forward secrecy)
   - `export_public()` for distribution to group members
   - `export_private()` / `from_private_export()` for persistence

2. **SenderKeyReceiver Class** (receiver side)
   - Created from sender's `export_public()` data
   - `decrypt()` verifies signature first, then decrypts
   - Handles out-of-order messages via skipped key cache
   - `export_state()` / `from_state()` for persistence

3. **EncryptedGroupMessage Dataclass**
   - Contains ciphertext (nonce || AES-GCM ciphertext), signature, message_index
   - `to_dict()` / `from_dict()` for JSON serialization

### Protocol Flow

```
Sender:                          Receiver:
  |                                 |
  | -- export_public() -----------> |
  |                                 | SenderKeyReceiver.from_public_export()
  |                                 |
  | -- encrypt(plaintext) --------> |
  |    returns EncryptedGroupMessage| decrypt(message)
  |    chain advances               | chain advances
  |                                 |
```

### Cryptographic Details

- **Chain Key Advancement:** SHA256(chain_key || info) - one-way, provides forward secrecy
- **Message Key Derivation:** HKDF-SHA256 with domain-specific info
- **Encryption:** AES-256-GCM with 12-byte random nonce
- **Signing:** Ed25519 signature of ciphertext (provides authentication)

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Domain separation | Unique HKDF info strings | Prevents key reuse vulnerabilities |
| Max skip limit | 1000 messages | Balance between out-of-order tolerance and memory safety |
| Signature verification | Before decryption | Fail fast on tampered messages |
| Key caching cleanup | Keep only last 100 indices | Prevent unbounded memory growth |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created prerequisite models.py**
- **Issue:** Plan depends on src/groups/models.py from 07-01 which wasn't fully executed
- **Fix:** Created Group, GroupMember, SenderKeyState dataclasses as part of this plan
- **Files created:** src/groups/models.py
- **Commit:** 4e5cc39

Note: Some 07-01 artifacts already existed from a previous partial execution (db.py tables, storage/groups.py).

## Verification Results

All 8 verification checks passed:
1. SenderKey generates chain key and signing key
2. encrypt() returns EncryptedGroupMessage with ciphertext, signature, message_index
3. Chain key advances after each encryption (forward secrecy)
4. SenderKeyReceiver.from_public_export() creates receiver from sender's public data
5. decrypt() verifies signature and decrypts message
6. Out-of-order messages handled via skipped key cache
7. Export/import methods work for persistence
8. EncryptedGroupMessage serializes to/from dict

## Files

### Created
- `src/groups/sender_keys.py` (406 lines) - Sender Keys protocol implementation

### Modified
- `src/groups/__init__.py` - Export SenderKey, SenderKeyReceiver, EncryptedGroupMessage

## Next Phase Readiness

**Ready for:**
- 07-03: Group service can now use SenderKey for message encryption
- 07-04: Group messaging can encrypt/decrypt messages

**No blockers identified.**

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 4e5cc39 | feat | Implement Sender Keys protocol with chain ratcheting, Ed25519 signing |
| aa1cf63 | feat | (Previous session) Create group models and storage module |
