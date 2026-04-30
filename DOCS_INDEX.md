# TableManager Backend - Documentation Index

## Core Documentation

### [QUICKSTART.md](QUICKSTART.md)
Fastest way to get up and running. Follow step-by-step instructions to install dependencies, configure the database, and start the server.

### [BACKEND_PLAN.md](BACKEND_PLAN.md)
Complete technical architecture plan including database schema, API endpoints, security model, and project structure.

### [API_USAGE.md](API_USAGE.md)
Detailed API reference with endpoint descriptions, request/response examples, cURL commands, and authentication guide.

### [ENVIRONMENT_VARS.md](ENVIRONMENT_VARS.md)
Complete reference of all environment variables, their defaults, descriptions, and security best practices.

### [DEPLOYMENT.md](DEPLOYMENT.md)
Production deployment guide covering Docker, Systemd, Nginx, SSL, scaling, monitoring, and security hardening.

## Quick Links

### Repository Structure
```
tableManager/
├── app/                      # FastAPI application
│   ├── main.py              # App entry point
│   ├── config.py            # Configuration
│   ├── database.py          # DB session & engine
│   ├── models/              # SQLAlchemy models (User, Product)
│   ├── schemas/             # Pydantic schemas
│   ├── api/v1/endpoints/    # API routes (auth, users, products)
│   ├── core/                # Auth & file upload utilities
│   └── utils/               # Helper functions
├── alembic/                 # Database migrations
├── uploads/                 # Uploaded files storage
├── requirements.txt         # Python dependencies
├── .env                    # Configuration (create from .env.example)
├── docker-compose.yml       # Docker setup
└── Dockerfile              # Container image
```

### Main API Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/auth/register` | POST | Register new user | Public |
| `/auth/login` | POST | Login & get tokens | Public |
| `/users/me` | GET | Get current user | Required |
| `/users/me` | PUT | Update profile | Required |
| `/users/me/avatar` | POST | Upload avatar | Required |
| `/users/{id}` | GET | Get public profile | Public |
| `/products/` | GET | List products | Public |
| `/products/` | POST | Create product | Admin |
| `/products/{id}` | PUT | Update product | Admin |
| `/products/{id}` | DELETE | Delete product | Admin |
| `/products/{id}/image` | POST | Upload image | Admin |

### Quick Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload

# Docker
docker-compose up

# Create admin user
python create_admin.py

# Validate setup
python setup_check.py

# Test API
python test_api.py
```

### Files Created

#### Source Code
- `app/main.py` - FastAPI application
- `app/config.py` - Settings from environment
- `app/database.py` - SQLAlchemy setup
- `app/models/user.py` - User model
- `app/models/product.py` - Product model
- `app/schemas/user.py` - User schemas
- `app/schemas/product.py` - Product schemas
- `app/core/security.py` - JWT & password utils
- `app/core/uploads.py` - File upload handling
- `app/api/v1/endpoints/auth.py` - Auth routes
- `app/api/v1/endpoints/users.py` - User routes
- `app/api/v1/endpoints/products.py` - Product routes

#### Configuration
- `requirements.txt` - Python dependencies
- `.env.example` - Configuration template
- `.env` - Your configuration
- `alembic.ini` - Migration config
- `alembic/env.py` - Migration env
- `alembic/versions/001_initial_migration.py` - Initial DB schema

#### Operations
- `setup.sh` / `setup.bat` - Automated setup
- `setup_check.py` - Health check script
- `test_api.py` - API test suite

#### Documentation
- `README.md` - Project overview
- `QUICKSTART.md` - Get started guide
- `BACKEND_PLAN.md` - Architecture plan
- `API_USAGE.md` - API reference
- `ENVIRONMENT_VARS.md` - Configuration reference
- `DEPLOYMENT.md` - Production deployment

#### Deployment
- `Dockerfile` - Container image
- `docker-compose.yml` - Docker Compose setup
- `.dockerignore` - Docker ignore rules

## Support

For issues or questions, check the documentation files above or create an issue in the repository.
