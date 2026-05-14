# FastAPI Multi-Tenant Restaurant Ordering System Backend Plan

## Project Structure
```
tableManager/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app initialization with multi-tenant middleware
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection & session management
│   ├── models/           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── public.py     # Public schema models (super_admins, restaurants, managers)
│   │   ├── tenant.py     # Tenant schema models (staff, menu_items, orders, etc.)
│   │   ├── user.py       # Legacy user model (if needed)
│   │   └── product.py    # Legacy product model (if needed)
│   ├── schemas/          # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py       # Legacy schemas
│   │   └── product.py    # Legacy schemas
│   ├── api/              # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── super_admin.py   # Super admin endpoints
│   │   │   ├── staff.py         # Staff management endpoints
│   │   │   ├── menu.py          # Menu management endpoints
│   │   │   ├── orders.py        # Order management endpoints
│   │   │   ├── users.py         # Legacy user endpoints
│   │   │   └── products.py      # Legacy product endpoints
│   │   └── router.py
│   ├── core/             # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py   # Password hashing, JWT
│   │   ├── tenant.py     # Multi-tenant middleware and utilities
│   │   └── uploads.py    # File upload handling
│   └── utils/            # Utilities
│       ├── __init__.py
├── alembic/              # Database migrations
│   ├── env.py
│   └── versions/
│       ├── 001_initial_migration.py
│       ├── c4660246c543_add_multi_tenant_schema_support.py
│       ├── d12345678901_create_tenant_schema_tables.py
├── uploads/              # Uploaded files
│   ├── profiles/
│   ├── products/
│   └── temp/
├── scripts/              # Utility scripts
│   └── init_tenant_tables.py
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── .gitignore
└── README.md
```

## Database Schema

### Public Schema (`public`)

#### SuperAdmin Model
- id: UUID (primary key)
- email: String (unique, indexed)
- username: String (unique)
- hashed_password: String
- full_name: String (optional)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime

#### Restaurant Model
- id: UUID (primary key)
- name: String
- description: Text (optional)
- schema_name: String (unique, e.g., "tenant_d539a8f3_baba_41c6_bbc4_f431c7acd3c7")
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime

#### RestaurantManager Model
- id: UUID (primary key)
- email: String (unique, indexed)
- username: String (unique)
- hashed_password: String
- full_name: String (optional)
- restaurant_id: UUID (foreign key to restaurants)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime

### Tenant Schemas (`tenant_<restaurant_id>` with hyphens replaced by underscores)

#### Staff Model
- id: UUID (primary key)
- email: String (unique, indexed)
- username: String (unique)
- hashed_password: String
- full_name: String (optional)
- role: Enum (manager, waiter, chef, cashier)
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime

#### MenuItem Model
- id: UUID (primary key)
- name: String
- description: Text (optional)
- price: Float
- category: String (optional)
- image_url: String (optional, file path)
- is_available: Boolean
- created_at: DateTime
- updated_at: DateTime

#### Order Model
- id: UUID (primary key)
- table_number: Integer
- status: Enum (pending, confirmed, preparing, ready, delivered, cancelled)
- total_amount: Float
- notes: Text (optional)
- created_by_id: UUID (foreign key to staff)
- created_at: DateTime
- updated_at: DateTime

#### OrderItem Model
- id: UUID (primary key)
- order_id: UUID (foreign key to orders)
- menu_item_id: UUID (foreign key to menu_items)
- quantity: Integer
- unit_price: Float
- notes: Text (optional)
- created_at: DateTime

## Features

### Multi-Tenancy
- Schema-per-tenant architecture
- Dynamic schema routing based on JWT tokens
- Complete data isolation between restaurants
- Shared database instance

### Authentication & Authorization
- Super admin registration and login
- Restaurant manager and staff login
- JWT-based authentication with access & refresh tokens
- Role-based access control (RBAC)
- Password hashing with bcrypt

### Super Admin Management
- Create and manage restaurants
- View all restaurants in the system
- Deactivate restaurants

### Restaurant Management
- Restaurant managers can manage their restaurant
- Create and manage staff members
- Full control over menu and orders

### Staff Management
- Role-based staff accounts (manager, waiter, chef, cashier)
- Staff can login to their restaurant's tenant
- Permissions based on roles

### Menu Management
- CRUD operations for menu items
- Category organization
- Image uploads for menu items
- Availability status

### Order Management
- Create orders with multiple items
- Table number assignment
- Order status tracking
- Real-time order updates

### File Uploads
- Profile avatars (users/)
- Product/menu images (products/)
- Validation: image formats (jpg, jpeg, png, webp)
- Max file size: 5MB
- Unique filenames with UUID

## API Endpoints

### Auth (v1/auth)
- POST `/super-admin/register` - Register super admin
- POST `/super-admin/login` - Super admin login
- POST `/restaurant/login` - Restaurant manager/staff login
- POST `/refresh` - Refresh access token

### Super Admin (v1/super-admin)
- POST `/restaurants` - Create new restaurant
- GET `/restaurants` - List all restaurants
- DELETE `/restaurants/{restaurant_id}` - Deactivate restaurant

### Staff Management (v1/staff) - Tenant Schema
- POST `/` - Create staff member (manager only)
- GET `/` - List staff members
- GET `/{staff_id}` - Get staff member details
- PUT `/{staff_id}` - Update staff member (manager only)
- DELETE `/{staff_id}` - Deactivate staff member (manager only)

### Menu Management (v1/menu) - Tenant Schema
- POST `/items` - Create menu item (manager/chef)
- GET `/items` - List menu items (with filters)
- GET `/items/{item_id}` - Get menu item details
- PUT `/items/{item_id}` - Update menu item (manager/chef)
- DELETE `/items/{item_id}` - Delete menu item (manager only)
- GET `/categories` - Get unique categories

### Order Management (v1/orders) - Tenant Schema
- POST `/` - Create new order (manager/waiter)
- GET `/` - List orders (with filters)
- GET `/{order_id}` - Get order details
- PUT `/{order_id}` - Update order (manager/waiter/chef)
- DELETE `/{order_id}` - Delete order (manager only)

## Tech Stack
- **FastAPI**: Modern Python web framework with async support
- **SQLAlchemy**: ORM for PostgreSQL with multi-schema support
- **Alembic**: Database migrations
- **Pydantic**: Data validation
- **Passlib + bcrypt**: Password hashing
- **python-jose**: JWT tokens
- **python-multipart**: File uploads
- **PostgreSQL**: Database with schema-per-tenant architecture

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
REFRESH_TOKEN_EXPIRE_DAYS=7
UPLOAD_DIR=uploads/
MAX_FILE_SIZE=5242880
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp
```

### 3. Initialize Database
```bash
alembic upgrade head
python scripts/init_tenant_tables.py  # Initialize tenant schema tables
```

### 4. Create Super Admin
```bash
python create_admin.py
```

### 5. Run Development Server
```bash
uvicorn app.main:app --reload
```

### 6. Access API Docs
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
- Schema-based data isolation for multi-tenancy

## Future Enhancements
- Email verification for user accounts
- Password reset functionality
- Rate limiting
- API key authentication
- WebSocket for real-time order updates
- Caching with Redis
- Comprehensive logging
- Unit and integration tests
- Payment integration
- Customer-facing mobile app API
