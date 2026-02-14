# Keycloak Setup Guide

Complete guide for setting up and configuring Keycloak as the authentication provider for backend services.

## Prerequisites

Before starting the installation, ensure you have:

- Java 17 or newer installed
- PostgreSQL 15+ database server
- Minimum 2GB RAM allocated for Keycloak
- Docker and Docker Compose (for containerized deployment)
- SSL certificates for production deployment

## Installation Methods

### Method 1: Docker Deployment (Recommended)

Docker deployment is the recommended approach for both development and production environments.

#### Step 1: Create Docker Compose File

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  keycloak:
    image: quay.io/keycloak/keycloak:latest
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak_password
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin_password
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    command: start-dev

volumes:
  postgres_data:
```

#### Step 2: Start Services

```bash
docker-compose up -d
```

#### Step 3: Access Admin Console

Navigate to `http://localhost:8080` and log in with:
- Username: `admin`
- Password: `admin_password`

### Method 2: Standalone Installation

For bare-metal or VM deployments:

1. Download Keycloak from official website
2. Extract to `/opt/keycloak`
3. Configure database connection in `conf/keycloak.conf`
4. Start with `bin/kc.sh start-dev`

## Configuration

### Creating a Realm

1. Access the admin console
2. Click "Create Realm" dropdown
3. Enter realm name (e.g., `company-realm`)
4. Click "Create"

### Setting Up a Client

1. Navigate to "Clients" in the sidebar
2. Click "Create client"
3. Configure:
   - **Client ID**: `backend-api`
   - **Client Protocol**: `openid-connect`
   - **Access Type**: `confidential`
   - **Valid Redirect URIs**: `http://localhost:3000/*`
   - **Web Origins**: `http://localhost:3000`

### Creating Users

1. Go to "Users" section
2. Click "Add user"
3. Fill in user details
4. Set credentials in "Credentials" tab
5. Assign roles in "Role Mappings" tab

## Integration with Backend Services

### JWT Token Validation

Backend services should validate JWT tokens issued by Keycloak:

```python
import jwt
from jwt import PyJWKClient

KEYCLOAK_URL = "http://localhost:8080"
REALM = "company-realm"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"

jwks_client = PyJWKClient(JWKS_URL)

def verify_token(token):
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    data = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience="backend-api",
        options={"verify_exp": True}
    )
    return data
```

### Client Credentials Flow

For service-to-service authentication:

```bash
curl -X POST \
  http://localhost:8080/realms/company-realm/protocol/openid-connect/token \
  -d "client_id=backend-api" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "grant_type=client_credentials"
```

## Security Best Practices

### Production Deployment

1. **Use HTTPS**: Always deploy Keycloak behind HTTPS in production
2. **Strong Passwords**: Enforce strong password policies
3. **Session Management**: Configure appropriate session timeouts
4. **CORS**: Properly configure CORS settings
5. **Rate Limiting**: Implement rate limiting on token endpoints

### Password Policies

Configure in Realm Settings → Security Defenses → Password Policy:
- Minimum length: 12 characters
- Must include uppercase, lowercase, numbers, special characters
- Password history: 5
- Expire after: 90 days

## Troubleshooting

### Common Issues

#### Issue: Cannot Connect to Database

**Solution**: Verify database connection string and credentials in `keycloak.conf`:
```
db=postgres
db-url=jdbc:postgresql://localhost/keycloak
db-username=keycloak
db-password=keycloak_password
```

#### Issue: Token Validation Fails

**Solution**: Check that:
- JWKS URL is accessible
- Token hasn't expired
- Audience matches client ID
- Clock skew is within acceptable range (±5 minutes)

#### Issue: Slow Performance

**Solution**:
- Increase heap size: `JAVA_OPTS="-Xms1024m -Xmx2048m"`
- Enable database connection pooling
- Use caching for frequently accessed data

## Monitoring and Maintenance

### Health Checks

Monitor Keycloak health:
```bash
curl http://localhost:8080/health
```

### Backup

Regular backup of PostgreSQL database:
```bash
docker exec postgres pg_dump -U keycloak keycloak > keycloak_backup.sql
```

### Updates

Always test updates in staging before production:
1. Backup database
2. Pull latest Keycloak image
3. Test thoroughly
4. Deploy to production

## References

- Official Keycloak Documentation: https://www.keycloak.org/documentation
- Server Administration Guide: https://www.keycloak.org/docs/latest/server_admin/
- Securing Applications: https://www.keycloak.org/docs/latest/securing_apps/
