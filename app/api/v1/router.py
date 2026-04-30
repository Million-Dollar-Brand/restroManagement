from fastapi import APIRouter
from app.api.v1.endpoints import auth, super_admin, staff, menu, orders

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
# Legacy endpoints not used in multi-tenant system:
# api_router.include_router(users.router)
# api_router.include_router(products.router)

api_router.include_router(super_admin.router)
api_router.include_router(staff.router)
api_router.include_router(menu.router)
api_router.include_router(orders.router)
