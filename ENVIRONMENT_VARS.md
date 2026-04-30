# Environment Variables Reference

## Database Configuration

### `DATABASE_URL`
- **Description**: PostgreSQL connection string
- **Format**: `postgresql://username:password@host:port/database`
- **Default**: `postgresql://postgres:password@localhost/tablemanager`
- **Required**: Yes

Example:
```
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/tablemanager
```

## Security

### `SECRET_KEY`
- **Description**: Secret key for JWT token signing
- **Default**: Development key (NOT for production)
- **Required**: Yes
- **Production**: Generate a strong random secret

Generate secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### `ALGORITHM`
- **Description**: JWT signing algorithm
- **Default**: `HS256`
- **Options**: `HS256`, `RS256`, etc.
- **Required**: No (uses default if not set)

### `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Description**: How long access tokens are valid
- **Default**: `30` (30 minutes)
- **Required**: No

### `REFRESH_TOKEN_EXPIRE_DAYS`
- **Description**: How long refresh tokens are valid
- **Default**: `7` (7 days)
- **Required**: No

## File Uploads

### `UPLOAD_DIR`
- **Description**: Directory path for uploaded files
- **Default**: `uploads/`
- **Required**: No
- **Note**: Must be writable by the application

### `MAX_FILE_SIZE`
- **Description**: Maximum file size in bytes
- **Default**: `5242880` (5 MB)
- **Required**: No

### `ALLOWED_EXTENSIONS`
- **Description**: Comma-separated list of allowed file extensions
- **Default**: `jpg,jpeg,png,webp`
- **Required**: No

## Application

### `APP_NAME`
- **Description**: Application name shown in API docs
- **Default**: `TableManager API`
- **Required**: No

### `VERSION`
- **Description**: API version
- **Default**: `1.0.0`
- **Required**: No

## Complete .env Example

```bash
# Database
DATABASE_URL=postgresql://postgres:mysecurepassword@localhost:5432/tablemanager

# Security - CHANGE THESE!
SECRET_KEY=your-super-secret-key-at-least-32-characters-long-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Uploads
UPLOAD_DIR=uploads/
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp,gif

# Application
APP_NAME=TableManager API
VERSION=1.0.0
```

## Security Best Practices

1. **SECRET_KEY**: Must be at least 32 characters, randomly generated, never committed to version control
2. **DATABASE_URL**: Use connection pooling in production
3. **MAX_FILE_SIZE**: Adjust based on your needs
4. **Permissions**: Restrict write access to upload directory
5. **HTTPS**: Always use HTTPS in production
6. **CORS**: Configure `CORS_ORIGINS` in production (currently set to `*` for development)
