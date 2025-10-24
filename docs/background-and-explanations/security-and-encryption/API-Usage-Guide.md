# Multi-User Secret Sharing - API Usage Guide

> **Audience**: Developers integrating with or consuming this API
> **Companion to**: [Multi-User Secret Sharing with Zero-Knowledge Architecture.md](Multi-User%20Secret%20Sharing%20with%20Zero-Knowledge%20Architecture.md)

This guide shows how to use the secret sharing service with practical code examples.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Operations](#core-operations)
3. [Advanced Usage](#advanced-usage)
4. [Error Handling](#error-handling)
5. [Security Best Practices](#security-best-practices)

---

## Quick Start

### Prerequisites

- User must have an `ApiUser` account with a valid `userId`
- User must have a password (never stored, only used for key derivation)

### Basic Flow

```kotlin
// 1. Setup (once per user)
service.setupUserKeys(userId = 1L, password = "user-password")

// 2. Create secret (by owner)
val secretId = service.createSecret(
    userId = 1L,
    password = "user-password",
    name = "Database Credentials",
    value = "postgresql://user:pass@host:5432/db"
)

// 3. Access secret (by owner or granted user)
val decrypted = service.accessSecret(
    userId = 1L,
    password = "user-password",
    secretId = secretId
)

println(decrypted) // "postgresql://user:pass@host:5432/db"
```

---

## Core Operations

### 1. Setup User Keys

**When**: Once per user, before they can create or access secrets

**What it does**: Generates X25519 key pair, encrypts private key with password-derived key

```kotlin
service.setupUserKeys(
    userId = 123L,
    password = "user-chosen-password"
)
```

**Returns**: Nothing (throws exception on error)

**Errors**:
- `IllegalStateException`: User already has keys (call once only)

**Notes**:
- Password is **never stored**
- Server derives encryption key from password using Argon2id
- Private key is encrypted and stored; public key stored in plaintext
- If user forgets password, all their secrets are **permanently lost**

---

### 2. Create Secret

**When**: User wants to store encrypted data

**What it does**: Encrypts secret with random DEK, encrypts DEK with user's public key

```kotlin
// Option A: With password (derives KEK, ~200ms)
val secretId: UUID = service.createSecret(
    userId = 123L,
    password = "user-password",
    name = "API Key",
    value = "sk_live_abc123xyz789"
)

// Option B: With pre-derived KEK from session (~1ms)
val kek = session.getUserKek()
val secretId: UUID = service.createSecret(
    userId = 123L,
    kek = kek,
    name = "API Key",
    value = "sk_live_abc123xyz789"
)
```

**Parameters**:
- `userId`: User creating the secret
- `password` OR `kek`: Authentication credential
- `name`: Human-readable label (stored in plaintext)
- `value`: Secret data to encrypt (any string)

**Returns**: `UUID` - unique identifier for the secret

**Errors**:
- `SecurityException`: Wrong password or user has no keys

**Notes**:
- Only the creator has access initially
- Creator must use `grantAccess()` to share with others

---

### 3. Access Secret

**When**: User wants to decrypt and read a secret

**What it does**: Decrypts user's private key, decrypts DEK, decrypts secret

```kotlin
// With password
val decrypted: String = service.accessSecret(
    userId = 123L,
    password = "user-password",
    secretId = UUID.fromString("...")
)

// With KEK from session (faster)
val kek = session.getUserKek()
val decrypted: String = service.accessSecret(
    userId = 123L,
    kek = kek,
    secretId = UUID.fromString("...")
)
```

**Parameters**:
- `userId`: User accessing the secret
- `password` OR `kek`: Authentication credential
- `secretId`: UUID of the secret

**Returns**: Decrypted secret value (plaintext string)

**Errors**:
- `SecurityException`: Wrong password, no access, or secret not found

**Notes**:
- User must have been granted access (creator has implicit access)
- Password must be correct (no retry logic built-in)

---

### 4. Grant Access

**When**: User wants to share a secret with another user

**What it does**: Re-encrypts DEK with grantee's public key

```kotlin
service.grantAccess(
    secretId = UUID.fromString("..."),
    granterUserId = 123L,
    granterPassword = "granter-password",
    granteeUserId = 456L
)
```

**Parameters**:
- `secretId`: Secret to share
- `granterUserId`: User granting access (must already have access)
- `granterPassword`: Granter's password (to decrypt DEK)
- `granteeUserId`: User receiving access

**Returns**: Nothing (throws exception on error)

**Errors**:
- `SecurityException`: Granter doesn't have access, wrong password, or grantee has no keys

**Key insights**:
- **Grantee doesn't need to be online** - only their public key is used
- **Grantee's password is never shared** - each user decrypts with their own password
- Granter needs their password to decrypt the DEK, then re-encrypts it for grantee

---

### 5. Revoke Access

**When**: User wants to remove another user's access

**What it does**: Deletes user's encrypted DEK entry

```kotlin
service.revokeAccess(
    secretId = UUID.fromString("..."),
    userId = 456L
)
```

**Parameters**:
- `secretId`: Secret to revoke access to
- `userId`: User to revoke access from

**Returns**: Nothing

**Limitations**:
- If user already decrypted and saved the secret, revocation doesn't affect saved copies
- No password required (administrative action)
- Cannot revoke creator's access (database constraint prevents it)

---

### 6. Rotate Password

**When**: User wants to change their password

**What it does**: Re-encrypts private key with new password-derived key

```kotlin
service.rotateUserPassword(
    userId = 123L,
    oldPassword = "current-password",
    newPassword = "new-secure-password"
)
```

**Parameters**:
- `userId`: User changing password
- `oldPassword`: Current password (must be correct)
- `newPassword`: New password to set

**Returns**: Nothing (throws exception on error)

**Errors**:
- `SecurityException`: Wrong old password

**Notes**:
- All secrets remain accessible with new password
- Private key (and thus DEKs) stay the same, just re-encrypted
- Old password is immediately invalidated

---

## Advanced Usage

### Multi-User Workflow

```kotlin
// Alice creates secret
service.setupUserKeys(userId = alice.id, password = "alice-pass")
val secretId = service.createSecret(
    userId = alice.id,
    password = "alice-pass",
    name = "Shared Database",
    value = "prod-db-credentials"
)

// Bob sets up keys
service.setupUserKeys(userId = bob.id, password = "bob-pass")

// Alice grants Bob access (Bob doesn't need to be online!)
service.grantAccess(
    secretId = secretId,
    granterUserId = alice.id,
    granterPassword = "alice-pass",
    granteeUserId = bob.id
)

// Bob accesses with his own password
val decrypted = service.accessSecret(
    userId = bob.id,
    password = "bob-pass",  // Not Alice's password!
    secretId = secretId
)
```

### Checking Access Before Granting

```kotlin
// Repository method available
val hasAccess = accessRepo.existsBySecretIdAndUserId(secretId, userId)
if (!hasAccess) {
    service.grantAccess(...)
}
```

### Listing User's Secrets

```kotlin
val userAccess: List<UserSecretAccess> = accessRepo.findByUserId(userId)
userAccess.forEach { access ->
    println("Secret: ${access.secret.name}")
    println("Granted by: ${access.grantedBy.name}")
    println("Granted at: ${access.grantedAt}")
}
```

### Listing Users With Access to Secret

```kotlin
val accessList: List<UserSecretAccess> = accessRepo.findBySecretId(secretId)
accessList.forEach { access ->
    println("User: ${access.user.name}")
    println("Granted by: ${access.grantedBy.name}")
}
```

---

## Error Handling

### SecurityException

Most operations throw `SecurityException` on auth failures:

```kotlin
try {
    val secret = service.accessSecret(userId, password, secretId)
} catch (e: SecurityException) {
    when {
        e.message?.contains("Wrong password") == true ->
            // Password incorrect
        e.message?.contains("has no access") == true ->
            // User not granted access
        e.message?.contains("has no crypto keys") == true ->
            // User hasn't called setupUserKeys()
        else ->
            // Other security error
    }
}
```

### IllegalStateException

```kotlin
try {
    service.setupUserKeys(userId, password)
} catch (e: IllegalStateException) {
    // User already has keys - cannot call twice
}
```

### Recommended Error Handling Pattern

```kotlin
fun accessSecretSafely(userId: Long, password: String, secretId: UUID): Result<String> {
    return try {
        Result.success(service.accessSecret(userId, password, secretId))
    } catch (e: SecurityException) {
        Result.failure(e)
    }
}

// Usage
accessSecretSafely(userId, password, secretId)
    .onSuccess { secret -> println("Decrypted: $secret") }
    .onFailure { error -> logger.error("Access failed: ${error.message}") }
```

---

## Security Best Practices

### 1. Password Handling

❌ **Don't**:
```kotlin
// Never store passwords
data class User(val password: String)  // BAD!

// Never log passwords
logger.info("User password: $password")  // BAD!
```

✅ **Do**:
```kotlin
// Accept password as parameter, use immediately, discard
fun login(username: String, password: String) {
    service.accessSecret(userId, password, secretId)
    // password garbage-collected after function returns
}

// Use char arrays for passwords (can be cleared)
fun login(username: String, password: CharArray) {
    try {
        val passwordStr = String(password)
        service.accessSecret(userId, passwordStr, secretId)
    } finally {
        password.fill('0')  // Clear password from memory
    }
}
```

### 2. Access Control

```kotlin
// Check user owns or has access before operations
fun userCanAccess(userId: Long, secretId: UUID): Boolean {
    return accessRepo.existsBySecretIdAndUserId(secretId, userId)
}

// Verify before granting (prevent over-sharing)
fun grantIfNotAlready(secretId: UUID, granterUserId: Long, ...) {
    if (!userCanAccess(granteeUserId, secretId)) {
        service.grantAccess(...)
    }
}
```

### 3. Error Messages

❌ **Don't leak information**:
```kotlin
catch (e: SecurityException) {
    // Reveals whether user exists
    return "User $userId doesn't have crypto keys"
}
```

✅ **Use generic messages**:
```kotlin
catch (e: SecurityException) {
    logger.warn("Access denied for user $userId", e)
    return "Access denied"  // Generic message to client
}
```

### 4. Rate Limiting

Implement rate limiting to prevent brute-force attacks:

```kotlin
@RateLimited(maxAttempts = 5, windowSeconds = 60)
fun accessSecret(userId: Long, password: String, secretId: UUID): String {
    return service.accessSecret(userId, password, secretId)
}
```

### 5. Audit Logging

Log all access operations (but not passwords or secrets):

```kotlin
fun accessSecret(userId: Long, password: String, secretId: UUID): String {
    val result = try {
        service.accessSecret(userId, password, secretId)
    } catch (e: SecurityException) {
        auditLog.warn("Failed secret access", mapOf(
            "userId" to userId,
            "secretId" to secretId,
            "reason" to e.message
        ))
        throw e
    }

    auditLog.info("Secret accessed", mapOf(
        "userId" to userId,
        "secretId" to secretId
    ))

    return result
}
```

### 6. Password Rotation Reminders

```kotlin
fun checkPasswordAge(userId: Long) {
    val keys = userKeysRepo.findById(userId).orElseThrow()
    val daysSinceCreation = ChronoUnit.DAYS.between(keys.createdAt, Instant.now())

    if (daysSinceCreation > 90) {
        notifyUser(userId, "Consider rotating your password")
    }
}
```

---

## Performance Considerations

### KDF Latency

Each password-based operation triggers Argon2id key derivation (~100-500ms). For better performance, use KEK-based method overloads with session-stored KEK:

```kotlin
// Slow: Derives KEK on every call
repeat(10) {
    service.accessSecret(userId, password, secretId)  // 10 × 200ms = 2000ms
}

// Fast: Derive KEK once, reuse from session
val kek = session.getUserKek()  // Already derived at login
repeat(10) {
    service.accessSecret(userId, kek, secretId)  // 10 × <1ms = ~10ms
}
```

**Recommendation**: Use session-based KEK for normal operations. Reserve password-based methods for high-security actions requiring explicit confirmation.

### Database Queries

Operations by query count:

- `setupUserKeys()`: 1 write
- `createSecret()`: 3 reads, 2 writes
- `accessSecret()`: 3 reads
- `grantAccess()`: 4 reads, 1 write
- `revokeAccess()`: 1 delete

**Recommendation**: Add indexes on `user_secret_access(secret_id, user_id)` for optimal performance.

---

## Integration Examples

### Spring MVC Controller

```kotlin
@RestController
@RequestMapping("/api/secrets")
class SecretController(
    private val service: Service,
    private val accessRepo: UserSecretAccessRepository
) {

    @PostMapping
    fun createSecret(
        @AuthenticationPrincipal user: ApiUser,
        @RequestParam password: String,
        @RequestBody request: CreateSecretRequest
    ): ResponseEntity<SecretResponse> {
        val secretId = service.createSecret(
            userId = user.id!!,
            password = password,
            name = request.name,
            value = request.value
        )

        return ResponseEntity.ok(SecretResponse(secretId))
    }

    @GetMapping("/{secretId}")
    fun getSecret(
        @AuthenticationPrincipal user: ApiUser,
        @PathVariable secretId: UUID,
        @RequestParam password: String
    ): ResponseEntity<String> {
        return try {
            val decrypted = service.accessSecret(user.id!!, password, secretId)
            ResponseEntity.ok(decrypted)
        } catch (e: SecurityException) {
            ResponseEntity.status(HttpStatus.FORBIDDEN).build()
        }
    }

    @PostMapping("/{secretId}/grant")
    fun grantAccess(
        @AuthenticationPrincipal user: ApiUser,
        @PathVariable secretId: UUID,
        @RequestParam password: String,
        @RequestParam granteeUserId: Long
    ): ResponseEntity<Void> {
        service.grantAccess(secretId, user.id!!, password, granteeUserId)
        return ResponseEntity.ok().build()
    }
}
```

### Thymeleaf Template

```html
<!-- Create secret form -->
<form th:action="@{/secrets}" method="post">
    <input type="text" name="name" placeholder="Secret name" required />
    <textarea name="value" placeholder="Secret value" required></textarea>
    <input type="password" name="password" placeholder="Your password" required />
    <button type="submit">Create Secret</button>
</form>

<!-- Access secret -->
<form th:action="@{/secrets/{id}/view(id=${secretId})}" method="post">
    <input type="password" name="password" placeholder="Your password" required />
    <button type="submit">Decrypt</button>
</form>

<!-- Display decrypted (be careful with XSS!) -->
<div th:if="${decrypted}">
    <pre th:text="${decrypted}"></pre>
</div>
```

---

## Troubleshooting

### "User has no crypto keys"

**Cause**: User hasn't called `setupUserKeys()` yet

**Fix**: Call `setupUserKeys()` once per user before other operations

### "Wrong password or corrupted private key"

**Cause**: Password is incorrect

**Fix**: Verify user entered correct password

**Note**: No password recovery possible - forgotten password = lost secrets

### "User has no access to secret"

**Cause**: User wasn't granted access

**Fix**: Secret creator must call `grantAccess()` first

### "User already has keys"

**Cause**: Called `setupUserKeys()` twice for same user

**Fix**: Only call once; use `rotateUserPassword()` to change password

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Related**:
- [Multi-User Secret Sharing with Zero-Knowledge Architecture.md](Multi-User%20Secret%20Sharing%20with%20Zero-Knowledge%20Architecture.md)
- [Implementation-Notes.md](Implementation-Notes.md)
