from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(0, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    is_available: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    is_available: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: uuid.UUID
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Schema for paginated product list"""
    items: list[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
