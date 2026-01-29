# Basic Auth Login (BAL) - Authentication Pattern

A universal authentication pattern that converts Basic Authentication credentials into secure session-based authentication with automatic redirect.

**Version:** 1.0.0
**Last Updated:** 2026-01-29

---

## Table of Contents

1. [Overview](#overview)
2. [Why Use BAL?](#why-use-bal)
3. [How It Works](#how-it-works)
4. [URL Pattern](#url-pattern)
5. [Usage Examples](#usage-examples)
6. [Security](#security)
7. [Integration Patterns](#integration-patterns)

---

## Overview

The Basic Auth Login (BAL) endpoint provides a universal way for external systems to generate authenticated links that automatically log users into ELIM and redirect them to their target destination.

**Endpoint:** `GET /bal/{target-path}`

**Purpose:** Convert Basic Authentication credentials into secure session-based authentication, enabling:
- Single-click access to pre-filled forms
- Proper session management with logout support
- Secure credential handling

---

## Why Use BAL?

### The Problem with Direct Basic Auth URLs

External systems often want to provide direct links to authenticated resources:

```
http://username:password@host/elimplus/Rsv/?m=memento123
```

However, Basic Authentication has fundamental limitations:
- **No logout**: Browser caches credentials indefinitely
- **Security risks**: Credentials sent with every request
- **Poor UX**: No visible logout button, confusion about session state

### The BAL Solution

BAL converts Basic Auth into a proper session:

```
http://username:password@host/bal/elimplus/Rsv/?m=memento123
         ↓ BAL endpoint authenticates user
         ↓ Creates secure session
         ↓ Redirects to target
http://host/elimplus/Rsv/?m=memento123
     (user now has session cookie, no credentials in URL)
```

**Benefits:**
✅ Users get proper sessions with logout support
✅ Credentials only sent once during initial authentication
✅ Standard web application security model
✅ Compatible with existing Basic Auth integration patterns

---

## How It Works

### Request Flow

```
1. External System creates authenticated URL:
   https://user:pass@elim.example.com/bal/elimplus/Rsv/?m=memento123

2. User clicks link → Browser sends GET request to /bal/elimplus/Rsv/?m=memento123
   with Authorization: Basic <base64(user:pass)> header

3. BAL endpoint:
   a. Extracts credentials from Authorization header
   b. Authenticates user via Spring Security
   c. Creates session-based authentication
   d. Stores authentication in HTTP session

4. Redirects to target:
   302 Redirect → /elimplus/Rsv/?m=memento123

5. Browser follows redirect with session cookie (no more Basic Auth)

6. User sees target page, fully authenticated with session
```

### Authentication Lifecycle

- **Initial request**: Basic Auth credentials validated
- **Session creation**: Spring Security session established
- **Subsequent requests**: Session cookie used (no credentials)
- **Logout**: Standard logout flow available

---

## URL Pattern

### Syntax

```
/bal/{target-path}?{query-parameters}
```

Where:
- `/bal/` - BAL endpoint prefix
- `{target-path}` - Internal path to redirect to (everything after `/bal/`)
- `{query-parameters}` - Preserved in redirect

### Path Extraction

| Original URL | Target Path | Final Redirect |
|--------------|-------------|----------------|
| `/bal/elimplus/Rsv` | `/elimplus/Rsv` | `GET /elimplus/Rsv` |
| `/bal/elimplus/Rsv/?m=abc123` | `/elimplus/Rsv/?m=abc123` | `GET /elimplus/Rsv/?m=abc123` |
| `/bal/admin/users?page=2` | `/admin/users?page=2` | `GET /admin/users?page=2` |
| `/bal` | `/` | `GET /` |

### Security Validations

The target URL is validated to prevent attacks:

| Check | Purpose | Example Blocked |
|-------|---------|----------------|
| Must start with `/` | Prevent external redirects | `http://evil.com` ❌ |
| Cannot start with `//` | Prevent protocol-relative URLs | `//evil.com/path` ❌ |
| Cannot contain `..` | Prevent path traversal | `/bal/../../../etc/passwd` ❌ |
| Cannot start with `/bal` | Prevent infinite loops | `/bal/bal/bal/...` ❌ |

---

## Usage Examples

### Example 1: ELIM+ Pre-filled Form Access

**Scenario:** Laboratory system wants to give technicians direct access to pre-filled disease reporting forms.

```bash
#!/bin/bash
# External laboratory system script

HOST="elim.example.com"
END_USER="lab-tech"
END_USER_PASSWORD="tech-secret"
API_USER="lab-api"
API_PASSWORD="api-secret"

# Step 1: Create memento via API
MEMENTO=$(curl -s -X POST \
  -u "$API_USER:$API_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "reportId": "LAB-2024-00123",
    "Krankheit": {"Influenza": {}},
    "Patient": {
      "IsAnonym": false,
      "Standard": {
        "Name": {"Vorname": "Max", "Nachname": "Mustermann"},
        "Geburtsdatum": "1980-05-15"
      }
    }
  }' \
  "https://$HOST/api/elimplus/v1/memento" | jq -r '.memento')

# Step 2: Construct BAL URL for end user
FORM_URL="https://$END_USER:$END_USER_PASSWORD@$HOST/bal/elimplus/Influenza/?m=$MEMENTO"

# Step 3: Send to user (email, portal, etc.)
echo "Please review and submit this report:"
echo "$FORM_URL"
```

**What happens:**
1. User clicks link
2. BAL authenticates with `lab-tech:tech-secret`
3. Creates session for `lab-tech` user
4. Redirects to `/elimplus/Influenza/?m={memento}`
5. User sees pre-filled Influenza form
6. User reviews and submits to DEMIS

### Example 2: Direct curl Access (Testing)

```bash
# Authenticate and access protected resource
curl -u "username:password" \
  -L \
  "https://elim.example.com/bal/elimplus/Rsv/?m=memento456"

# -L flag follows redirects
# First request: BAL authenticates
# Second request: Follows redirect with session cookie
```

### Example 3: Batch Link Generation

```bash
#!/bin/bash
# Generate BAL links for multiple reports

BASE_URL="https://elim.example.com"
USER="tech-user"
PASS="tech-pass"

# Read CSV with lab results
while IFS=',' read -r report_id disease firstname lastname dob; do
  # Create memento (simplified)
  MEMENTO=$(create_memento "$report_id" "$disease" "$firstname" "$lastname" "$dob")

  # Generate BAL URL
  FORM_URL="https://$USER:$PASS@$BASE_URL/bal/elimplus/$disease/?m=$MEMENTO"

  echo "$report_id,$FORM_URL"
done < lab_results.csv > form_links.csv
```

### Example 4: Email Notification with BAL Link

```bash
#!/bin/bash
# Send email with authenticated form link

TO="technician@hospital.com"
FORM_URL="https://tech:secret@elim.example.com/bal/elimplus/Norovirus/?m=abc123"

mail -s "Laboratory Report Ready for Review (LAB-2024-789)" "$TO" <<EOF
Hello,

A laboratory report is ready for your review and submission to DEMIS.

Click here to access the pre-filled form:
$FORM_URL

The form has been pre-filled with laboratory data. Please review for accuracy
and submit to the health authority.

Note: You will be automatically logged in when you click the link.

---
Laboratory Information System
EOF
```

---

## Security

### Credential Handling

**✅ Secure practices:**
- Credentials only transmitted in initial request
- HTTPS required in production (credentials never in plain text)
- Session cookies are HttpOnly and Secure
- Credentials never logged or stored

**❌ Avoid:**
- Don't include credentials in query parameters (use Authorization header)
- Don't reuse credentials across multiple users
- Don't share BAL URLs publicly (contain credentials)

### Target URL Validation

BAL validates all target URLs to prevent:

1. **Open redirects:**
   ```
   /bal//evil.com/phishing  ❌ Blocked
   ```

2. **Path traversal:**
   ```
   /bal/../../../etc/passwd  ❌ Blocked
   ```

3. **Infinite loops:**
   ```
   /bal/bal/bal/target  ❌ Blocked
   ```

### Session Security

- **Session fixation protection**: New session ID generated after authentication
- **Session timeout**: Configured server-side (typically 30 minutes idle)
- **Logout support**: Users can explicitly log out via `/logout`
- **CSRF protection**: Enabled for all state-changing operations

### Production Recommendations

1. **Use HTTPS**: Always use HTTPS in production to protect credentials
2. **Strong passwords**: Enforce strong password policies for end users
3. **Separate credentials**: Use different credentials for API users vs end users
4. **Monitor access**: Log authentication attempts and target URLs
5. **Rate limiting**: Implement rate limiting to prevent brute force attacks

---

## Integration Patterns

### Pattern 1: API-Generated + BAL Access (ELIM+)

**Use case:** External system creates data via API, users access via browser

```
External System
    ↓
[1] POST /api/elimplus/v1/memento → memento string
    ↓
[2] Construct: https://user:pass@host/bal/elimplus/Disease/?m={memento}
    ↓
[3] Send URL to end user (email, portal, etc.)
    ↓
End User clicks link
    ↓
[4] GET /bal/elimplus/Disease/?m={memento} with Basic Auth
    ↓ BAL authenticates and creates session
    ↓
[5] 302 Redirect → /elimplus/Disease/?m={memento}
    ↓
[6] User sees pre-filled form with session cookie
```

### Pattern 2: Direct Resource Access

**Use case:** External portal provides links to ELIM resources

```
External Portal
    ↓
Generates link: https://user:pass@host/bal/admin/reports
    ↓
User clicks in portal
    ↓
BAL authenticates → redirects to /admin/reports
    ↓
User browses ELIM with active session
```

### Pattern 3: Bookmarkable Forms (Development/Testing)

**Use case:** Developers/testers need quick access to specific forms

```
Developer creates bookmark:
https://test-user:test-pass@dev.elim.example.com/bal/elimplus/Rsv

Click bookmark → instant authenticated access to RSV form
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause:** Invalid credentials

**Solution:**
- Verify username and password are correct
- Check if user account is active
- Ensure credentials are properly URL-encoded in the URL

### Issue: 302 Redirect Loop

**Cause:** Target URL starts with `/bal`

**Solution:**
- Remove `/bal` prefix from target path
- Correct: `/bal/elimplus/Rsv`
- Incorrect: `/bal/bal/elimplus/Rsv`

### Issue: Credentials Visible in Browser

**Cause:** Basic Auth credentials may appear in browser's address bar

**Solution:**
- This is expected for the initial request
- After redirect, credentials are gone (session cookie used)
- Consider generating short-lived links or one-time tokens if this is a concern

### Issue: Cannot Logout

**Cause:** Browser caches Basic Auth credentials

**Solution:**
- BAL automatically converts to session-based auth on first access
- Users can then use standard `/logout` endpoint
- Initial Basic Auth credentials only used for BAL request

---

## FAQ

**Q: Is BAL secure for production use?**
A: Yes, when used with HTTPS. Credentials are only sent in the initial request and then converted to secure session-based authentication.

**Q: Can I use BAL for API endpoints?**
A: No, BAL is designed for browser-based access. For API endpoints, use Basic Auth directly with the API endpoint (e.g., `/api/elimplus/v1/memento`).

**Q: What happens if credentials are wrong?**
A: BAL returns a 401 Unauthorized response or redirects to `/login?error`.

**Q: Can I use BAL without credentials in the URL?**
A: Yes, send credentials in the `Authorization: Basic` header instead of embedding them in the URL.

**Q: Does BAL work with OAuth/OIDC?**
A: BAL specifically handles Basic Auth → session conversion. For OAuth/OIDC, use the standard OAuth login flow.

**Q: Can I customize the redirect behavior?**
A: The target path is extracted from the URL structure. To customize further, contact your administrator or see the source code.

---

## Related Documentation

- [ELIM+ API Integration Guide](../Products/ELIMPLUS/api-tutorial.md) - Complete API workflow including BAL usage
- [ELIM+ OpenAPI Specification](../Products/ELIMPLUS/api.yml) - API endpoint details

---

*This is external-facing documentation for integration partners. For internal implementation details, see `src/main/java/de/vertama/web/BasicAuthLoginController.kt` in the elim repository.*
