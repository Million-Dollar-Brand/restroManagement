# TableManager API

A FastAPI backend with PostgreSQL for a REST API service featuring user authentication, user management, and product catalog with file uploads.

## Features

- **User Authentication**: JWT-based auth with registration/login
- **User Management**: Profile updates, avatar uploads
- **Product Catalog**: Full CRUD with image uploads
- **File Uploads**: Secure upload handling with validation
- **PostgreSQL**: Robust relational data storage
- **Migrations**: Alembic for schema versioning

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- pip

### Installation

1. Clone and setup:
```bash
cd tableManager
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a PostgreSQL database:
```sql
CREATE DATABASE tablemanager;
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
tableManager/
├── app/                  # Main application package
│   ├── main.py          # FastAPI app
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── api/             # API endpoints
│   ├── core/            # Auth, security
│   └── utils/           # Helpers
├── alembic/             # Database migrations
├── uploads/             # Uploaded files
├── requirements.txt     # Dependencies
├── .env                # Configuration
└── README.md           # This file
```

## License

MIT
