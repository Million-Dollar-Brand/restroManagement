from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductList
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductList)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    available_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List products with optional filtering

    - **skip**: Number of records to skip
    - **limit**: Maximum records per page (max 100)
    - **category**: Filter by category name
    - **available_only**: Show only available products (default true)
    - **search**: Search in name and description
    """
    query = db.query(Product)

    # Filter by availability
    if available_only:
        query = query.filter(Product.is_available == True)

    # Filter by category
    if category:
        query = query.filter(Product.category == category)

    # Search in name/description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term))
        )

    total = query.count()
    products = query.offset(skip).limit(limit).all()
    total_pages = (total + limit - 1) // limit

    return {
        "items": products,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
        "total_pages": total_pages
    }


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """
    Get product details by ID

    - **product_id**: UUID of the product
    """
    try:
        import uuid
        pid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new product (admin only)

    - **name**: Product name (required)
    - **description**: Optional description
    - **price**: Positive decimal price
    - **stock_quantity**: Inventory count (default 0)
    - **category**: Optional category name
    - **is_available**: Availability status (default true)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a product (admin only)

    - **product_id**: UUID of product to update
    - All fields optional, only provided fields will be updated
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        import uuid
        pid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a product (admin only)

    - **product_id**: UUID of product to delete
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        import uuid
        pid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete associated image
    if product.image_url:
        await delete_file(product.image_url)

    db.delete(product)
    db.commit()
    return None


@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload product image (admin only)

    - **product_id**: UUID of product
    - **file**: Image file (jpg, jpeg, png, webp), max 5MB
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        import uuid
        pid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete old image
    if product.image_url:
        await delete_file(product.image_url)

    # Save new image
    file_path = await save_upload_file(file, subfolder="products")
    product.image_url = file_path
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}/image", response_model=ProductResponse)
async def remove_product_image(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove product image (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        import uuid
        pid = uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    product = db.query(Product).filter(Product.id == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.image_url:
        await delete_file(product.image_url)
        product.image_url = None
        db.commit()
        db.refresh(product)

    return product
