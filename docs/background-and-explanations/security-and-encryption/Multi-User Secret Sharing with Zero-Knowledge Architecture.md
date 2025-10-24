# Multi-User Secret Sharing with Zero-Knowledge Architecture

## Implementation Guide

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Solution Architecture](#solution-architecture)
3. [Cryptographic Components](#cryptographic-components)
4. [Data Model](#data-model)
5. [Core Operations](#core-operations)
6. [Security Analysis](#security-analysis)
7. [Implementation Considerations](#implementation-considerations)
8. [References](#references)

---

## Problem Statement

### Requirements

- Encrypt user secrets so the server cannot read them
- Allow multiple users to access the same secret
- Enable granting/revoking access without password sharing
- Maintain zero-knowledge architecture (server never sees plaintext secrets or passwords)
- Support asynchronous access grants (users don't need to be online simultaneously)

### Constraints

- Cannot store encryption keys server-side
- Cannot share passwords between users
- Must be able to decrypt secrets deterministically
- Need to derive encryption keys from user passwords

---

## Solution Architecture

### Two-Layer Encryption Model

The solution uses a **Data Encryption Key (DEK) + Key Encryption Key (KEK)** pattern with elliptic curve cryptography:

```
Secret
  ↓ encrypted with
Data Encryption Key (DEK) - random, same for all users with access
  ↓ encrypted separately for each user with
X25519 Key Agreement (user's private + granter's public)
  ↓ derives
Shared Secret → encrypts DEK with AES-GCM
  ↓ decrypted with
User's Private Key (X25519) - encrypted at rest
  ↓ encrypted with
Key Encryption Key (KEK) - derived from password
  ↓ derived from
User's Password (Argon2id + salt)
```

### Key Insight

**The DEK is shared** (conceptually), but each user has their own encrypted copy of it. Users never exchange passwords; instead, they use public-key cryptography to securely share the DEK.

---

## Cryptographic Components

### 1. Password-Based Key Derivation (Argon2id)

**Purpose**: Derive a symmetric Key Encryption Key (KEK) from user password

**Algorithm**: Argon2id
- Time cost: 3 iterations (tune to ~100-500ms)
- Memory cost: 64 MB (65536 KB)
- Salt: 16 bytes, random per user, stored in database
- Output: 256-bit KEK

**Properties**:
- Deterministic: same password + salt → same KEK
- Slow by design: makes brute-force expensive
- Memory-hard: resistant to GPU/ASIC attacks

### 2. Symmetric Encryption (AES-256-GCM)

**Purpose**: Encrypt private keys and secrets

**Algorithm**: AES-256-GCM
- Key size: 256 bits
- IV size: 12 bytes (96 bits), random per encryption
- Authentication tag: 128 bits (embedded in ciphertext)

**Used for**:
- Encrypting user's private X25519 key with KEK
- Encrypting secrets with DEK
- Encrypting DEK with shared secret from key agreement

**Properties**:
- Authenticated encryption (confidentiality + integrity)
- Fast and well-supported
- IV must be unique per encryption operation

### 3. Elliptic Curve Key Agreement (X25519)

**Purpose**: Enable secure sharing of DEK between users via Diffie-Hellman key agreement

**Algorithm**: X25519 (Curve25519)
- Key size: 32 bytes (256 bits)
- Each user has a key pair (public + private)
- Key agreement produces a shared secret, used with AES-GCM to encrypt DEK

**Properties**:
- Public key: can be stored in plaintext, used for key agreement
- Private key: encrypted with KEK, used for key agreement
- Enables encryption without recipient's password
- 10-20x faster than RSA-2048
- Smaller keys (32 bytes vs 256+ bytes for RSA)

---

## Data Model

### User Crypto Keys

```kotlin
data class UserCryptoKeys(
    val userId: UUID,
    val publicKey: ByteArray,           // X25519 public key (32 bytes, plaintext)
    val encryptedPrivateKey: ByteArray, // X25519 private key (AES-encrypted with KEK)
    val privateKeyKDFSalt: ByteArray,   // Salt for deriving KEK (16 bytes)
    val privateKeyIV: ByteArray,        // IV for encrypting private key (12 bytes)
    val kdfIterations: Int = 3,         // Argon2id parameters (for flexibility)
    val kdfMemoryKb: Int = 65536
)
```

**Storage**: One row per user

**Security notes**:
- Public key stored in plaintext (it's meant to be public)
- Private key encrypted with user's KEK (derived from password)
- Salt is not secret, just unique per user
- If database is compromised, attacker needs user passwords to decrypt private keys

### Shared Secrets

```kotlin
data class SharedSecret(
    val id: UUID,
    val name: String,                   // e.g., "Production API Key"
    val encryptedSecret: String,        // Secret encrypted with DEK (Base64)
    val secretIV: String,               // IV for secret encryption (Base64)
    val createdBy: UUID,                // User who created the secret
    val createdAt: Timestamp
)
```

**Storage**: One row per secret

**Security notes**:
- Secret encrypted with a random DEK
- DEK is NOT stored here (stored separately per user)
- IV is unique for this encryption

### User Secret Access

```kotlin
data class UserSecretAccess(
    val secretId: UUID,                 // Reference to SharedSecret
    val userId: UUID,                   // User who has access
    val encryptedDEK: ByteArray,        // DEK encrypted via X25519 key agreement + AES-GCM
    val dekIV: ByteArray,               // IV for DEK encryption (12 bytes)
    val grantedBy: UUID,                // User who granted access (used for key agreement)
    val grantedAt: Timestamp
)
```

**Storage**: One row per (user, secret) pair

**Security notes**:
- Each user has their own encrypted copy of the DEK
- DEK encrypted using X25519 key agreement (user's private + granter's public) + AES-GCM
- User can decrypt DEK by deriving the same shared secret (requires their password to decrypt private key)
- `grantedBy` indicates whose public key to use for key agreement

### Database Schema Example

```sql
CREATE TABLE user_crypto_keys (
    user_id UUID PRIMARY KEY,
    public_key TEXT NOT NULL,
    encrypted_private_key TEXT NOT NULL,
    private_key_kdf_salt VARCHAR(32) NOT NULL,
    private_key_iv VARCHAR(32) NOT NULL,
    kdf_iterations INT DEFAULT 3,
    kdf_memory_kb INT DEFAULT 65536,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shared_secret (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    encrypted_secret TEXT NOT NULL,
    secret_iv VARCHAR(32) NOT NULL,
    created_by UUID REFERENCES user_crypto_keys(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_secret_access (
    secret_id UUID REFERENCES shared_secret(id),
    user_id UUID REFERENCES user_crypto_keys(user_id),
    encrypted_dek TEXT NOT NULL,
    granted_by UUID REFERENCES user_crypto_keys(user_id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (secret_id, user_id)
);
```

---

## Core Operations

### 1. User Registration / Key Setup

**Trigger**: New user account creation

**Process**:
1. Generate X25519 key pair (32-byte keys)
2. Generate random salt (16 bytes)
3. Derive KEK from password using Argon2id
4. Encrypt private key with KEK using AES-GCM
5. Store: public key (plaintext), encrypted private key, salt, IV

**Pseudocode**:
```kotlin
fun setupUserKeys(userId: UUID, password: String) {
    // Generate X25519 key pair
    val keyPair = generateX25519KeyPair()
    
    // Derive KEK from password
    val salt = generateRandomBytes(16)
    val kek = Argon2id.derive(password, salt, iterations=3, memory=65536)
    
    // Encrypt private key with KEK
    val iv = generateRandomBytes(12)
    val encryptedPrivateKey = AES_GCM.encrypt(keyPair.private, kek, iv)
    
    // Store in database
    store(UserCryptoKeys(
        userId = userId,
        publicKey = keyPair.public.toBase64(),
        encryptedPrivateKey = encryptedPrivateKey.toBase64(),
        privateKeyKDFSalt = salt.toBase64(),
        privateKeyIV = iv.toBase64()
    ))
    
    // Clear sensitive data
    kek.clear()
    keyPair.private.destroy()
}
```

**Security considerations**:
- Private key never stored in plaintext
- KEK never stored, only derived on-demand
- Password never stored

### 2. Create and Store Secret

**Trigger**: User creates a new secret to share

**Note**: Also available as `createSecret(userId, kek, name, value)` using pre-derived KEK for better performance (see [Session-Based KEK Storage](#session-based-kek-storage-pattern-ux-optimization)).

**Process**:
1. Generate random DEK (256-bit key)
2. Encrypt secret with DEK using AES-GCM
3. Get creator's public key
4. Encrypt DEK with creator's public key (so they can access it later)
5. Store: encrypted secret, encrypted DEK for creator

**Pseudocode**:
```kotlin
fun createSecret(
    userId: UUID, 
    secretName: String, 
    secretValue: String
): UUID {
    // Generate random DEK
    val dek = generateRandomBytes(32)
    
    // Encrypt secret with DEK
    val secretIV = generateRandomBytes(12)
    val encryptedSecret = AES_GCM.encrypt(secretValue, dek, secretIV)
    
    // Store encrypted secret
    val secretId = UUID.randomUUID()
    store(SharedSecret(
        id = secretId,
        name = secretName,
        encryptedSecret = encryptedSecret.toBase64(),
        secretIV = secretIV.toBase64(),
        createdBy = userId
    ))
    
    // Encrypt DEK using X25519 key agreement (creator's own keys)
    val creatorKeys = getUserKeys(userId)
    val privateKey = decryptPrivateKey(creatorKeys, password) // Already done above
    val sharedSecret = X25519_KeyAgreement(privateKey, creatorKeys.publicKey)
    val dekIV = generateRandomBytes(12)
    val encryptedDEK = AES_GCM.encrypt(dek, sharedSecret, dekIV)

    // Store access record for creator
    store(UserSecretAccess(
        secretId = secretId,
        userId = userId,
        encryptedDEK = encryptedDEK,
        dekIV = dekIV,
        grantedBy = userId
    ))
    
    // Clear sensitive data
    dek.clear()
    
    return secretId
}
```

**Security considerations**:
- DEK is random, never derived from password
- Same DEK used for all users (but encrypted separately for each)
- Secret never stored in plaintext

### 3. Access Secret

**Trigger**: User wants to read a secret they have access to

**Note**: Also available as `accessSecret(userId, kek, secretId)` using pre-derived KEK (see [Session-Based KEK Storage](#session-based-kek-storage-pattern-ux-optimization)).

**Process**:
1. User provides password
2. Derive KEK from password
3. Decrypt user's private key with KEK
4. Retrieve user's encrypted DEK for this secret
5. Decrypt DEK with private key
6. Decrypt secret with DEK
7. Return plaintext secret (clear all keys from memory)

**Pseudocode**:
```kotlin
fun accessSecret(
    secretId: UUID, 
    userId: UUID, 
    password: String
): String {
    // 1. Get user's encrypted private key
    val userKeys = getUserKeys(userId)
    
    // 2. Derive KEK from password
    val kek = Argon2id.derive(
        password, 
        userKeys.privateKeyKDFSalt.fromBase64(),
        iterations = userKeys.kdfIterations,
        memory = userKeys.kdfMemoryKb
    )
    
    // 3. Decrypt private key with KEK
    val privateKey = AES_GCM.decrypt(
        userKeys.encryptedPrivateKey.fromBase64(),
        kek,
        userKeys.privateKeyIV.fromBase64()
    )
    
    // 4. Get user's encrypted DEK for this secret
    val access = getUserAccess(secretId, userId)

    // 5. Derive shared secret via X25519 key agreement
    // Use granter's public key (from grantedBy field)
    val granterKeys = getUserKeys(access.grantedBy)
    val sharedSecret = X25519_KeyAgreement(privateKey, granterKeys.publicKey)

    // 6. Decrypt DEK with shared secret
    val dek = AES_GCM.decrypt(access.encryptedDEK, sharedSecret, access.dekIV)

    // 7. Get and decrypt the secret
    val secret = getSecret(secretId)
    val plaintext = AES_GCM.decrypt(
        secret.encryptedSecret.fromBase64(),
        dek,
        secret.secretIV.fromBase64()
    )
    
    // 8. Clear all sensitive data from memory
    kek.clear()
    privateKey.destroy()
    dek.clear()
    sharedSecret.clear()
    
    return plaintext.toString(Charsets.UTF_8)
}
```

**Security considerations**:
- Password never transmitted or stored
- Private key and keys only exist in memory temporarily
- Multiple layers of decryption: KEK → private key → DEK → secret
- All intermediate keys cleared after use

### 4. Grant Access to Another User

**Trigger**: User A wants to share a secret with User B

**Note**: Also available as `grantAccess(secretId, granterUserId, granterKEK, granteeUserId)` using pre-derived KEK (see [Session-Based KEK Storage](#session-based-kek-storage-pattern-ux-optimization)).

**Process**:
1. User A provides password
2. User A decrypts their private key and retrieves DEK (same as "Access Secret")
3. Get User B's public key (no password needed!)
4. Encrypt DEK with User B's public key
5. Store new access record for User B

**Pseudocode**:
```kotlin
fun grantAccess(
    secretId: UUID,
    granterUserId: UUID,      // User A
    granterPassword: String,  // User A's password
    granteeUserId: UUID       // User B
) {
    // 1-2. Granter decrypts their private key and gets DEK
    val granterKeys = getUserKeys(granterUserId)
    val granterKEK = Argon2id.derive(
        granterPassword,
        granterKeys.privateKeyKDFSalt.fromBase64(),
        iterations = granterKeys.kdfIterations,
        memory = granterKeys.kdfMemoryKb
    )
    
    val granterPrivateKey = AES_GCM.decrypt(
        granterKeys.encryptedPrivateKey.fromBase64(),
        granterKEK,
        granterKeys.privateKeyIV.fromBase64()
    )
    
    val granterAccess = getUserAccess(secretId, granterUserId)

    // Decrypt granter's DEK using key agreement with own keys
    val granterSharedSecret = X25519_KeyAgreement(granterPrivateKey, granterKeys.publicKey)
    val dek = AES_GCM.decrypt(
        granterAccess.encryptedDEK,
        granterSharedSecret,
        granterAccess.dekIV
    )

    // 3. Get grantee's public key (no password needed!)
    val granteeKeys = getUserKeys(granteeUserId)

    // 4. Encrypt DEK for grantee using key agreement (granter's private + grantee's public)
    val granteeSharedSecret = X25519_KeyAgreement(granterPrivateKey, granteeKeys.publicKey)
    val dekIV = generateRandomBytes(12)
    val encryptedDEKForGrantee = AES_GCM.encrypt(dek, granteeSharedSecret, dekIV)
    
    // 5. Store access record for grantee
    store(UserSecretAccess(
        secretId = secretId,
        userId = granteeUserId,
        encryptedDEK = encryptedDEKForGrantee,
        dekIV = dekIV,
        grantedBy = granterUserId  // Grantee will use granter's public key
    ))

    // Clear sensitive data
    granterKEK.clear()
    granterPrivateKey.destroy()
    dek.clear()
    granterSharedSecret.clear()
    granteeSharedSecret.clear()
}
```

**Security considerations**:
- **User B does not need to be online or provide password**
- User B's password never shared with User A
- Only User A's password is needed to perform the grant
- Uses User B's public key (which is safe to use without permission)

### 5. Revoke Access

**Trigger**: Remove a user's ability to access a secret

**Process**:
1. Delete the user's access record (encrypted DEK entry)
2. User can no longer decrypt the secret

**Pseudocode**:
```kotlin
fun revokeAccess(secretId: UUID, userId: UUID) {
    deleteUserAccess(secretId, userId)
}
```

**Important limitation**:
- If user already decrypted and saved the secret, revocation doesn't affect saved copies
- Consider re-encrypting the secret with a new DEK if you need to fully revoke access
- Audit logs recommended to track who accessed what and when

---

## Security Analysis

### What the Server Can See

✅ **Stored in database (not secret)**:
- User public keys (meant to be public)
- Encrypted private keys (useless without passwords)
- KDF salts (not secret, just unique)
- Encrypted DEKs (useless without private keys)
- Encrypted secrets (useless without DEKs)

### What the Server Cannot See

❌ **Never stored or transmitted in plaintext**:
- User passwords
- KEKs (Key Encryption Keys)
- Private keys (plaintext)
- DEKs (plaintext)
- Secrets (plaintext)

### Threat Model

**If database is compromised:**
- Attacker gets: all encrypted data, public keys, salts
- Attacker needs: user passwords to derive KEKs
- Protection: Argon2id makes password brute-forcing expensive (~100-500ms per attempt)
- Weak passwords remain vulnerable (use password policies)

**If single user account is compromised:**
- Attacker gets: access to secrets that user can access
- Attacker cannot: grant themselves access to other secrets
- Attacker cannot: decrypt other users' private keys

**If server is compromised (but not database):**
- Attacker could: intercept passwords during login
- Mitigation: Use TLS, consider client-side key derivation
- This is same risk as any password-based system

### Security Properties

✅ **Zero-knowledge**: Server never sees plaintext secrets or passwords  
✅ **Forward secrecy**: Revoking access prevents future decryption (with limitations)  
✅ **Access control**: Users can only decrypt secrets they've been explicitly granted access to  
✅ **Audit trail**: Track who granted access and when  
✅ **Brute-force resistance**: Argon2id makes password attacks expensive  

❌ **Not protected against**: Weak user passwords, phishing, compromised endpoints  
❌ **No password recovery**: If user forgets password, their secrets are lost  

---

## Implementation Considerations

### Technology Stack (Kotlin/JVM)

**Required libraries**:
```kotlin
// Bouncy Castle for Argon2id and X25519
implementation("org.bouncycastle:bcprov-jdk18on:1.78.1")

// Standard Java crypto for AES-GCM
// (included in JDK, no additional dependencies)
```

**Key classes**:
- `Argon2BytesGenerator` - for key derivation
- `Cipher` with "AES/GCM/NoPadding" - for symmetric encryption
- `KeyPairGenerator` with "X25519" - for key generation (Bouncy Castle provider)
- `KeyAgreement` with "X25519" - for Diffie-Hellman key agreement

### Performance Considerations

**Key derivation (Argon2id)**:
- Expected time: 100-500ms per operation
- Occurs on: login, accessing secrets, granting access
- Tuning: Adjust iterations and memory to balance security vs UX
- Testing: Use reduced parameters (iterations=1, memory=1024KB) for unit tests

**X25519 operations**:
- Key generation: ~5-10ms (done once per user, 10-20x faster than RSA)
- Key agreement: <1ms (much faster than RSA encryption/decryption)
- Key size: 32 bytes (256 bits, much smaller than RSA)

**AES-GCM operations**:
- Very fast: <1ms for typical secret sizes
- Scales linearly with data size

### Memory Management

**Critical: Clear sensitive data after use**

```kotlin
// Clear byte arrays
byteArray.fill(0)

// Destroy keys
secretKey.destroy()
privateKey.destroy()

// Use try-finally blocks
val key = deriveKey(password, salt)
try {
    // Use key
} finally {
    key.fill(0)
}
```

### Error Handling

**Authentication failures**:
- Wrong password → KEK derivation succeeds but decryption fails
- Catch `AEADBadTagException` for AES-GCM failures
- Return generic "authentication failed" (don't leak which step failed)

**Access control**:
- Check user has access record before attempting decryption
- Return 403 Forbidden if no access record exists

### Testing Strategy

**Unit tests** (fast parameters):
```kotlin
class SecretManager(
    val kdfIterations: Int = 3,
    val kdfMemoryKb: Int = 65536
) {
    companion object {
        fun forTesting() = SecretManager(
            kdfIterations = 1,
            kdfMemoryKb = 1024
        )
    }
}
```

**Integration tests** (real parameters):
- Test full flows with production Argon2id settings
- Mark as `@Tag("slow")` or separate test suite
- Run less frequently

**Security tests**:
- Verify keys are cleared from memory
- Test wrong password scenarios
- Test unauthorized access attempts
- Verify encrypted data format

### Key Rotation

**Rotating user passwords**:
1. User provides old and new passwords
2. Derive old KEK, decrypt private key
3. Derive new KEK, re-encrypt private key with new IV
4. Update database with new encrypted private key, new salt, new IV

**Rotating secrets** (for stronger security after revocation):
1. Generate new DEK
2. Re-encrypt secret with new DEK
3. Re-encrypt new DEK for all authorized users
4. Update all records atomically

### Scalability

**Database**:
- Index on `(secret_id, user_id)` for user_secret_access
- Consider partitioning by user_id or secret_id for large deployments

**Caching**:
- Can cache public keys (they don't change often)
- Never cache passwords, KEKs, or decrypted keys
- Can cache encrypted data (it's safe)

**Concurrent access**:
- Multiple users can access same secret simultaneously (read-only)
- Granting access requires transaction isolation to prevent race conditions

---

## Session-Based KEK Storage Pattern (UX Optimization)

### The Performance Problem

Argon2id key derivation takes 100-500ms per operation. Every password-based call (`createSecret`, `accessSecret`, `grantAccess`) triggers a full KDF cycle, creating noticeable latency when users perform multiple operations.

### The Solution: Derive Once, Store in Session

The implementation derives the KEK once at login and stores it in the HTTP session (server-side, encrypted via HTTPS):

**How it works:**
1. `KekDerivationFilter` intercepts login POST, extracts password, stores in request attribute
2. `Active.handleAuthenticationSuccess()` listener fires after successful authentication
3. KEK is derived via `service.deriveKEK(userId, password)` and stored in session
4. Controllers retrieve KEK from session using `session.getUserKek()`
5. On logout, KEK is cleared from session

**Key classes:**
- `KekDerivationFilter` (Active.kt:12-38): Captures password from login POST
- `Active.deriveAndStoreKek()` (Active.kt:85-103): Derives and stores KEK after authentication
- `HttpSession.getUserKek()` (KekDerivationFilter.kt:40-41): Extension function to retrieve KEK

### Method Overloads

All operations have both password-based and KEK-based variants:

```kotlin
// Password-based: derives KEK internally (~200ms)
fun createSecret(userId: Long, password: String, name: String, value: String): UUID

// KEK-based: uses pre-derived KEK (~1ms)
fun createSecret(userId: Long, kek: ByteArray, name: String, value: String): UUID
```

**Available KEK overloads:**
- `createSecret(userId, kek, name, value)` → Returns UUID
- `createSecretEntity(userId, kek, name, value)` → Returns SharedSecret entity
- `accessSecret(userId, kek, secretId)` → Returns decrypted string
- `grantAccess(secretId, granterUserId, granterKEK, granteeUserId)`

### Usage in Controllers

```kotlin
@PostMapping("/secrets")
fun createSecret(request: CreateSecretRequest, session: HttpSession): UUID {
    val kek = session.getUserKek()  // Fast retrieval
    return service.createSecret(userId, kek, request.name, request.value)
}
```

### Security Considerations

**Threat: Session hijacking**
- Attacker with stolen session cookie has KEK access until timeout
- **Mitigations**: HTTPS only, short session timeout (15-30 min), `HttpOnly` + `SameSite=Strict` cookies, Spring Session JDBC with encrypted storage

**Trade-off:**

| Aspect | Password-per-Operation | Session KEK |
|--------|----------------------|-------------|
| UX | 100-500ms per op | <1ms after login |
| Security | Password never stored | KEK in session (encrypted) |
| Hijacking risk | Limited (need password) | Full access until timeout |

**When to use each:**
- **Password-per-operation**: High-security admin operations, destructive actions requiring confirmation
- **Session KEK**: Normal dashboard operations, frequent access patterns

### Performance Impact

**Before:** Login (200ms) + 5 secret accesses (5×200ms) = **1200ms**
**After:** Login (200ms) + 5 secret accesses (5×<1ms) = **~205ms**
**Improvement: ~6x faster**

---

## References

### Cryptographic Standards

- **Argon2**: [RFC 9106](https://datatracker.ietf.org/doc/html/rfc9106)
- **AES-GCM**: [NIST SP 800-38D](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- **X25519**: [RFC 7748](https://www.rfc-editor.org/rfc/rfc7748)
- **Key Derivation**: [NIST SP 800-132](https://csrc.nist.gov/publications/detail/sp/800-132/final)

### Similar Implementations

- **Signal**: Uses X3DH key agreement protocol (X25519-based)
- **WireGuard**: Uses X25519 for key exchange
- **1Password Teams**: Uses SRP + RSA for vault sharing
- **Bitwarden**: Uses RSA-2048 for organization sharing
- **ProtonMail**: Uses PGP-based key exchange

### Best Practices

- **OWASP Key Management Cheat Sheet**: [Link](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- **NIST Password Guidelines**: [SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html)
- **Latacora Cryptographic Right Answers**: [Blog post](https://latacora.micro.blog/2018/04/03/cryptographic-right-answers.html)

---

## Appendix: Algorithm Choices

### Why Argon2id over PBKDF2 or bcrypt?

- More resistant to GPU/ASIC attacks (memory-hard)
- Configurable time and memory costs
- Winner of Password Hashing Competition (2015)
- Recommended by OWASP and cryptography experts

### Why AES-GCM over AES-CBC?

- Authenticated encryption (prevents tampering)
- No padding oracle attacks
- Faster than separate encryption + MAC
- Industry standard for modern applications

### Why X25519 (Elliptic Curve) over RSA?

- **Performance**: 10-20x faster than RSA-2048 for key operations
- **Key size**: 32 bytes vs 256+ bytes for RSA (easier storage, faster transmission)
- **Security**: 128-bit equivalent security (same as RSA-2048)
- **Modern standard**: Used in Signal, WireGuard, TLS 1.3
- **Constant-time operations**: Resistant to timing attacks by design
- **Mature**: Well-vetted, standardized in RFC 7748

### Why Two-Layer Encryption (DEK + KEK)?

- Separates concerns: user authentication vs data encryption
- Enables efficient multi-user access (shared DEK, individual KEKs)
- Allows key rotation without re-encrypting all data
- Standard pattern in enterprise key management (AWS KMS, Google KMS, etc.)

---

## Glossary

- **DEK (Data Encryption Key)**: Symmetric key used to encrypt the actual secret
- **KEK (Key Encryption Key)**: Symmetric key derived from password, used to encrypt private key
- **KDF (Key Derivation Function)**: Algorithm to derive cryptographic key from password
- **Salt**: Random value added to KDF to ensure unique outputs
- **IV (Initialization Vector)**: Random value for each encryption to ensure unique ciphertexts
- **Nonce**: Same as IV in the context of AES-GCM
- **X25519**: Elliptic curve Diffie-Hellman key agreement protocol using Curve25519
- **Key Agreement**: Deriving a shared secret from two key pairs without directly transmitting keys
- **GCM**: Galois/Counter Mode, an authenticated encryption mode for AES
- **Zero-knowledge**: Server cannot access plaintext data even if it wanted to

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-13  
**Author**: Implementation Guide for Multi-User Secret Sharing System