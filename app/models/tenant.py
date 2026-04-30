import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from app.config import settings
import enum


# Create a separate base for tenant-specific models
# This allows us to configure schema dynamically
TenantBase = declarative_base()


class UserRole(str, enum.Enum):
    """Enum for tenant user roles"""
    MANAGER = "manager"
    WAITER = "waiter"
    CHEF = "chef"
    CASHIER = "cashier"


class OrderStatus(str, enum.Enum):
    """Enum for order statuses"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Staff(TenantBase):
    """Staff user model - stores in tenant schema"""
    __tablename__ = "staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.WAITER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MenuItem(TenantBase):
    """Menu item model - stores in tenant schema"""
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Order(TenantBase):
    """Order model - stores in tenant schema"""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_number = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_amount = Column(Float, nullable=False, default=0.0)
    notes = Column(Text, nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    created_by = relationship("Staff")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(TenantBase):
    """Order item model - stores in tenant schema"""
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")


__all__ = ["Staff", "MenuItem", "Order", "OrderItem", "UserRole", "OrderStatus", "TenantBase"]