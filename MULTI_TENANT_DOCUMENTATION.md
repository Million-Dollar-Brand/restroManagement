# Multi-Tenant Restaurant Ordering System

## Overview

This is a comprehensive FastAPI-based backend system for a multi-tenant restaurant ordering platform. The system implements a **schema-per-tenant architecture** where each restaurant operates in complete data isolation within its own PostgreSQL schema.

## Architecture

### Multi-Tenancy Approach
- **Schema-per-tenant**: Each restaurant gets a dedicated PostgreSQL schema (`tenant_<restaurant_id>`)
- **Shared database**: All tenants share the same PostgreSQL database instance
- **Dynamic routing**: FastAPI middleware automatically routes requests to the correct tenant schema based on JWT tokens

### Technology Stack
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT with OAuth2PasswordBearer
- **Validation**: Pydantic V2

## Database Schema

### Public Schema (`public`)

Contains system-level data shared across all tenants.

#### `super_admins`
System administrators with full access to create and manage restaurants.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Admin email |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Admin username |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(100) | NULL | Admin full name |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Account status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

#### `restaurants`
Registry of all restaurants in the system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique restaurant identifier |
| name | VARCHAR(100) | NOT NULL | Restaurant name |
| description | TEXT | NULL | Restaurant description |
| schema_name | VARCHAR(100) | UNIQUE, NOT NULL | PostgreSQL schema name (e.g., `tenant_123`) |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Restaurant status |
| manager_id | UUID | FOREIGN KEY → restaurant_managers.id | Reference to restaurant manager |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

#### `restaurant_managers`
Users who manage specific restaurants (stored in public schema).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique manager identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Manager email |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Manager username |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(100) | NULL | Manager full name |
| restaurant_id | UUID | NOT NULL, FOREIGN KEY → restaurants.id | Associated restaurant |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Account status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

### Tenant Schemas (`tenant_<restaurant_id>`)

Each restaurant has its own schema containing restaurant-specific data.

#### `staff`
Restaurant staff members (waiters, chefs, cashiers).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique staff identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Staff email |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Staff username |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(100) | NULL | Staff full name |
| role | ENUM | NOT NULL, DEFAULT 'waiter' | Staff role: 'manager', 'waiter', 'chef', 'cashier' |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Account status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

#### `menu_items`
Restaurant menu items.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique menu item identifier |
| name | VARCHAR(100) | NOT NULL | Item name |
| description | TEXT | NULL | Item description |
| price | FLOAT | NOT NULL | Item price |
| category | VARCHAR(50) | NULL | Item category |
| image_url | VARCHAR(500) | NULL | Item image URL |
| is_available | BOOLEAN | NOT NULL, DEFAULT true | Availability status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

#### `orders`
Customer orders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique order identifier |
| table_number | INTEGER | NOT NULL | Table number |
| status | ENUM | NOT NULL, DEFAULT 'pending' | Order status: 'pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled' |
| total_amount | FLOAT | NOT NULL, DEFAULT 0.0 | Total order amount |
| notes | TEXT | NULL | Order notes |
| created_by_id | UUID | NOT NULL, FOREIGN KEY → staff.id | Staff who created the order |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

#### `order_items`
Individual items within orders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique order item identifier |
| order_id | UUID | NOT NULL, FOREIGN KEY → orders.id | Parent order |
| menu_item_id | UUID | NOT NULL, FOREIGN KEY → menu_items.id | Menu item |
| quantity | INTEGER | NOT NULL, DEFAULT 1 | Item quantity |
| unit_price | FLOAT | NOT NULL | Price per unit at time of order |
| notes | TEXT | NULL | Item-specific notes |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |

## Role-Based Access Control (RBAC)

### User Roles Hierarchy

1. **Super Admin** (System Level)
   - Can create new restaurants
   - Can manage restaurant registry
   - Has access to all system functions
   - Operates in `public` schema

2. **Restaurant Manager** (Tenant Level)
   - Full control over their restaurant
   - Can create/manage staff
   - Can manage menu and orders
   - Operates in `tenant_<restaurant_id>` schema

3. **Restaurant Staff** (Tenant Level)
   - Role-based permissions:
     - **Waiter**: Can create and manage orders
     - **Chef**: Can update order status, manage menu
     - **Cashier**: Can view orders and manage payments
   - Operates in `tenant_<restaurant_id>` schema

## API Endpoints

### Authentication Endpoints

#### Super Admin
- `POST /api/v1/auth/super-admin/register` - Register super admin
- `POST /api/v1/auth/super-admin/login` - Super admin login

#### Restaurant Users
- `POST /api/v1/auth/restaurant/login` - Manager/staff login
- `POST /api/v1/auth/refresh` - Refresh JWT tokens

### Super Admin Endpoints
- `POST /api/v1/super-admin/restaurants` - Create new restaurant with schema
- `GET /api/v1/super-admin/restaurants` - List all restaurants
- `DELETE /api/v1/super-admin/restaurants/{id}` - Deactivate restaurant

### Staff Management (Tenant Schema)
- `POST /api/v1/staff` - Create staff member (Manager only)
- `GET /api/v1/staff` - List staff members
- `GET /api/v1/staff/{id}` - Get staff member details
- `PUT /api/v1/staff/{id}` - Update staff member (Manager only)
- `DELETE /api/v1/staff/{id}` - Deactivate staff member (Manager only)

### Menu Management (Tenant Schema)
- `POST /api/v1/menu/items` - Create menu item (Manager/Chef)
- `GET /api/v1/menu/items` - List menu items (with category/availability filters)
- `GET /api/v1/menu/items/{id}` - Get menu item details
- `PUT /api/v1/menu/items/{id}` - Update menu item (Manager/Chef)
- `DELETE /api/v1/menu/items/{id}` - Delete menu item (Manager only)
- `GET /api/v1/menu/categories` - Get unique menu categories

### Order Management (Tenant Schema)
- `POST /api/v1/orders` - Create new order (Manager/Waiter)
- `GET /api/v1/orders` - List orders (with status/table filters)
- `GET /api/v1/orders/{id}` - Get order details with items
- `PUT /api/v1/orders/{id}` - Update order (Manager/Waiter/Chef)
- `DELETE /api/v1/orders/{id}` - Delete order (Manager only)

## Authentication Flow

### JWT Token Structure
```json
{
  "sub": "username",
  "tenant_id": "uuid-string",  // null for super admin
  "role": "manager|waiter|chef|cashier",  // null for super admin
  "type": "access",
  "exp": 1640995200,
  "iat": 1640991600
}
```

### Schema Routing
1. JWT token is decoded to extract `tenant_id`
2. For super admin: operates in `public` schema
3. For tenant users: operates in `tenant_<tenant_id>` schema
4. SQLAlchemy session automatically sets `search_path` to correct schema

## Key Features

### Tenant Provisioning
- **Automatic schema creation**: `CREATE SCHEMA tenant_<id>`
- **Migration execution**: Alembic runs tenant-specific migrations
- **Initial setup**: Creates manager user in both public and tenant schemas
- **Cleanup**: Handles rollback on provisioning failures

### Data Isolation
- **Schema separation**: Each tenant's data is completely isolated
- **Foreign key integrity**: Relationships maintained within tenant schemas
- **Performance**: Efficient querying within tenant boundaries

### Security
- **JWT authentication**: Stateless token-based auth
- **Role-based permissions**: Endpoint-level access control
- **Tenant context**: Automatic schema switching prevents data leakage

### Async Operations
- **Full async/await**: All database operations are asynchronous
- **Connection pooling**: Efficient PostgreSQL connection management
- **Concurrent requests**: High performance under load

## Usage Examples

### 1. Super Admin Setup
```bash
# Register super admin
POST /api/v1/auth/super-admin/register
{
  "email": "admin@restaurantapp.com",
  "username": "superadmin",
  "password": "securepassword",
  "full_name": "Super Admin"
}

# Login
POST /api/v1/auth/super-admin/login
username=superadmin&password=securepassword
```

### 2. Restaurant Creation
```bash
# Create restaurant (requires super admin token)
POST /api/v1/super-admin/restaurants
Authorization: Bearer <super_admin_token>
{
  "name": "Mario's Italian Kitchen",
  "description": "Authentic Italian cuisine",
  "manager_email": "mario@marios.com",
  "manager_username": "mario_manager",
  "manager_password": "managerpass",
  "manager_full_name": "Mario Rossi"
}
```

### 3. Restaurant Operations
```bash
# Manager login
POST /api/v1/auth/restaurant/login
username=mario_manager&password=managerpass

# Create staff (requires manager token)
POST /api/v1/staff
Authorization: Bearer <manager_token>
{
  "email": "anna@restaurant.com",
  "username": "anna_waiter",
  "password": "staffpass",
  "full_name": "Anna Smith",
  "role": "waiter"
}

# Add menu item
POST /api/v1/menu/items
Authorization: Bearer <manager_token>
{
  "name": "Margherita Pizza",
  "description": "Classic tomato, mozzarella, and basil",
  "price": 12.99,
  "category": "Pizza"
}

# Create order
POST /api/v1/orders
Authorization: Bearer <manager_token>
{
  "table_number": 5,
  "items": [
    {
      "menu_item_id": "uuid-of-pizza",
      "quantity": 2,
      "notes": "Extra cheese"
    }
  ]
}
```

## Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Virtual environment

### Installation
```bash
# Clone repository
git clone <repository>
cd tablemanager

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Environment Variables
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/tablemanager
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Testing

Run the comprehensive test suite:
```bash
python test_api.py
```

This will test the complete flow:
1. Super admin registration and login
2. Restaurant creation with schema provisioning
3. Manager login and authentication
4. Staff creation and management
5. Menu item creation
6. Order creation and management

## Migration Strategy

### Public Schema Migrations
```bash
alembic revision -m "Add new public schema feature"
alembic upgrade head
```

### Tenant Schema Migrations
```bash
# Set environment variable for tenant schema
export TENANT_SCHEMA=tenant_12345678-1234-1234-1234-123456789012
alembic revision -m "Add tenant feature"
alembic upgrade head
```

## Security Considerations

1. **JWT Secret**: Use strong, randomly generated secret keys
2. **Password Hashing**: Bcrypt with appropriate cost factor
3. **Token Expiration**: Short-lived access tokens with refresh mechanism
4. **Schema Isolation**: Prevents data leakage between tenants
5. **Input Validation**: Pydantic models validate all API inputs
6. **SQL Injection**: SQLAlchemy parameterized queries prevent injection

## Performance Optimizations

1. **Async Operations**: Non-blocking I/O for high concurrency
2. **Connection Pooling**: Efficient PostgreSQL connection reuse
3. **Schema Search Path**: Fast tenant context switching
4. **Indexing**: Proper database indexes on frequently queried columns
5. **Pagination**: API endpoints support pagination for large datasets

## Future Enhancements

1. **Real-time Updates**: WebSocket support for order status updates
2. **Payment Integration**: Integration with payment processors
3. **Analytics**: Restaurant performance metrics and reporting
4. **Mobile App**: React Native mobile application
5. **Multi-language**: Internationalization support
6. **API Rate Limiting**: Request throttling and abuse prevention</content>
<parameter name="filePath">/home/biksbee/Personal/Projects/tableManager/MULTI_TENANT_RESTAURANT_SYSTEM.md