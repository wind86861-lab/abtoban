from sqladmin import ModelView

from app.db.models import (
    AsphaltType,
    Expense,
    MaterialRequest,
    Order,
    Region,
    User,
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
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.full_name, User.username, User.phone]
    column_sortable_list = [User.id, User.role, User.is_active, User.created_at]
    column_filters = [User.role, User.is_active]

    form_columns = [User.full_name, User.username, User.phone, User.role, User.is_active, User.region_id]
    form_include_pk = False

    can_create = False
    can_delete = False
    page_size = 25


class OrderAdmin(ModelView, model=Order):
    name = "Zakaz"
    name_plural = "Zakazlar"
    icon = "fa-solid fa-file-invoice"

    column_list = [
        Order.id,
        Order.order_number,
        Order.client_name,
        Order.client_phone,
        Order.address,
        Order.area_m2,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.status,
        Order.work_date,
        Order.created_at,
    ]
    column_searchable_list = [Order.order_number, Order.client_name, Order.client_phone, Order.address]
    column_sortable_list = [Order.id, Order.status, Order.total_price, Order.created_at]
    column_filters = [Order.status]

    form_columns = [
        Order.client_name,
        Order.client_phone,
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
        Order.region_id,
    ]

    can_create = False
    page_size = 25


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


class AsphaltTypeAdmin(ModelView, model=AsphaltType):
    name = "Asfalt turi"
    name_plural = "Asfalt turlari"
    icon = "fa-solid fa-road"

    column_list = [
        AsphaltType.id,
        AsphaltType.name,
        AsphaltType.price_per_m2,
        AsphaltType.is_active,
        AsphaltType.created_at,
    ]
    column_searchable_list = [AsphaltType.name]
    column_sortable_list = [AsphaltType.id, AsphaltType.price_per_m2, AsphaltType.is_active]

    form_columns = [AsphaltType.name, AsphaltType.price_per_m2, AsphaltType.is_active]
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
