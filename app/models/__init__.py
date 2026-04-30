# Legacy models - kept for backward compatibility
from app.models.user import User
from app.models.product import Product

# Public schema models (system-level)
from app.models.public import SuperAdmin, Restaurant, RestaurantManager

# Tenant schema models (restaurant-specific)
from app.models.tenant import Staff, MenuItem, Order, OrderItem, UserRole, OrderStatus, TenantBase

__all__ = [
    "User", "Product",  # Legacy
    "SuperAdmin", "Restaurant", "RestaurantManager",  # Public schema
    "Staff", "MenuItem", "Order", "OrderItem", "UserRole", "OrderStatus", "TenantBase"  # Tenant schema
]
