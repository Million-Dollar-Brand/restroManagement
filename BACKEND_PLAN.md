# FastAPI Backend Project Plan

## Project Structure
```
tableManager/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app initialization
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection & session
│   ├── models/           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── api/              # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   └── products.py
│   │   │   └── router.py
│   ├── core/             # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py   # Password hashing, JWT
│   │   └── uploads.py    # File upload handling
│   └── utils/            # Utilities
│       ├── __init__.py
│       └── helpers.py
├── alembic/              # Database migrations
├── uploads/              # Uploaded files
│   ├── profiles/
│   └── products/
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .gitignore
└── README.md
```

## Database Schema

### User Model
- id: UUID (primary key)
- email: String (unique, indexed)
- username: String (unique)
- hashed_password: String
- full_name: String (optional)
- avatar_url: String (optional, file path)
- is_active: Boolean
- is_admin: Boolean
- created_at: DateTime
- updated_at: DateTime

### Product Model
- id: UUID (primary key)
- name: String
- description: Text (optional)
- price: Decimal
- stock_quantity: Integer
- image_url: String (optional, file path)
- category: String (optional)
- is_available: Boolean
- created_at: DateTime
- updated_at: DateTime

## Features

### Authentication
- User registration (email verification optional)
- User login (JWT tokens)
- Password hashing with bcrypt
- Protected routes with dependency
- Token refresh mechanism

### User Management
- CRUD operations (users can update own profile, admin manages all)
- Avatar upload/update
- List users with pagination

### Product Management
- CRUD operations (admin manages all, authenticated users can read)
- Product image upload
- Stock management
- Search/filter by category
- List products with pagination

### File Uploads
- Profile avatars (users/)
- Product images (products/)
- Validation: image formats (jpg, jpeg, png, webp)
- Max file size: 5MB
- Unique filenames with UUID

## API Endpoints

### Auth (v1/auth)
- POST `/register` - Register new user
- POST `/login` - Login and get JWT tokens
- POST `/refresh` - Refresh access token

### Users (v1/users)
- GET `/` - List all users (admin only, paginated)
- GET `/me` - Get current user profile
- GET `/{user_id}` - Get specific user (public profile)
- PUT `/me` - Update current user
- DELETE `/me` - Delete current user
- POST `/me/avatar` - Upload avatar

### Products (v1/products)
- GET `/` - List all products (paginated, filterable)
- GET `/{product_id}` - Get product details
- POST `/` - Create product (admin only)
- PUT `/{product_id}` - Update product (admin only)
- DELETE `/{product_id}` - Delete product (admin only)
- POST `/{product_id}/image` - Upload product image (admin only)

## Tech Stack
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for PostgreSQL
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **Passlib + bcrypt**: Password hashing
- **python-jose**: JWT tokens
- **python-multipart**: File uploads
- **PostgreSQL**: Database

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost/tablemanager
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads/
MAX_FILE_SIZE=5242880
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp
```

### 3. Initialize Database
```bash
alembic upgrade head
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload
```

### 5. Access API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | None |
| SECRET_KEY | JWT signing secret | None |
| ALGORITHM | JWT algorithm | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry time | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiry | 7 |
| UPLOAD_DIR | Upload directory path | uploads/ |
| MAX_FILE_SIZE | Max upload size in bytes | 5242880 |

## Security Considerations
- Passwords hashed with bcrypt
- JWT tokens with expiry
- File upload validation (type, size)
- CORS middleware configured
- SQL injection protection via ORM
- Environment variables for secrets

## Future Enhancements
- Email verification
- Password reset
- Rate limiting
- API key authentication
- WebSocket for real-time updates
- Caching with Redis
- API versioning
- Comprehensive logging
- Unit and integration tests
