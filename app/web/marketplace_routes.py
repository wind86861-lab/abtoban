"""
Marketplace API routes for online shop (products, categories, cart, orders, portfolio)
"""
import os
import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db.models import Category, Portfolio, Product, CartItem, MarketOrder, MarketOrderItem, MarketOrderStatus, User
from app.db.session import async_session_maker

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")

router = APIRouter(prefix="/market-api", tags=["marketplace"])


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class CategoryCreate(BaseModel):
    name_uz: str
    name_ru: str
    name_en: str
    parent_id: Optional[int] = None
    image: Optional[str] = None
    order: int = 0


class CategoryUpdate(BaseModel):
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    parent_id: Optional[int] = None
    image: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class ProductCreate(BaseModel):
    name_uz: str
    name_ru: str
    name_en: str
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    price: Decimal
    discount_value: Optional[Decimal] = None
    discount_type: Optional[str] = None
    category_id: Optional[int] = None
    images: Optional[str] = None
    stock: int = 0
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name_uz: Optional[str] = None
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    price: Optional[Decimal] = None
    discount_value: Optional[Decimal] = None
    discount_type: Optional[str] = None
    category_id: Optional[int] = None
    images: Optional[str] = None
    stock: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CheckoutRequest(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: str
    comment: Optional[str] = None


class DirectCheckoutItem(BaseModel):
    product_id: int
    quantity: int


class DirectCheckoutRequest(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: str
    comment: Optional[str] = None
    viloyat: Optional[str] = None
    tuman: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    items: List[DirectCheckoutItem]


class MarketOrderStatusUpdate(BaseModel):
    status: MarketOrderStatus


class PortfolioCreate(BaseModel):
    title_uz: str
    title_ru: str
    title_en: str
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    year: Optional[int] = None
    images: Optional[str] = None
    order: int = 0


class PortfolioUpdate(BaseModel):
    title_uz: Optional[str] = None
    title_ru: Optional[str] = None
    title_en: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    year: Optional[int] = None
    images: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


# ══════════════════════════════════════════════════════════════════════════════
# IMAGE UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and return its URL."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Faqat rasm fayllar qabul qilinadi")

    ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fayl hajmi 10MB dan oshmasligi kerak")

    with open(filepath, "wb") as f:
        f.write(content)

    return {"url": f"/uploads/{filename}", "filename": filename}


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/categories")
async def list_categories(active_only: bool = False):
    """Get all categories."""
    async with async_session_maker() as session:
        q = select(Category).options(selectinload(Category.parent), selectinload(Category.children))
        if active_only:
            q = q.where(Category.is_active == True)
        q = q.order_by(Category.order, Category.id)
        result = await session.execute(q)
        categories = result.scalars().all()
        return [
            {
                "id": c.id,
                "name_uz": c.name_uz,
                "name_ru": c.name_ru,
                "name_en": c.name_en,
                "parent_id": c.parent_id,
                "image": c.image,
                "order": c.order,
                "is_active": c.is_active,
                "children_count": len(c.children),
            }
            for c in categories
        ]


@router.post("/categories")
async def create_category(data: CategoryCreate):
    """Create a new category."""
    async with async_session_maker() as session:
        category = Category(**data.model_dump())
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return {"id": category.id, "ok": True}


@router.patch("/categories/{category_id}")
async def update_category(category_id: int, data: CategoryUpdate):
    """Update a category."""
    async with async_session_maker() as session:
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        await session.commit()
        return {"ok": True}


@router.patch("/categories/{category_id}/toggle")
async def toggle_category(category_id: int):
    """Toggle category active status."""
    async with async_session_maker() as session:
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
        category.is_active = not category.is_active
        await session.commit()
        return {"ok": True, "is_active": category.is_active}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """Delete a category."""
    async with async_session_maker() as session:
        category = await session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
        await session.delete(category)
        await session.commit()
        return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/products")
async def list_products(
    category_id: Optional[int] = None,
    active_only: bool = False,
    featured_only: bool = False,
    limit: int = 100,
):
    """Get all products with filters."""
    async with async_session_maker() as session:
        q = select(Product).options(selectinload(Product.category))
        if category_id:
            q = q.where(Product.category_id == category_id)
        if active_only:
            q = q.where(Product.is_active == True)
        if featured_only:
            q = q.where(Product.is_featured == True)
        q = q.order_by(Product.created_at.desc()).limit(limit)
        result = await session.execute(q)
        products = result.scalars().all()
        return [
            {
                "id": p.id,
                "name_uz": p.name_uz,
                "name_ru": p.name_ru,
                "name_en": p.name_en,
                "description_uz": p.description_uz,
                "description_ru": p.description_ru,
                "description_en": p.description_en,
                "price": float(p.price),
                "discount_value": float(p.discount_value) if p.discount_value else None,
                "discount_type": p.discount_type,
                "category_id": p.category_id,
                "category_name": p.category.name_uz if p.category else None,
                "images": p.images.split(",") if p.images else [],
                "stock": p.stock,
                "is_featured": p.is_featured,
                "is_active": p.is_active,
            }
            for p in products
        ]


@router.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a single product by ID."""
    async with async_session_maker() as session:
        product = (
            await session.execute(
                select(Product)
                .options(selectinload(Product.category))
                .where(Product.id == product_id)
            )
        ).scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        return {
            "id": product.id,
            "name_uz": product.name_uz,
            "name_ru": product.name_ru,
            "name_en": product.name_en,
            "description_uz": product.description_uz,
            "description_ru": product.description_ru,
            "description_en": product.description_en,
            "price": float(product.price),
            "discount_value": float(product.discount_value) if product.discount_value else None,
            "discount_type": product.discount_type,
            "category_id": product.category_id,
            "category_name": product.category.name_uz if product.category else None,
            "images": product.images.split(",") if product.images else [],
            "stock": product.stock,
            "is_featured": product.is_featured,
            "is_active": product.is_active,
        }


@router.post("/products")
async def create_product(data: ProductCreate):
    """Create a new product."""
    async with async_session_maker() as session:
        product = Product(**data.model_dump())
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return {"id": product.id, "ok": True}


@router.patch("/products/{product_id}")
async def update_product(product_id: int, data: ProductUpdate):
    """Update a product."""
    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(product, key, value)
        await session.commit()
        return {"ok": True}


@router.patch("/products/{product_id}/toggle")
async def toggle_product(product_id: int):
    """Toggle product active status."""
    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        product.is_active = not product.is_active
        await session.commit()
        return {"ok": True, "is_active": product.is_active}


@router.delete("/products/{product_id}")
async def delete_product(product_id: int):
    """Delete a product."""
    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        await session.delete(product)
        await session.commit()
        return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# CART (for clients)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/cart/{user_id}")
async def get_cart(user_id: int):
    """Get user's cart items."""
    async with async_session_maker() as session:
        cart_items = (
            await session.execute(
                select(CartItem)
                .options(selectinload(CartItem.product))
                .where(CartItem.user_id == user_id)
            )
        ).scalars().all()
        
        total = Decimal(0)
        items = []
        for item in cart_items:
            if item.product and item.product.is_active:
                price = item.product.price
                if item.product.discount_value and item.product.discount_type:
                    if item.product.discount_type == "percentage":
                        price = price * (1 - item.product.discount_value / 100)
                    else:
                        price = max(Decimal(0), price - item.product.discount_value)
                subtotal = price * item.quantity
                total += subtotal
                items.append({
                    "id": item.id,
                    "product_id": item.product.id,
                    "product_name": item.product.name_uz,
                    "price": float(price),
                    "quantity": item.quantity,
                    "subtotal": float(subtotal),
                    "image": item.product.images.split(",")[0] if item.product.images else None,
                    "stock": item.product.stock,
                })
        
        return {"items": items, "total": float(total)}


@router.post("/cart/{user_id}")
async def add_to_cart(user_id: int, data: CartItemAdd):
    """Add item to cart."""
    async with async_session_maker() as session:
        # Check if product exists and is active
        product = await session.get(Product, data.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        
        # Check if already in cart
        existing = (
            await session.execute(
                select(CartItem).where(
                    CartItem.user_id == user_id,
                    CartItem.product_id == data.product_id
                )
            )
        ).scalar_one_or_none()
        
        if existing:
            existing.quantity += data.quantity
        else:
            cart_item = CartItem(user_id=user_id, **data.model_dump())
            session.add(cart_item)
        
        await session.commit()
        return {"ok": True}


@router.patch("/cart/items/{cart_item_id}")
async def update_cart_item(cart_item_id: int, data: CartItemUpdate):
    """Update cart item quantity."""
    async with async_session_maker() as session:
        cart_item = await session.get(CartItem, cart_item_id)
        if not cart_item:
            raise HTTPException(status_code=404, detail="Savatda topilmadi")
        cart_item.quantity = data.quantity
        await session.commit()
        return {"ok": True}


@router.delete("/cart/items/{cart_item_id}")
async def remove_from_cart(cart_item_id: int):
    """Remove item from cart."""
    async with async_session_maker() as session:
        cart_item = await session.get(CartItem, cart_item_id)
        if not cart_item:
            raise HTTPException(status_code=404, detail="Savatda topilmadi")
        await session.delete(cart_item)
        await session.commit()
        return {"ok": True}


@router.delete("/cart/{user_id}/clear")
async def clear_cart(user_id: int):
    """Clear all items from user's cart."""
    async with async_session_maker() as session:
        await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await session.commit()
        return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/cart/{user_id}/checkout")
async def checkout(user_id: int, data: CheckoutRequest):
    """Checkout cart and create order."""
    async with async_session_maker() as session:
        # Get cart items
        cart_items = (
            await session.execute(
                select(CartItem)
                .options(selectinload(CartItem.product))
                .where(CartItem.user_id == user_id)
            )
        ).scalars().all()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Savat bo'sh")
        
        # Calculate total and create order items
        total = Decimal(0)
        order_items = []
        
        for item in cart_items:
            if not item.product or not item.product.is_active:
                continue
            
            price = item.product.price
            if item.product.discount_value and item.product.discount_type:
                if item.product.discount_type == "percentage":
                    price = price * (1 - item.product.discount_value / 100)
                else:
                    price = max(Decimal(0), price - item.product.discount_value)
            
            subtotal = price * item.quantity
            total += subtotal
            
            order_items.append(
                MarketOrderItem(
                    product_id=item.product.id,
                    product_name=item.product.name_uz,
                    price=price,
                    quantity=item.quantity,
                    image=item.product.images.split(",")[0] if item.product.images else None,
                )
            )
        
        if not order_items:
            raise HTTPException(status_code=400, detail="Savat bo'sh")
        
        # Create order
        order = MarketOrder(
            user_id=user_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            total_price=total,
            comment=data.comment,
            items=order_items,
        )
        session.add(order)
        
        # Clear cart
        await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
        
        await session.commit()
        await session.refresh(order)
        
        return {"ok": True, "order_id": order.id}


@router.get("/orders")
async def list_market_orders(status: Optional[str] = None, limit: int = 100):
    """Get all market orders (admin)."""
    async with async_session_maker() as session:
        q = select(MarketOrder).options(
            selectinload(MarketOrder.user),
            selectinload(MarketOrder.items)
        )
        if status:
            q = q.where(MarketOrder.status == status)
        q = q.order_by(MarketOrder.created_at.desc()).limit(limit)
        result = await session.execute(q)
        orders = result.scalars().all()
        
        return [
            {
                "id": o.id,
                "user_id": o.user_id,
                "customer_name": o.customer_name or o.user.full_name,
                "customer_phone": o.customer_phone,
                "total_price": float(o.total_price),
                "status": o.status.value,
                "comment": o.comment,
                "items_count": len(o.items),
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]


@router.get("/orders/{order_id}")
async def get_market_order(order_id: int):
    """Get market order details."""
    async with async_session_maker() as session:
        order = (
            await session.execute(
                select(MarketOrder)
                .options(
                    selectinload(MarketOrder.user),
                    selectinload(MarketOrder.items).selectinload(MarketOrderItem.product)
                )
                .where(MarketOrder.id == order_id)
            )
        ).scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
        
        return {
            "id": order.id,
            "user_id": order.user_id,
            "customer_name": order.customer_name or order.user.full_name,
            "customer_phone": order.customer_phone,
            "total_price": float(order.total_price),
            "status": order.status.value,
            "comment": order.comment,
            "viloyat": order.viloyat,
            "tuman": order.tuman,
            "latitude": order.latitude,
            "longitude": order.longitude,
            "address": order.address,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "price": float(item.price),
                    "quantity": item.quantity,
                    "image": item.image,
                    "subtotal": float(item.price * item.quantity),
                }
                for item in order.items
            ],
        }


@router.patch("/orders/{order_id}/status")
async def update_market_order_status(order_id: int, data: MarketOrderStatusUpdate):
    """Update market order status (admin)."""
    async with async_session_maker() as session:
        order = await session.get(MarketOrder, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
        order.status = data.status
        await session.commit()
        return {"ok": True}


@router.get("/users/{user_id}/orders")
async def get_user_market_orders(user_id: int):
    """Get user's market orders."""
    async with async_session_maker() as session:
        orders = (
            await session.execute(
                select(MarketOrder)
                .options(selectinload(MarketOrder.items))
                .where(MarketOrder.user_id == user_id)
                .order_by(MarketOrder.created_at.desc())
            )
        ).scalars().all()
        
        return [
            {
                "id": o.id,
                "total_price": float(o.total_price),
                "status": o.status.value,
                "items_count": len(o.items),
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]


@router.post("/shop/checkout")
async def direct_checkout(data: DirectCheckoutRequest):
    """Direct checkout from web shop (client-side cart). No user_id required."""
    async with async_session_maker() as session:
        if not data.items:
            raise HTTPException(status_code=400, detail="Savat bo'sh")

        total = Decimal(0)
        order_items = []

        for cart_item in data.items:
            product = await session.get(Product, cart_item.product_id)
            if not product or not product.is_active:
                continue

            price = product.price
            if product.discount_value and product.discount_type:
                if product.discount_type == "percentage":
                    price = price * (1 - product.discount_value / 100)
                else:
                    price = max(Decimal(0), price - product.discount_value)

            subtotal = price * cart_item.quantity
            total += subtotal

            order_items.append(
                MarketOrderItem(
                    product_id=product.id,
                    product_name=product.name_uz,
                    price=price,
                    quantity=cart_item.quantity,
                    image=product.images.split(",")[0] if product.images else None,
                )
            )

        if not order_items:
            raise HTTPException(status_code=400, detail="Mahsulotlar topilmadi")

        # Find or create a guest user for web orders
        guest = (await session.execute(
            select(User).where(User.phone == data.customer_phone)
        )).scalar_one_or_none()

        user_id = guest.id if guest else 0

        order = MarketOrder(
            user_id=user_id if user_id else 1,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            total_price=total,
            comment=data.comment,
            viloyat=data.viloyat,
            tuman=data.tuman,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
            items=order_items,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)

        return {"ok": True, "order_id": order.id}


# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/portfolios")
async def list_portfolios(active_only: bool = False):
    """Get all portfolio projects."""
    async with async_session_maker() as session:
        q = select(Portfolio)
        if active_only:
            q = q.where(Portfolio.is_active == True)
        q = q.order_by(Portfolio.order.desc(), Portfolio.id.desc())
        result = await session.execute(q)
        items = result.scalars().all()
        return [
            {
                "id": p.id,
                "title_uz": p.title_uz,
                "title_ru": p.title_ru,
                "title_en": p.title_en,
                "description_uz": p.description_uz,
                "description_ru": p.description_ru,
                "description_en": p.description_en,
                "location": p.location,
                "client_name": p.client_name,
                "year": p.year,
                "images": p.images.split(",") if p.images else [],
                "order": p.order,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in items
        ]


@router.post("/portfolios")
async def create_portfolio(data: PortfolioCreate):
    """Create a new portfolio project."""
    async with async_session_maker() as session:
        item = Portfolio(**data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return {"id": item.id, "ok": True}


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio(portfolio_id: int):
    """Get a single portfolio project."""
    async with async_session_maker() as session:
        item = await session.get(Portfolio, portfolio_id)
        if not item:
            raise HTTPException(status_code=404, detail="Loyiha topilmadi")
        return {
            "id": item.id,
            "title_uz": item.title_uz,
            "title_ru": item.title_ru,
            "title_en": item.title_en,
            "description_uz": item.description_uz,
            "description_ru": item.description_ru,
            "description_en": item.description_en,
            "location": item.location,
            "client_name": item.client_name,
            "year": item.year,
            "images": item.images.split(",") if item.images else [],
            "order": item.order,
            "is_active": item.is_active,
        }


@router.patch("/portfolios/{portfolio_id}")
async def update_portfolio(portfolio_id: int, data: PortfolioUpdate):
    """Update a portfolio project."""
    async with async_session_maker() as session:
        item = await session.get(Portfolio, portfolio_id)
        if not item:
            raise HTTPException(status_code=404, detail="Loyiha topilmadi")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        await session.commit()
        return {"ok": True}


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: int):
    """Delete a portfolio project."""
    async with async_session_maker() as session:
        item = await session.get(Portfolio, portfolio_id)
        if not item:
            raise HTTPException(status_code=404, detail="Loyiha topilmadi")
        await session.delete(item)
        await session.commit()
        return {"ok": True}


@router.patch("/portfolios/{portfolio_id}/toggle")
async def toggle_portfolio(portfolio_id: int):
    """Toggle portfolio project active status."""
    async with async_session_maker() as session:
        item = await session.get(Portfolio, portfolio_id)
        if not item:
            raise HTTPException(status_code=404, detail="Loyiha topilmadi")
        item.is_active = not item.is_active
        await session.commit()
        return {"ok": True, "is_active": item.is_active}
