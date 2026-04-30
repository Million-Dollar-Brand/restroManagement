from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from app.core.tenant import get_tenant_session
from app.models.tenant import Order, OrderItem, MenuItem, OrderStatus
from app.core.tenant import require_role

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderItemCreate(BaseModel):
    """Schema for creating order item"""
    menu_item_id: str
    quantity: int = 1
    notes: str | None = None


class OrderCreate(BaseModel):
    """Schema for creating order"""
    table_number: int
    items: List[OrderItemCreate]
    notes: str | None = None


class OrderItemResponse(BaseModel):
    """Response schema for order item"""
    id: str
    menu_item_id: str
    menu_item_name: str
    quantity: int
    unit_price: float
    notes: str | None
    created_at: str


class OrderResponse(BaseModel):
    """Response schema for order"""
    id: str
    table_number: int
    status: str
    total_amount: float
    notes: str | None
    created_by: str
    items: List[OrderItemResponse]
    created_at: str
    updated_at: str


class OrderUpdate(BaseModel):
    """Schema for updating order"""
    status: OrderStatus | None = None
    notes: str | None = None


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter"]))
):
    """
    Create a new order (Manager/Waiter only)

    - **table_number**: Table number (required)
    - **items**: List of order items
    - **notes**: Optional order notes
    """
    # Validate menu items exist and calculate total
    total_amount = 0.0
    order_items = []

    for item_data in order_data.items:
        try:
            from uuid import UUID
            menu_item_uuid = UUID(item_data.menu_item_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid menu item ID: {item_data.menu_item_id}")

        # Get menu item
        result = await session.execute(
            select(MenuItem).where(
                and_(MenuItem.id == menu_item_uuid, MenuItem.is_available == True)
            )
        )
        menu_item = result.scalar_one_or_none()

        if not menu_item:
            raise HTTPException(
                status_code=400,
                detail=f"Menu item not found or not available: {item_data.menu_item_id}"
            )

        # Calculate item total
        item_total = menu_item.price * item_data.quantity
        total_amount += item_total

        order_items.append((menu_item, item_data))

    # Get current user ID from JWT (assuming it's stored in user_info)
    # For now, we'll need to look up the staff user by username
    from uuid import UUID
    current_username = user_info.get("username")

    result = await session.execute(
        select(Staff).where(Staff.username == current_username)
    )
    current_staff = result.scalar_one_or_none()

    if not current_staff:
        raise HTTPException(status_code=400, detail="Current user not found in tenant")

    # Create order
    order = Order(
        table_number=order_data.table_number,
        status=OrderStatus.PENDING,
        total_amount=total_amount,
        notes=order_data.notes,
        created_by_id=current_staff.id
    )
    session.add(order)
    await session.flush()  # Get order ID

    # Create order items
    created_items = []
    for menu_item, item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=item_data.quantity,
            unit_price=menu_item.price,
            notes=item_data.notes
        )
        session.add(order_item)
        created_items.append(OrderItemResponse(
            id=str(order_item.id),
            menu_item_id=str(menu_item.id),
            menu_item_name=menu_item.name,
            quantity=item_data.quantity,
            unit_price=menu_item.price,
            notes=item_data.notes,
            created_at=order_item.created_at.isoformat()
        ))

    await session.commit()
    await session.refresh(order)

    return OrderResponse(
        id=str(order.id),
        table_number=order.table_number,
        status=order.status.value,
        total_amount=order.total_amount,
        notes=order.notes,
        created_by=str(order.created_by_id),
        items=created_items,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat()
    )


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    status: OrderStatus | None = None,
    table_number: int | None = None,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """List orders with optional filtering"""
    query = select(Order)

    if status:
        query = query.where(Order.status == status)
    if table_number:
        query = query.where(Order.table_number == table_number)

    result = await session.execute(query)
    orders = result.scalars().all()

    response_orders = []
    for order in orders:
        # Get order items
        items_result = await session.execute(
            select(OrderItem, MenuItem).join(MenuItem).where(OrderItem.order_id == order.id)
        )
        items = []
        for order_item, menu_item in items_result:
            items.append(OrderItemResponse(
                id=str(order_item.id),
                menu_item_id=str(menu_item.id),
                menu_item_name=menu_item.name,
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
                notes=order_item.notes,
                created_at=order_item.created_at.isoformat()
            ))

        response_orders.append(OrderResponse(
            id=str(order.id),
            table_number=order.table_number,
            status=order.status.value,
            total_amount=order.total_amount,
            notes=order.notes,
            created_by=str(order.created_by_id),
            items=items,
            created_at=order.created_at.isoformat(),
            updated_at=order.updated_at.isoformat()
        ))

    return response_orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef", "cashier"]))
):
    """Get order by ID"""
    try:
        from uuid import UUID
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    result = await session.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get order items
    items_result = await session.execute(
        select(OrderItem, MenuItem).join(MenuItem).where(OrderItem.order_id == order.id)
    )
    items = []
    for order_item, menu_item in items_result:
        items.append(OrderItemResponse(
            id=str(order_item.id),
            menu_item_id=str(menu_item.id),
            menu_item_name=menu_item.name,
            quantity=order_item.quantity,
            unit_price=order_item.unit_price,
            notes=order_item.notes,
            created_at=order_item.created_at.isoformat()
        ))

    return OrderResponse(
        id=str(order.id),
        table_number=order.table_number,
        status=order.status.value,
        total_amount=order.total_amount,
        notes=order.notes,
        created_by=str(order.created_by_id),
        items=items,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat()
    )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    order_data: OrderUpdate,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager", "waiter", "chef"]))
):
    """Update order (Manager/Waiter/Chef only)"""
    try:
        from uuid import UUID
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    result = await session.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update fields
    update_data = order_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    await session.commit()
    await session.refresh(order)

    # Return updated order with items
    return await get_order(order_id, session, user_info)


@router.delete("/{order_id}")
async def delete_order(
    order_id: str,
    session: AsyncSession = Depends(get_tenant_session),
    user_info: dict = Depends(require_role(["manager"]))
):
    """Delete order (Manager only)"""
    try:
        from uuid import UUID
        order_uuid = UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    result = await session.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    await session.delete(order)
    await session.commit()

    return {"message": "Order deleted successfully"}