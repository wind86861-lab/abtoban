from sqladmin import ModelView
from sqlalchemy.orm.exc import DetachedInstanceError

from app.db.models import (
    AsphaltCategory,
    AsphaltSubCategory,
    AsphaltType,
    Category,
    Expense,
    MarketOrder,
    MarketOrderStatus,
    MaterialRequest,
    Order,
    OrderStatus,
    Portfolio,
    Product,
    Region,
    Tuman,
    User,
    Viloyat,
    Zavod,
)


class UserAdmin(ModelView, model=User):
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    icon = "fa-solid fa-users"

    column_list = [
        User.id,
        User.telegram_id,
        User.full_name,
        User.phone,
        User.role,
        User.viloyat_id,
        User.tuman_id,
        User.is_active,
        User.created_at,
    ]

    column_details_list = [
        User.id,
        User.telegram_id,
        User.full_name,
        User.username,
        User.phone,
        User.role,
        User.viloyat_id,
        User.tuman_id,
        User.region_id,
        User.zavod_id,
        User.language,
        User.is_active,
        User.created_at,
        User.updated_at,
        "client_orders",
        "master_orders",
        "usta_orders",
    ]

    column_searchable_list = [User.full_name, User.username, User.phone]

    column_sortable_list = [
        User.id, User.role, User.is_active, User.created_at, User.full_name
    ]

    column_filters = [
        User.role,
        User.is_active,
        User.viloyat_id,
        User.tuman_id,
        User.zavod_id,
        User.created_at,
    ]

    column_labels = {
        User.viloyat_id: "Viloyat",
        User.tuman_id: "Tuman",
        User.region_id: "Hudud",
        User.zavod_id: "Zavod",
    }
    
    form_args = {
        "viloyat_id": {"label": "Viloyat"},
        "tuman_id": {"label": "Tuman"},
        "region_id": {"label": "Hudud (eski)"},
        "zavod_id": {"label": "Zavod"},
    }

    form_columns = [
        User.full_name,
        User.username,
        User.phone,
        User.role,
        User.is_active,
        User.viloyat_id,
        User.tuman_id,
        User.region_id,
        User.zavod_id,
    ]
    
    form_ajax_refs = {
        "viloyat": {
            "fields": ("name",),
            "order_by": "name",
        },
        "tuman_rel": {
            "fields": ("name",),
            "order_by": "name",
        },
        "region": {
            "fields": ("name",),
            "order_by": "name",
        },
        "zavod": {
            "fields": ("name",),
            "order_by": "name",
        },
    }

    form_include_pk = False
    can_create = False
    can_delete = False
    can_edit = True
    page_size = 25

    column_select_related_list = ["viloyat", "tuman_rel", "region", "zavod"]

    def _fmt_orders(m, a):
        orders = (
            getattr(m, "usta_orders", None)
            or getattr(m, "master_orders", None)
            or getattr(m, "client_orders", None)
            or []
        )
        if not orders:
            return "-"
        lines = []
        for o in orders[:20]:
            lines.append(
                f"#{o.order_number} — {o.client_name} — {o.status.value if hasattr(o.status,'value') else o.status} — {o.total_price or 0:.0f} so'm"
            )
        return " | ".join(lines) + (f" (+{len(orders)-20} ta)" if len(orders) > 20 else "")

    column_formatters = {
        User.viloyat_id: lambda m, a: m.viloyat.name if m.viloyat else "-",
        User.tuman_id: lambda m, a: m.tuman_rel.name if m.tuman_rel else "-",
    }

    column_formatters_detail = {
        User.viloyat_id: lambda m, a: m.viloyat.name if m.viloyat else "-",
        User.tuman_id: lambda m, a: m.tuman_rel.name if m.tuman_rel else "-",
        User.region_id: lambda m, a: m.region.name if m.region else "-",
        User.zavod_id: lambda m, a: m.zavod.name if m.zavod else "-",
        "usta_orders": _fmt_orders,
        "master_orders": _fmt_orders,
        "client_orders": _fmt_orders,
    }
    
    async def on_model_change(self, data: dict, model: User, is_created: bool, request) -> None:
        """Called when model is updated. Ensure changes are committed."""
        # Update timestamp
        from datetime import datetime
        model.updated_at = datetime.utcnow()
        await super().on_model_change(data, model, is_created, request)


class OrderAdmin(ModelView, model=Order):
    name = "Zakaz"
    name_plural = "Zakazlar"
    icon = "fa-solid fa-file-invoice"

    column_list = [
        Order.id,
        Order.order_number,
        Order.client_name,
        Order.client_phone,
        Order.viloyat_id,
        Order.tuman_id,
        Order.master_id,
        Order.usta_id,
        Order.asphalt_type_id,
        Order.area_m2,
        Order.total_price,
        Order.status,
        Order.work_date,
        Order.created_at,
    ]

    column_details_list = [
        Order.id,
        Order.order_number,
        Order.client_id,
        Order.client_name,
        Order.client_phone,
        Order.viloyat_id,
        Order.tuman_id,
        Order.region_id,
        Order.address,
        Order.latitude,
        Order.longitude,
        Order.master_id,
        Order.usta_id,
        Order.zavod_id,
        Order.asphalt_type_id,
        Order.area_m2,
        Order.area_tonnes,
        Order.total_price,
        Order.advance_paid,
        Order.discount,
        Order.debt,
        Order.usta_wage,
        Order.usta_wage_note,
        Order.master_commission,
        Order.status,
        Order.work_date,
        Order.created_at,
        Order.confirmed_at,
        Order.completed_at,
        Order.notes,
        "expenses",
        "material_requests",
    ]

    column_searchable_list = [
        Order.order_number, Order.client_name, Order.client_phone, Order.address
    ]

    column_sortable_list = [
        Order.id, Order.status, Order.total_price, Order.created_at, Order.work_date
    ]

    column_filters = [
        Order.status,
        Order.viloyat_id,
        Order.tuman_id,
        Order.master_id,
        Order.usta_id,
        Order.asphalt_type_id,
        Order.work_date,
        Order.created_at,
    ]

    column_labels = {
        Order.viloyat_id: "Viloyat",
        Order.tuman_id: "Tuman",
        Order.region_id: "Hudud",
        Order.master_id: "Master",
        Order.usta_id: "Usta",
        Order.zavod_id: "Zavod",
        Order.asphalt_type_id: "Asfalt turi",
        Order.client_id: "Klient",
    }

    form_columns = [
        Order.client_id,
        Order.client_name,
        Order.client_phone,
        Order.viloyat_id,
        Order.tuman_id,
        Order.region_id,
        Order.address,
        Order.latitude,
        Order.longitude,
        Order.area_m2,
        Order.asphalt_type_id,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.usta_wage,
        Order.master_commission,
        Order.status,
        Order.work_date,
        Order.notes,
        Order.master_id,
        Order.usta_id,
    ]

    form_args = {
        "client_id": {"description": "Klient User.id (Foydalanuvchilar ro'yxatidan tekshiring)"},
        "client_name": {"description": "Klient ismi"},
        "client_phone": {"description": "998901234567 formatida"},
        "address": {"description": "To'liq manzil"},
        "area_m2": {"description": "Maydon m² (masalan: 500)"},
        "total_price": {"description": "Kelishilgan summa (so'm)"},
        "advance_paid": {"description": "Zaklad/avans (so'm)"},
        "usta_wage": {"description": "Usta ish haqi (so'm)"},
        "master_commission": {"description": "Master komissiyasi (so'm)"},
        "work_date": {"description": "Ish sanasi"},
    }

    can_create = True
    page_size = 25

    async def on_model_change(self, data, model, is_created, request):
        """Auto-generate order_number on create."""
        if is_created and not getattr(model, "order_number", None):
            from datetime import datetime
            from sqlalchemy import func, select
            from app.db.session import async_session_maker
            today = datetime.now().strftime("%Y%m%d")
            async with async_session_maker() as session:
                result = await session.execute(
                    select(func.count(Order.id)).where(
                        Order.order_number.like(f"AVT-{today}-%")
                    )
                )
                count = result.scalar_one() + 1
            model.order_number = f"AVT-{today}-{count:04d}"
            if not model.status:
                model.status = OrderStatus.NEW
        return await super().on_model_change(data, model, is_created, request)

    column_select_related_list = [
        "master", "usta", "client", "asphalt_type", "viloyat", "tuman_rel", "region"
    ]

    def _fmt_master(m, a):
        try:
            return f"{m.master.full_name} ({m.master.phone})" if m.master else "-"
        except DetachedInstanceError:
            return f"#{m.master_id}" if m.master_id else "-"

    def _fmt_usta(m, a):
        try:
            return f"{m.usta.full_name} ({m.usta.phone})" if m.usta else "-"
        except DetachedInstanceError:
            return f"#{m.usta_id}" if m.usta_id else "-"

    def _fmt_expenses(m, a):
        items = getattr(m, "expenses", []) or []
        if not items:
            return "-"
        return " | ".join(
            f"{e.expense_type}: {float(e.amount):,.0f} so'm" for e in items[:20]
        )

    def _fmt_materials(m, a):
        items = getattr(m, "material_requests", []) or []
        if not items:
            return "-"
        return " | ".join(
            f"#{mr.id} {mr.amount_tonnes}t {mr.status}" for mr in items[:20]
        )

    def _fmt_viloyat(m, a):
        try:
            return m.viloyat.name if m.viloyat else "-"
        except DetachedInstanceError:
            return f"#{m.viloyat_id}" if m.viloyat_id else "-"

    def _fmt_tuman(m, a):
        try:
            return m.tuman_rel.name if m.tuman_rel else "-"
        except DetachedInstanceError:
            return f"#{m.tuman_id}" if m.tuman_id else "-"

    def _fmt_asphalt(m, a):
        try:
            return m.asphalt_type.name if m.asphalt_type else "-"
        except DetachedInstanceError:
            return f"#{m.asphalt_type_id}" if m.asphalt_type_id else "-"

    def _fmt_client(m, a):
        try:
            return f"{m.client.full_name} ({m.client.phone})" if m.client else "-"
        except DetachedInstanceError:
            return m.client_name or "-"

    def _fmt_region(m, a):
        try:
            return m.region.name if m.region else "-"
        except DetachedInstanceError:
            return f"#{m.region_id}" if m.region_id else "-"

    column_formatters = {
        Order.master_id: _fmt_master,
        Order.usta_id: _fmt_usta,
        Order.viloyat_id: _fmt_viloyat,
        Order.tuman_id: _fmt_tuman,
        Order.asphalt_type_id: _fmt_asphalt,
    }

    column_formatters_detail = {
        Order.master_id: _fmt_master,
        Order.usta_id: _fmt_usta,
        Order.client_id: _fmt_client,
        Order.viloyat_id: _fmt_viloyat,
        Order.tuman_id: _fmt_tuman,
        Order.region_id: _fmt_region,
        Order.asphalt_type_id: _fmt_asphalt,
        "expenses": _fmt_expenses,
        "material_requests": _fmt_materials,
    }


class ExpenseAdmin(ModelView, model=Expense):
    name = "Xarajat"
    name_plural = "Xarajatlar"
    icon = "fa-solid fa-money-bill-wave"

    column_list = [
        Expense.id,
        Expense.order_id,
        Expense.expense_type,
        Expense.amount,
        Expense.description,
        Expense.created_at,
    ]
    column_searchable_list = [Expense.description]
    column_sortable_list = [Expense.id, Expense.amount, Expense.expense_type, Expense.created_at]
    column_filters = [Expense.expense_type]

    form_columns = [Expense.order_id, Expense.expense_type, Expense.amount, Expense.description]
    page_size = 25


class MaterialRequestAdmin(ModelView, model=MaterialRequest):
    name = "Material so'rov"
    name_plural = "Material so'rovlar"
    icon = "fa-solid fa-boxes-stacked"

    column_list = [
        MaterialRequest.id,
        MaterialRequest.order_id,
        MaterialRequest.usta_id,
        MaterialRequest.amount_tonnes,
        MaterialRequest.material_price,
        MaterialRequest.delivery_price,
        MaterialRequest.extra_cost,
        MaterialRequest.status,
        MaterialRequest.created_at,
    ]
    column_sortable_list = [MaterialRequest.id, MaterialRequest.status, MaterialRequest.created_at]
    column_filters = [MaterialRequest.status]

    form_columns = [
        MaterialRequest.order_id,
        MaterialRequest.usta_id,
        MaterialRequest.amount_tonnes,
        MaterialRequest.material_price,
        MaterialRequest.delivery_price,
        MaterialRequest.extra_cost,
        MaterialRequest.status,
        MaterialRequest.notes,
    ]
    page_size = 25
    
    # Eager load relationships to prevent N+1 queries
    column_select_related_list = ["order", "usta", "zavod", "assigned_zavod"]


class AsphaltCategoryAdmin(ModelView, model=AsphaltCategory):
    name = "Kategoriya"
    name_plural = "Kategoriyalar"
    icon = "fa-solid fa-folder-tree"

    column_list = [
        AsphaltCategory.id,
        AsphaltCategory.name,
        AsphaltCategory.description,
        AsphaltCategory.is_active,
        AsphaltCategory.created_at,
    ]
    
    column_searchable_list = [AsphaltCategory.name, AsphaltCategory.description]
    column_sortable_list = [AsphaltCategory.id, AsphaltCategory.name, AsphaltCategory.is_active]
    column_filters = [AsphaltCategory.is_active]
    
    form_columns = [
        AsphaltCategory.name,
        AsphaltCategory.description,
        AsphaltCategory.is_active
    ]
    
    page_size = 25


class AsphaltSubCategoryAdmin(ModelView, model=AsphaltSubCategory):
    name = "Sub-kategoriya"
    name_plural = "Sub-kategoriyalar"
    icon = "fa-solid fa-folder-open"

    column_list = [
        AsphaltSubCategory.id,
        AsphaltSubCategory.category_id,
        AsphaltSubCategory.name,
        AsphaltSubCategory.description,
        AsphaltSubCategory.is_active,
        AsphaltSubCategory.created_at,
    ]
    
    column_searchable_list = [AsphaltSubCategory.name, AsphaltSubCategory.description]
    column_sortable_list = [AsphaltSubCategory.id, AsphaltSubCategory.name, AsphaltSubCategory.is_active]
    column_filters = [AsphaltSubCategory.category_id, AsphaltSubCategory.is_active]
    
    column_labels = {
        AsphaltSubCategory.category_id: "Kategoriya"
    }
    
    form_columns = [
        AsphaltSubCategory.category_id,
        AsphaltSubCategory.name,
        AsphaltSubCategory.description,
        AsphaltSubCategory.is_active
    ]
    
    column_select_related_list = ["category"]
    
    column_formatters = {
        AsphaltSubCategory.category_id: lambda m, a: m.category.name if m.category else "-",
    }
    
    page_size = 25


class AsphaltTypeAdmin(ModelView, model=AsphaltType):
    name = "Material"
    name_plural = "Materiallar"
    icon = "fa-solid fa-road"

    column_list = [
        AsphaltType.id,
        AsphaltType.subcategory_id,
        AsphaltType.name,
        AsphaltType.cost_price_per_m2,
        AsphaltType.price_per_m2,
        AsphaltType.is_active,
        AsphaltType.created_at,
    ]
    
    column_searchable_list = [AsphaltType.name]
    column_sortable_list = [
        AsphaltType.id, 
        AsphaltType.cost_price_per_m2, 
        AsphaltType.price_per_m2, 
        AsphaltType.is_active
    ]
    
    column_filters = [
        AsphaltType.subcategory_id,
        AsphaltType.is_active
    ]
    
    column_labels = {
        AsphaltType.subcategory_id: "Sub-kategoriya",
        AsphaltType.cost_price_per_m2: "Tannarxi (so'm/m²)",
        AsphaltType.price_per_m2: "Sotuvdagi narxi (so'm/m²)",
    }

    form_columns = [
        AsphaltType.subcategory_id,
        AsphaltType.name, 
        AsphaltType.cost_price_per_m2, 
        AsphaltType.price_per_m2, 
        AsphaltType.is_active
    ]
    
    column_select_related_list = ["subcategory"]
    
    column_formatters = {
        AsphaltType.subcategory_id: lambda m, a: f"{m.subcategory.category.name} → {m.subcategory.name}" if m.subcategory else "-",
    }
    
    page_size = 25


# ══════════════════════════════════════════════════════════════════════════════
# MARKETPLACE ADMIN VIEWS
# ══════════════════════════════════════════════════════════════════════════════


class ShopCategoryAdmin(ModelView, model=Category):
    name = "Do'kon Kategoriya"
    name_plural = "Do'kon Kategoriyalar"
    icon = "fa-solid fa-folder"

    column_list = [
        Category.id,
        Category.name_uz,
        Category.name_ru,
        Category.name_en,
        Category.order,
        Category.is_active,
    ]
    column_searchable_list = [Category.name_uz, Category.name_ru, Category.name_en]
    column_sortable_list = [Category.id, Category.name_uz, Category.order, Category.is_active]
    column_filters = [Category.is_active]

    column_labels = {
        Category.name_uz: "Nomi (Lotin)",
        Category.name_ru: "Название (Рус)",
        Category.name_en: "Name (En)",
        Category.order: "Tartib",
    }

    form_columns = [
        Category.name_uz,
        Category.name_ru,
        Category.name_en,
        Category.parent_id,
        Category.image,
        Category.order,
        Category.is_active,
    ]
    page_size = 25


class ProductAdmin(ModelView, model=Product):
    name = "Mahsulot"
    name_plural = "Mahsulotlar"
    icon = "fa-solid fa-box"

    column_list = [
        Product.id,
        Product.name_uz,
        Product.name_ru,
        Product.price,
        Product.stock,
        Product.category_id,
        Product.is_featured,
        Product.is_active,
    ]
    column_searchable_list = [Product.name_uz, Product.name_ru, Product.name_en]
    column_sortable_list = [
        Product.id, Product.name_uz, Product.price,
        Product.stock, Product.is_featured, Product.is_active,
    ]
    column_filters = [Product.category_id, Product.is_featured, Product.is_active]

    column_labels = {
        Product.name_uz: "Nomi (Lotin)",
        Product.name_ru: "Название (Рус)",
        Product.name_en: "Name (En)",
        Product.description_uz: "Tavsif (Lotin)",
        Product.description_ru: "Описание (Рус)",
        Product.description_en: "Description (En)",
        Product.price: "Narxi",
        Product.discount_value: "Chegirma",
        Product.discount_type: "Chegirma turi",
        Product.stock: "Ombor",
        Product.category_id: "Kategoriya",
        Product.images: "Rasmlar (URL, vergul bilan)",
    }

    form_columns = [
        Product.name_uz,
        Product.name_ru,
        Product.name_en,
        Product.description_uz,
        Product.description_ru,
        Product.description_en,
        Product.price,
        Product.discount_value,
        Product.discount_type,
        Product.category_id,
        Product.images,
        Product.stock,
        Product.is_featured,
        Product.is_active,
    ]

    column_select_related_list = ["category"]
    column_formatters = {
        Product.category_id: lambda m, a: m.category.name_uz if m.category else "—",
    }
    page_size = 25


class PortfolioAdmin(ModelView, model=Portfolio):
    name = "Portfolio"
    name_plural = "Portfoliolar"
    icon = "fa-solid fa-images"

    column_list = [
        Portfolio.id,
        Portfolio.title_uz,
        Portfolio.title_ru,
        Portfolio.year,
        Portfolio.location,
        Portfolio.order,
        Portfolio.is_active,
    ]
    column_searchable_list = [Portfolio.title_uz, Portfolio.title_ru, Portfolio.location]
    column_sortable_list = [
        Portfolio.id, Portfolio.title_uz, Portfolio.year,
        Portfolio.order, Portfolio.is_active,
    ]
    column_filters = [Portfolio.is_active, Portfolio.year]

    column_labels = {
        Portfolio.title_uz: "Sarlavha (Lotin)",
        Portfolio.title_ru: "Заголовок (Рус)",
        Portfolio.title_en: "Title (En)",
        Portfolio.description_uz: "Tavsif (Lotin)",
        Portfolio.description_ru: "Описание (Рус)",
        Portfolio.description_en: "Description (En)",
        Portfolio.location: "Joylashuv",
        Portfolio.client_name: "Buyurtmachi",
        Portfolio.year: "Yil",
        Portfolio.images: "Rasmlar (URL, vergul bilan)",
        Portfolio.order: "Tartib",
    }

    form_columns = [
        Portfolio.title_uz,
        Portfolio.title_ru,
        Portfolio.title_en,
        Portfolio.description_uz,
        Portfolio.description_ru,
        Portfolio.description_en,
        Portfolio.location,
        Portfolio.client_name,
        Portfolio.year,
        Portfolio.images,
        Portfolio.order,
        Portfolio.is_active,
    ]
    page_size = 25


class MarketOrderAdmin(ModelView, model=MarketOrder):
    name = "Do'kon Buyurtma"
    name_plural = "Do'kon Buyurtmalar"
    icon = "fa-solid fa-receipt"

    column_list = [
        MarketOrder.id,
        MarketOrder.customer_phone,
        MarketOrder.total_price,
        MarketOrder.status,
        MarketOrder.created_at,
    ]
    column_sortable_list = [MarketOrder.id, MarketOrder.total_price, MarketOrder.created_at]
    column_filters = [MarketOrder.status]
    column_searchable_list = [MarketOrder.customer_phone]

    column_labels = {
        MarketOrder.customer_phone: "Telefon",
        MarketOrder.total_price: "Jami",
        MarketOrder.status: "Holat",
    }

    form_columns = [MarketOrder.status, MarketOrder.comment]
    page_size = 25


class ViloyatAdmin(ModelView, model=Viloyat):
    name = "Viloyat"
    name_plural = "Viloyatlar"
    icon = "fa-solid fa-map"

    column_list = [Viloyat.id, Viloyat.name, Viloyat.is_active, Viloyat.created_at]
    column_searchable_list = [Viloyat.name]
    column_sortable_list = [Viloyat.id, Viloyat.name, Viloyat.is_active]
    column_filters = [Viloyat.is_active]

    form_columns = [Viloyat.name, Viloyat.is_active]
    page_size = 50


class TumanAdmin(ModelView, model=Tuman):
    name = "Tuman"
    name_plural = "Tumanlar"
    icon = "fa-solid fa-location-dot"

    column_list = [
        Tuman.id,
        Tuman.viloyat_id,
        Tuman.name,
        Tuman.is_active,
        Tuman.created_at,
    ]
    column_searchable_list = [Tuman.name]
    column_sortable_list = [Tuman.id, Tuman.name, Tuman.viloyat_id, Tuman.is_active]
    column_filters = [Tuman.viloyat_id, Tuman.is_active]

    column_labels = {Tuman.viloyat_id: "Viloyat"}

    form_columns = [Tuman.viloyat_id, Tuman.name, Tuman.is_active]
    page_size = 100

    column_select_related_list = ["viloyat"]
    column_formatters = {
        Tuman.viloyat_id: lambda m, a: m.viloyat.name if m.viloyat else "-",
    }


class RegionAdmin(ModelView, model=Region):
    name = "Hudud"
    name_plural = "Hududlar (eski)"
    icon = "fa-solid fa-map-location-dot"

    column_list = [Region.id, Region.name, Region.viloyat, Region.tuman, Region.is_active, Region.created_at]
    column_searchable_list = [Region.name, Region.viloyat, Region.tuman]
    column_sortable_list = [Region.id, Region.name, Region.is_active]
    column_filters = [Region.is_active]

    form_columns = [Region.name, Region.viloyat, Region.tuman, Region.is_active]
    page_size = 25


class ZavodAdmin(ModelView, model=Zavod):
    name = "Zavod"
    name_plural = "Zavodlar"
    icon = "fa-solid fa-industry"

    column_list = [
        Zavod.id,
        Zavod.name,
        Zavod.tafsif,
        Zavod.is_active,
        Zavod.created_at,
    ]
    
    column_searchable_list = [Zavod.name, Zavod.tafsif]
    column_sortable_list = [Zavod.id, Zavod.name, Zavod.is_active, Zavod.created_at]
    column_filters = [Zavod.is_active, Zavod.created_at]

    form_columns = [Zavod.name, Zavod.tafsif, Zavod.is_active]
    page_size = 25
