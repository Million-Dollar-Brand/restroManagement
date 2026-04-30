import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Product(Base):
    """Product model for catalog items"""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    image_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


__all__ = ["Product"]
