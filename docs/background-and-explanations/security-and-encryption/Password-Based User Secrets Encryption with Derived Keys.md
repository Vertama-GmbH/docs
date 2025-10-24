# Password-Based User Secrets Encryption

## Overview

This implementation encrypts user secrets using a password-derived key, without storing any encryption secrets server-side. Users must provide their password to decrypt their secrets.

## The Problem

We need to:
- Encrypt user secrets (API keys, tokens, etc.)
- NOT store any encryption keys server-side
- Derive encryption keys from user passwords
- Ensure the same password always produces the same key (for decryption)

**Challenge**: Deterministic key derivation (same password → same key) is vulnerable to brute-force attacks if not properly protected.

## The Solution: Argon2id + AES-GCM

### Key Derivation: Argon2id

**Why Argon2id?**
- Winner of the Password Hashing Competition
- Makes brute-force attacks computationally expensive (~100-500ms per attempt)
- Memory-hard: resistant to GPU/ASIC attacks
- Deterministic with salt: same password + salt = same key

**How it works:**
```
encryption_key = Argon2id(password, salt, iterations, memory)
```

**Key parameters:**
- **Salt**: Random 16-byte value, unique per user, stored in database (not secret!)
- **Iterations**: Time cost (typically 3), tune so derivation takes ~100-500ms
- **Memory**: Memory cost (typically 64MB), makes parallel attacks expensive
- **Output**: 256-bit encryption key

### Encryption: AES-256-GCM

**Why AES-GCM?**
- Industry standard for authenticated encryption
- Provides confidentiality (encryption) AND authenticity (prevents tampering)
- Fast and well-supported

**How it works:**
```
ciphertext = AES-GCM-Encrypt(plaintext, key, iv)
```

**Key parameters:**
- **IV (Initialization Vector)**: Random 12-byte value, unique per encryption operation
- **Key**: 256-bit key derived from password via Argon2id
- **Output**: Ciphertext with embedded authentication tag

## What Gets Stored

### Per User (once):
- **KDF Salt** (16 bytes, Base64 encoded): Used to derive encryption key
- **Algorithm parameters** (optional): iterations, memory cost for future flexibility

### Per Secret:
- **Encrypted Data** (variable length, Base64 encoded): IV (12 bytes) + ciphertext combined

**Storage format:**
```
encrypted_value = Base64(IV || ciphertext)
```

The IV is prepended to the ciphertext for convenience - it's not secret, just needs to be unique.

## Security Properties

### What This Protects Against:
- **Database breach**: Encrypted secrets are useless without user passwords
- **Weak passwords**: Argon2id makes brute-force attacks slow (~100-500ms per guess)
- **Rainbow tables**: Unique per-user salts prevent precomputed attacks
- **Tampering**: GCM authentication tag detects any modifications

### What This Does NOT Protect Against:
- **Weak user passwords**: Still vulnerable to dictionary attacks (just slower)
- **Compromised passwords**: If password is leaked, secrets can be decrypted
- **Password reuse**: Users reusing passwords across services

### Important Constraints:
- **No password recovery**: If user forgets password, secrets are permanently lost
- **Password required for access**: User must provide password on every session
- **Performance impact**: ~100-500ms key derivation on login (by design)

## Key Decisions

### Why Not Just Hash Passwords?
Hashing (like bcrypt) is for *verifying* passwords, not *deriving* keys. Each hash uses a random salt, so the same password produces different hashes - incompatible with encryption.

### Why Store Salt?
The salt ensures different users with the same password get different keys. It's not secret, just unique. Without it stored, we couldn't reproduce the same key from the password.

### Why Store IV with Ciphertext?
The IV must be unique for each encryption but doesn't need to be secret. Storing it with the ciphertext is standard practice and simplifies key management.

### Why Base64 Encoding?
Makes binary data (salt, IV, ciphertext) easy to store in text database columns. Alternative is binary BLOB storage.

## Testing Considerations

Argon2id is intentionally slow (~100-500ms). For unit tests:
- Use reduced parameters: `iterations=1, memory=1024KB` (~5-10ms)
- Reserve full parameters for integration tests
- The slowness is a security feature, not a bug!

## Architecture Trade-offs

**Pros:**
- Zero-knowledge architecture: server never sees encryption keys
- Strong security with proper password
- No server-side secret management complexity

**Cons:**
- No password recovery mechanism
- User experience: must enter password to decrypt secrets
- Performance: noticeable delay on login (by design)
- Password strength critical: system security depends entirely on password quality

## References

- [Argon2 RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106)
- [NIST Guidelines on Password-Based Key Derivation](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [AES-GCM Specification](https://csrc.nist.gov/publications/detail/sp/800-38d/final)