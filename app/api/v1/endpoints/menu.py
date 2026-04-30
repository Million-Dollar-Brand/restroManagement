from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.tenant import get_tenant_session
from app.models.tenant import MenuItem
from app.core.tenant import require_role

router = APIRouter(prefix="/menu", tags=["menu"])


class MenuItemCreate(BaseModel):
    """Schema for creating menu item"""
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    image_url: str | None = None
    is_available: bool = True


class MenuItemResponse(BaseModel):
    """Response schema for menu item"""
    id: str
    name: str
    description: str | None
    price: float
    category: str | None
    image_url: str | None
    is_available: bool
    created_at: str
    updated_at: str


class MenuItemUpdate(BaseModel):
    """Schema for updating menu item"""
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    image_url: str | None = None
    is_available: bool | None = None


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item_data: MenuItemCreate,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "chef"]))
):
    """
    Create a new menu item (Manager/Chef only)

    - **name**: Item name (required)
    - **description**: Optional description
    - **price**: Item price (required)
    - **category**: Optional category
    - **image_url**: Optional image URL
    - **is_available**: Availability status
    """
    # Create menu item
    item = MenuItem(
        name=item_data.name,
        description=item_data.description,
        price=item_data.price,
        category=item_data.category,
        image_url=item_data.image_url,
        is_available=item_data.is_available
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    return MenuItemResponse(
        id=str(item.id),
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category,
        image_url=item.image_url,
        is_available=item.is_available,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat()
    )


@router.get("/items", response_model=List[MenuItemResponse])
async def list_menu_items(
    category: str | None = None,
    available_only: bool = False,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """List menu items with optional filtering"""
    query = select(MenuItem)

    if category:
        query = query.where(MenuItem.category == category)

    if available_only:
        query = query.where(MenuItem.is_available == True)

    result = await session.execute(query)
    items = result.scalars().all()

    return [
        MenuItemResponse(
            id=str(i.id),
            name=i.name,
            description=i.description,
            price=i.price,
            category=i.category,
            image_url=i.image_url,
            is_available=i.is_available,
            created_at=i.created_at.isoformat(),
            updated_at=i.updated_at.isoformat()
        )
        for i in items
    ]


@router.get("/items/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: str,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """Get menu item by ID"""
    try:
        from uuid import UUID
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID")

    result = await session.execute(select(MenuItem).where(MenuItem.id == item_uuid))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    return MenuItemResponse(
        id=str(item.id),
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category,
        image_url=item.image_url,
        is_available=item.is_available,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat()
    )


@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: str,
    item_data: MenuItemUpdate,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "chef"]))
):
    """Update menu item (Manager/Chef only)"""
    try:
        from uuid import UUID
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID")

    result = await session.execute(select(MenuItem).where(MenuItem.id == item_uuid))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Update fields
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    await session.commit()
    await session.refresh(item)

    return MenuItemResponse(
        id=str(item.id),
        name=item.name,
        description=item.description,
        price=item.price,
        category=item.category,
        image_url=item.image_url,
        is_available=item.is_available,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat()
    )


@router.delete("/items/{item_id}")
async def delete_menu_item(
    item_id: str,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager"]))
):
    """Delete menu item (Manager only)"""
    try:
        from uuid import UUID
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID")

    result = await session.execute(select(MenuItem).where(MenuItem.id == item_uuid))
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    await session.delete(item)
    await session.commit()

    return {"message": "Menu item deleted successfully"}


@router.get("/categories")
async def get_menu_categories(
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """Get unique menu categories"""
    result = await session.execute(
        select(MenuItem.category).where(MenuItem.category.isnot(None)).distinct()
    )
    categories = [row[0] for row in result.all()]

    return {"categories": categories}