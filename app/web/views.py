from sqladmin import ModelView

from app.db.models import (
    AsphaltType,
    Expense,
    MaterialRequest,
    Order,
    Region,
    User,
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
        User.username,
        User.phone,
        User.role,
        User.region_id,
        User.is_active,
        User.created_at,
    ]
    
    column_searchable_list = [User.full_name, User.username, User.phone]
    
    column_sortable_list = [
        User.id, 
        User.role, 
        User.is_active, 
        User.created_at,
        User.full_name
    ]
    
    column_filters = [
        User.role, 
        User.is_active,
        User.region_id,
        User.created_at
    ]
    
    column_labels = {
        User.region_id: "Viloyat"
    }

    form_columns = [
        User.full_name, 
        User.username, 
        User.phone, 
        User.role, 
        User.is_active, 
        User.region_id
    ]
    
    form_include_pk = False
    can_create = False
    can_delete = False
    page_size = 25
    
    column_select_related_list = ["region"]
    
    column_formatters = {
        User.region_id: lambda m, a: m.region.name if m.region else "-",
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
        Order.region_id,
        Order.tuman,
        Order.address,
        Order.master_id,
        Order.usta_id,
        Order.asphalt_type_id,
        Order.area_m2,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.status,
        Order.work_date,
        Order.created_at,
    ]
    
    column_searchable_list = [
        Order.order_number, 
        Order.client_name, 
        Order.client_phone, 
        Order.address,
        Order.tuman
    ]
    
    column_sortable_list = [
        Order.id, 
        Order.status, 
        Order.total_price, 
        Order.created_at,
        Order.work_date
    ]
    
    column_filters = [
        Order.status,
        Order.region_id,
        Order.tuman,
        Order.master_id,
        Order.usta_id,
        Order.asphalt_type_id,
        Order.work_date,
        Order.created_at
    ]
    
    column_labels = {
        Order.region_id: "Viloyat",
        Order.tuman: "Tuman",
        Order.master_id: "Master",
        Order.usta_id: "Usta",
        Order.asphalt_type_id: "Asfalt turi"
    }

    form_columns = [
        Order.client_name,
        Order.client_phone,
        Order.region_id,
        Order.tuman,
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
    
    # Eager load relationships to prevent N+1 queries
    column_select_related_list = ["master", "usta", "asphalt_type", "region"]
    
    column_formatters = {
        Order.master_id: lambda m, a: f"{m.master.full_name} ({m.master.phone})" if m.master else "-",
        Order.usta_id: lambda m, a: f"{m.usta.full_name} ({m.usta.phone})" if m.usta else "-",
        Order.region_id: lambda m, a: m.region.name if m.region else "-",
        Order.asphalt_type_id: lambda m, a: m.asphalt_type.name if m.asphalt_type else "-",
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


class AsphaltTypeAdmin(ModelView, model=AsphaltType):
    name = "Asfalt turi"
    name_plural = "Asfalt turlari"
    icon = "fa-solid fa-road"

    column_list = [
        AsphaltType.id,
        AsphaltType.name,
        AsphaltType.cost_price_per_m2,
        AsphaltType.price_per_m2,
        AsphaltType.is_active,
        AsphaltType.created_at,
    ]
    column_searchable_list = [AsphaltType.name]
    column_sortable_list = [AsphaltType.id, AsphaltType.cost_price_per_m2, AsphaltType.price_per_m2, AsphaltType.is_active]
    column_labels = {
        AsphaltType.cost_price_per_m2: "Tannarxi (so'm/m²)",
        AsphaltType.price_per_m2: "Sotuvdagi narxi (so'm/m²)",
    }

    form_columns = [AsphaltType.name, AsphaltType.cost_price_per_m2, AsphaltType.price_per_m2, AsphaltType.is_active]
    page_size = 25


class RegionAdmin(ModelView, model=Region):
    name = "Hudud"
    name_plural = "Hududlar"
    icon = "fa-solid fa-map-location-dot"

    column_list = [Region.id, Region.name, Region.is_active, Region.created_at]
    column_searchable_list = [Region.name]
    column_sortable_list = [Region.id, Region.name, Region.is_active]

    form_columns = [Region.name, Region.is_active]
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
