# TableManager Project Context

## Purpose
This is a FastAPI backend service for a multi-tenant restaurant/table management system. It is designed to support super admins, restaurant managers, staff users, menus, orders, and tenant-specific data isolation through PostgreSQL schemas.

## Workspace Overview
- `app/main.py` - FastAPI app entrypoint, includes CORS, static uploads mounting, and routers.
- `app/config.py` - Application settings loaded from `.env` via `pydantic-settings`.
- `app/database.py` - Async SQLAlchemy engine/session management and schema search path helpers.
- `app/api/v1/router.py` - Main API router mounted at `/api/v1`.
- `app/api/v1/endpoints/` - REST endpoints for auth, super-admin, staff, menu, orders, plus legacy user/product code.
- `app/core/tenant.py` - Tenant routing, JWT role assertions, search path handling.
- `app/core/security.py` - JWT creation/verification and password hashing.
- `app/models/public.py` - Public schema models: `SuperAdmin`, `Restaurant`, `RestaurantManager`.
- `app/models/tenant.py` - Tenant schema models: `Staff`, `MenuItem`, `Order`, `OrderItem`.
- `alembic/` - Database migration environment and migrations.
- `uploads/` - Stored file uploads (profiles, products, etc.).

## Architecture
- FastAPI backend with async SQLAlchemy and PostgreSQL.
- Multi-tenant support using separate PostgreSQL schemas per restaurant tenant.
- Public schema stores super admins, restaurant registry, and restaurant managers.
- Tenant schemas store staff, menu items, orders, and order items.
- JWT authentication with role-based access control.
- Uploads served from `/uploads` static route.

## Primary Routes
### Authentication
- `POST /api/v1/auth/super-admin/register` - Create super admin.
- `POST /api/v1/auth/super-admin/login` - Super admin login.
- `POST /api/v1/auth/restaurant/login` - Restaurant manager login.
- `POST /api/v1/auth/refresh` - Refresh JWT token.

### Super Admin
- `POST /api/v1/super-admin/restaurants` - Create new restaurant tenant.
  - Creates PostgreSQL schema, runs tenant migrations, and bootstraps manager account.

### Tenant User Management
- `POST /api/v1/staff` - Create staff user.
- `GET /api/v1/staff` - List staff.
- `GET /api/v1/staff/{staff_id}` - Get staff user.
- `PUT /api/v1/staff/{staff_id}` - Update staff.
- `DELETE /api/v1/staff/{staff_id}` - Deactivate staff.

### Menu Management
- `POST /api/v1/menu/items` - Create menu item.
- `GET /api/v1/menu/items` - List items with optional filters.
- `GET /api/v1/menu/items/{item_id}` - Get menu item.
- `PUT /api/v1/menu/items/{item_id}` - Update menu item.
- `DELETE /api/v1/menu/items/{item_id}` - Delete item.
- `GET /api/v1/menu/categories` - List unique categories.

### Orders
- `POST /api/v1/orders` - Create order.
- `GET /api/v1/orders` - List orders with optional filters.
- `GET /api/v1/orders/{order_id}` - Get order details.

## JWT / Tenant Behavior
- JWT payload includes `sub`, `tenant_id`, `role`, and token `type`.
- `get_current_user_tenant()` decodes tokens and distinguishes super admins from tenant users.
- `get_tenant_session()` sets `search_path` to `public` or `tenant_<tenant_id>`.
- `require_role([...])` checks tenant user roles and grants super admin all access.

## Configuration
Key settings from `app/config.py`:
- `DATABASE_URL` - Async SQLAlchemy URL for PostgreSQL.
- `SECRET_KEY` - JWT secret.
- `ALGORITHM` - JWT algorithm (default `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Access token duration.
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token duration.
- `UPLOAD_DIR` - Upload storage path.
- `MAX_FILE_SIZE` - File upload size limit.
- `ALLOWED_EXTENSIONS` - Allowed upload file types.
- `TENANT_SCHEMA_PREFIX` - Prefix for tenant schemas (default `tenant_`).

## Database/Deployment Notes
- Uses PostgreSQL with asyncpg.
- Tenant creation is handled by `POST /api/v1/super-admin/restaurants`.
- Alembic migrations are used for schema versioning.
- `ALEMBIC_RUNNING` environment variable is used to disable async engine creation during migrations.
- Uploads are mounted and served under `/uploads`.

## Important Files
- `README.md` - Project overview and setup.
- `QUICKSTART.md` - Setup guide and troubleshooting.
- `API_USAGE.md` - API reference and examples.
- `ENVIRONMENT_VARS.md` - Environment variable descriptions.
- `DEPLOYMENT.md` - Deployment instructions.
- `setup.sh` / `setup.bat` - Automated local setup scripts.
- `create_admin.py` - Admin bootstrap utility.

## How to Use This Context
Use this file as a project summary for future prompts aimed at:
- extending API endpoints,
- adjusting tenant schema logic,
- fixing auth/role issues,
- adding features like email verification, shopping cart, or reporting,
- configuring production deployment.

## Recommended Starting Commands
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env values
alembic upgrade head
uvicorn app.main:app --reload
```

## Notes for Future Engines
- This repository is not a monolithic storefront; it is a multi-tenant restaurant backend.
- Super admins manage tenant creation and restaurant registry.
- Tenant users access menu and orders from their own schema.
- The router files in `app/api/v1/endpoints/` are the best place to implement business logic.
- `app/core/tenant.py` and `app/core/security.py` contain the auth and schema-routing control flow.
