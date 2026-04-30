# Quick Start Guide

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12+ running locally or remotely
- pip package manager

## One-Command Setup (Linux/macOS)

```bash
# Clone/cd into project directory
cd tableManager

# Run setup script
chmod +x setup.sh && ./setup.sh
```

## Manual Setup

### Step 1: Install Python Dependencies

```bash
cd tableManager
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Database

Create a PostgreSQL database:
```sql
CREATE DATABASE tablemanager;
CREATE USER tableuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE tablemanager TO tableuser;
```

Update `.env` with your database URL:
```
DATABASE_URL=postgresql://tableuser:yourpassword@localhost/tablemanager
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `SECRET_KEY` in `.env`:
```
SECRET_KEY=generated-secret-key-here
```

### Step 3: Run Database Migrations

```bash
alembic upgrade head
```

### Step 4: Start Development Server

```bash
uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000

## Verify Installation

1. Open browser to http://localhost:8000/docs
2. Try the `/health` endpoint: `curl http://localhost:8000/health`
3. You should see: `{"status":"healthy"}`

## Create Your First Admin User

```python
import sqlalchemy as sa
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = User(
    email="admin@example.com",
    username="admin",
    hashed_password=get_password_hash("your-secure-password"),
    is_active=True,
    is_admin=True
)
db.add(admin)
db.commit()
db.close()
print("Admin user created!")
```

Or register via API at http://localhost:8000/docs (use `/auth/register` endpoint)

## Common Issues

### Database Connection Error
- Ensure PostgreSQL is running: `sudo service postgresql start`
- Check credentials in `.env`
- Verify database exists

### Port Already in Use
Change port: `uvicorn app.main:app --reload --port 8001`

### Module Not Found Errors
- Ensure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

### Upload Directory Errors
- Ensure write permissions: `chmod 755 uploads/`

## Production Deployment

### Using Gunicorn with Uvicorn Workers

```bash
pip install gunicorn
gunicorn -k uvicorn.workers.UvicornWorker -w 4 app.main:app --bind 0.0.0.0:8000
```

### Environment Variables
Set production values:
```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
export DATABASE_URL=postgresql://user:pass@host:5432/proddb
export ALGORITHM=HS256
```

### Configure CORS
Update `app/main.py` to set specific allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

- Read [API Usage Guide](API_USAGE.md)
- Review [Environment Variables](ENVIRONMENT_VARS.md)
- Extend models/schemas for your specific needs
- Add email verification, password reset, rate limiting
- Write unit and integration tests
