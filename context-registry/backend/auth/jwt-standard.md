# JWT Token Standards

Standards and guidelines for implementing JWT (JSON Web Token) authentication in backend services.

## Overview

JWT is the standard token format for stateless authentication across all backend services. This document defines organization-wide standards for JWT implementation.

## Token Structure

### Standard Claims

All JWTs must include these standard claims:

```json
{
  "iss": "https://auth.company.com",
  "sub": "user-uuid-here",
  "aud": "backend-api",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique-token-id"
}
```

**Required Claims:**
- `iss` (Issuer): Authentication server URL
- `sub` (Subject): User identifier (UUID format)
- `aud` (Audience): Intended recipient service
- `exp` (Expiration): Unix timestamp
- `iat` (Issued At): Unix timestamp
- `jti` (JWT ID): Unique token identifier

### Custom Claims

Include application-specific claims in the `user_claims` object:

```json
{
  "user_claims": {
    "email": "user@company.com",
    "roles": ["admin", "developer"],
    "permissions": ["read:users", "write:users"],
    "department": "engineering",
    "employee_id": "EMP-001"
  }
}
```

## Token Lifetime

### Access Tokens
- **Lifetime**: 15 minutes
- **Use**: API authentication
- **Storage**: Memory only (never localStorage)

### Refresh Tokens
- **Lifetime**: 7 days
- **Use**: Obtaining new access tokens
- **Storage**: Secure HTTP-only cookie
- **Rotation**: Issue new refresh token on each use

## Implementation Guidelines

### Token Validation

All services must validate:
1. Signature using public key from JWKS endpoint
2. Expiration time (`exp` claim)
3. Issuer (`iss` claim matches expected value)
4. Audience (`aud` claim includes this service)
5. Not before time if present (`nbf` claim)

### Python Example

```python
import jwt
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization

def create_token(user_id: str, roles: list) -> str:
    payload = {
        "iss": "https://auth.company.com",
        "sub": user_id,
        "aud": "backend-api",
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "iat": datetime.utcnow(),
        "user_claims": {
            "roles": roles
        }
    }
    
    return jwt.encode(payload, private_key, algorithm="RS256")

def verify_token(token: str) -> dict:
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience="backend-api",
        issuer="https://auth.company.com"
    )
```

## Security Requirements

### Algorithm

- **Required**: RS256 (RSA Signature with SHA-256)
- **Forbidden**: HS256, none algorithm

**Rationale**: Asymmetric signatures prevent token forgery even if services are compromised.

### Key Management

- Private keys: Stored in HSM or secure key vault
- Public keys: Distributed via JWKS endpoint
- Key rotation: Every 90 days
- Support 2 active keys during rotation period

### Transport Security

- Tokens must only be transmitted over HTTPS
- Include in `Authorization` header: `Bearer <token>`
- Never include in URL query parameters or request body

## Error Handling

### Standard Error Responses

```json
{
  "error": "invalid_token",
  "error_description": "Token has expired",
  "error_code": "TOKEN_EXPIRED"
}
```

**Error Codes:**
- `TOKEN_EXPIRED`: Token exp claim is in the past
- `TOKEN_INVALID`: Signature validation failed
- `TOKEN_MALFORMED`: Token structure is invalid
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions

## Testing

### Test Token Generation

For development and testing only:

```python
# DO NOT USE IN PRODUCTION
def create_test_token():
    return jwt.encode(
        {
            "sub": "test-user",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "user_claims": {"roles": ["admin"]}
        },
        "test-secret",
        algorithm="HS256"
    )
```

### Validation Tests

Test cases to implement:
1. Valid token is accepted
2. Expired token is rejected
3. Invalid signature is rejected
4. Missing required claims is rejected
5. Wrong audience is rejected
