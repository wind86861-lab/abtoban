from sqladmin import ModelView

from app.db.models import (
    AsphaltCategory,
    AsphaltSubCategory,
    AsphaltType,
    Expense,
    MaterialRequest,
    Order,
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
        "viloyat": {"label": "Viloyat"},
        "tuman_rel": {"label": "Tuman"},
        "region": {"label": "Hudud (eski)"},
        "zavod": {"label": "Zavod"},
    }

    form_columns = [
        User.full_name,
        User.username,
        User.phone,
        User.role,
        User.is_active,
        "viloyat",
        "tuman_rel",
        "region",
        "zavod",
    ]

    form_include_pk = False
    can_create = False
    can_delete = False
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
        Order.client_name,
        Order.client_phone,
        Order.viloyat_id,
        Order.tuman_id,
        Order.region_id,
        Order.address,
        Order.area_m2,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.status,
        Order.work_date,
        Order.notes,
        Order.master_id,
        Order.usta_id,
        Order.asphalt_type_id,
    ]

    can_create = False
    page_size = 25

    column_select_related_list = [
        "master", "usta", "client", "asphalt_type", "viloyat", "tuman_rel", "region"
    ]

    def _fmt_master(m, a):
        return f"{m.master.full_name} ({m.master.phone})" if m.master else "-"

    def _fmt_usta(m, a):
        return f"{m.usta.full_name} ({m.usta.phone})" if m.usta else "-"

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

    column_formatters = {
        Order.master_id: _fmt_master,
        Order.usta_id: _fmt_usta,
        Order.viloyat_id: lambda m, a: m.viloyat.name if m.viloyat else "-",
        Order.tuman_id: lambda m, a: m.tuman_rel.name if m.tuman_rel else "-",
        Order.asphalt_type_id: lambda m, a: m.asphalt_type.name if m.asphalt_type else "-",
    }

    column_formatters_detail = {
        Order.master_id: _fmt_master,
        Order.usta_id: _fmt_usta,
        Order.client_id: lambda m, a: f"{m.client.full_name} ({m.client.phone})" if m.client else "-",
        Order.viloyat_id: lambda m, a: m.viloyat.name if m.viloyat else "-",
        Order.tuman_id: lambda m, a: m.tuman_rel.name if m.tuman_rel else "-",
        Order.region_id: lambda m, a: m.region.name if m.region else "-",
        Order.asphalt_type_id: lambda m, a: m.asphalt_type.name if m.asphalt_type else "-",
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
