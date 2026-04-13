import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum as SAEnum,
    ForeignKey, Integer, Numeric, String, Table, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Language(str, enum.Enum):
    UZ_LAT = "uz_lat"
    UZ_CYR = "uz_cyr"
    RU = "ru"


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    HELPER_ADMIN = "helper_admin"
    MASTER = "master"
    USTA = "usta"
    ZAVOD = "zavod"
    SHOFER = "shofer"
    KLIENT = "klient"


ROLE_LABELS: dict[UserRole, str] = {
    UserRole.SUPER_ADMIN: "Super Admin",
    UserRole.ADMIN: "Admin",
    UserRole.HELPER_ADMIN: "Yordamchi Admin",
    UserRole.MASTER: "Master",
    UserRole.USTA: "Usta",
    UserRole.ZAVOD: "Zavod",
    UserRole.SHOFER: "Shofer",
    UserRole.KLIENT: "Klient",
}

ADMIN_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN}
MANAGEMENT_ROLES = {UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HELPER_ADMIN}


class OrderStatus(str, enum.Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_WORK = "in_work"
    DONE = "done"
    CANCELLED = "cancelled"


ORDER_STATUS_LABELS: dict[OrderStatus, str] = {
    OrderStatus.NEW: "🆕 Yangi",
    OrderStatus.CONFIRMED: "✅ Tasdiqlangan",
    OrderStatus.IN_WORK: "🔧 Ishda",
    OrderStatus.DONE: "🏁 Tugagan",
    OrderStatus.CANCELLED: "❌ Bekor qilingan",
}


class ExpenseType(str, enum.Enum):
    MATERIAL = "material"
    DELIVERY = "delivery"
    WAGE = "wage"
    BARDYOR = "bardyor"
    EXTRA = "extra"


class MaterialRequestStatus(str, enum.Enum):
    ADMIN_PENDING = "admin_pending"
    PENDING = "pending"
    PRICED = "priced"
    DELIVERED = "delivered"


# Many-to-many join table: User ↔ Hudud (Region) — for multi-region ustas/shofers
user_hududlar = Table(
    "user_hududlar",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("hudud_id", Integer, ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True),
)

# Many-to-many join table: Zavod ↔ Hudud (Region)
zavod_hududlar = Table(
    "zavod_hududlar",
    Base.metadata,
    Column("zavod_id", Integer, ForeignKey("zavods.id", ondelete="CASCADE"), primary_key=True),
    Column("hudud_id", Integer, ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True),
)


class Region(Base):
    """Hudud (location): viloyat + tuman + tafsif."""
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    viloyat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tuman: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tafsif: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    users: Mapped[List["User"]] = relationship("User", back_populates="region")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="region")
    zavods: Mapped[List["Zavod"]] = relationship(
        "Zavod", secondary=zavod_hududlar, back_populates="hududlar"
    )
    ustas: Mapped[List["User"]] = relationship(
        "User", secondary=user_hududlar, back_populates="hududlar"
    )


class AsphaltType(Base):
    __tablename__ = "asphalt_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_per_m2: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="asphalt_type")


class Zavod(Base):
    """Zavod (factory/plant) entity that can serve multiple locations."""
    
    __tablename__ = "zavods"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    tafsif: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    
    users: Mapped[List["User"]] = relationship("User", back_populates="zavod")
    hududlar: Mapped[List["Region"]] = relationship(
        "Region", secondary=zavod_hududlar, back_populates="zavods"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.KLIENT,
        nullable=False,
    )
    region_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("regions.id"), nullable=True
    )
    zavod_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("zavods.id"), nullable=True
    )
    language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    region: Mapped[Optional["Region"]] = relationship("Region", back_populates="users")
    zavod: Mapped[Optional["Zavod"]] = relationship("Zavod", back_populates="users")
    hududlar: Mapped[List["Region"]] = relationship(
        "Region", secondary=user_hududlar, back_populates="ustas"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", foreign_keys="AuditLog.user_id"
    )
    client_orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="client", foreign_keys="Order.client_id"
    )
    master_orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="master", foreign_keys="Order.master_id"
    )
    usta_orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="usta", foreign_keys="Order.usta_id"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="user", cascade="all, delete-orphan"
    )
    market_orders: Mapped[List["MarketOrder"]] = relationship(
        "MarketOrder", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} role={self.role}>"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    master_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    usta_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    zavod_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    region_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("regions.id"), nullable=True)
    asphalt_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("asphalt_types.id"), nullable=True)

    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    area_m2: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    area_tonnes: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)

    total_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    advance_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    debt: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)

    usta_wage: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    usta_wage_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    master_commission: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.NEW,
        nullable=False,
        index=True,
    )

    work_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    usta_assignment_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    client: Mapped["User"] = relationship("User", back_populates="client_orders", foreign_keys=[client_id])
    master: Mapped[Optional["User"]] = relationship("User", back_populates="master_orders", foreign_keys=[master_id])
    usta: Mapped[Optional["User"]] = relationship("User", back_populates="usta_orders", foreign_keys=[usta_id])
    region: Mapped[Optional["Region"]] = relationship("Region", back_populates="orders")
    asphalt_type: Mapped[Optional["AsphaltType"]] = relationship("AsphaltType", back_populates="orders")
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="order")
    material_requests: Mapped[List["MaterialRequest"]] = relationship("MaterialRequest", back_populates="order")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    expense_type: Mapped[ExpenseType] = mapped_column(
        SAEnum(ExpenseType, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="expenses")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class MaterialRequest(Base):
    __tablename__ = "material_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    usta_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    zavod_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    amount_tonnes: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    material_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    delivery_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    extra_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    status: Mapped[MaterialRequestStatus] = mapped_column(
        SAEnum(MaterialRequestStatus, values_callable=lambda x: [e.value for e in x]),
        default=MaterialRequestStatus.PENDING,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="material_requests")
    usta: Mapped["User"] = relationship("User", foreign_keys=[usta_id])
    zavod: Mapped[Optional["User"]] = relationship("User", foreign_keys=[zavod_id])


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])


# ══════════════════════════════════════════════════════════════════════════════
# MARKETPLACE MODELS (Online Shop for Clients)
# ══════════════════════════════════════════════════════════════════════════════

class Category(Base):
    """Product category with multilingual support."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category"
    )


class Product(Base):
    """Product in the online marketplace."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_uz: Mapped[str] = mapped_column(String(500), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(500), nullable=False)
    name_en: Mapped[str] = mapped_column(String(500), nullable=False)
    description_uz: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    discount_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    category: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="products"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="product", cascade="all, delete-orphan"
    )
    order_items: Mapped[List["MarketOrderItem"]] = relationship(
        "MarketOrderItem", back_populates="product"
    )


class CartItem(Base):
    """Shopping cart item for a user."""
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="cart_items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")


class MarketOrderStatus(str, enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MarketOrder(Base):
    """Customer order from the online marketplace."""
    __tablename__ = "market_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[MarketOrderStatus] = mapped_column(
        SAEnum(MarketOrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=MarketOrderStatus.NEW,
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="market_orders")
    items: Mapped[List["MarketOrderItem"]] = relationship(
        "MarketOrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class MarketOrderItem(Base):
    """Individual item in a market order."""
    __tablename__ = "market_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("market_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    order: Mapped["MarketOrder"] = relationship(
        "MarketOrder", back_populates="items"
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="order_items"
    )
