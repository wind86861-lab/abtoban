from sqladmin import ModelView
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from app.db.models import Order, User, UserRole, OrderStatus, Region, AsphaltType


class MasterOrderAdmin(ModelView, model=Order):
    name = "Zakaz"
    name_plural = "Mening Zakazlarim"
    icon = "fa-solid fa-clipboard-list"
    
    column_list = [
        Order.id,
        Order.order_number,
        Order.client_name,
        Order.client_phone,
        Order.viloyat_id,
        Order.tuman_id,
        Order.usta_id,
        Order.area_m2,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.master_commission,
        Order.status,
        Order.work_date,
        Order.created_at,
    ]

    column_details_list = [
        Order.id,
        Order.order_number,
        Order.client_name,
        Order.client_phone,
        Order.viloyat_id,
        Order.tuman_id,
        Order.region,
        Order.address,
        Order.latitude,
        Order.longitude,
        Order.usta_id,
        Order.area_m2,
        Order.asphalt_type,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.master_commission,
        Order.usta_wage,
        Order.usta_wage_note,
        Order.status,
        Order.work_date,
        Order.notes,
        Order.created_at,
        Order.updated_at,
        "expenses",
        "material_requests",
    ]
    
    column_searchable_list = [Order.order_number, Order.client_name, Order.client_phone, Order.address]
    column_sortable_list = [Order.id, Order.status, Order.total_price, Order.created_at, Order.work_date]
    column_filters = [
        Order.status,
        Order.viloyat_id,
        Order.tuman_id,
        Order.usta_id,
        Order.work_date,
        Order.created_at,
    ]

    
    column_labels = {
        Order.order_number: "Zakaz №",
        Order.client_name: "Klient Ismi",
        Order.client_phone: "Telefon",
        Order.address: "Manzil",
        Order.viloyat_id: "Viloyat",
        Order.tuman_id: "Tuman",
        Order.usta_id: "Usta",
        Order.area_m2: "Maydon (m²)",
        Order.total_price: "Jami Summa",
        Order.advance_paid: "Oldindan To'lov",
        Order.debt: "Qarz",
        Order.master_commission: "Mening Komissiyam",
        Order.usta_wage: "Usta Maoshi",
        Order.status: "Holat",
        Order.work_date: "Ish Sanasi",
        Order.notes: "Izohlar",
        Order.region: "Hudud",
        Order.asphalt_type: "Asfalt Turi",
        Order.created_at: "Yaratilgan",
        Order.updated_at: "O'zgartirilgan",
    }

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

    column_formatters = {}

    column_formatters_detail = {
        "expenses": _fmt_expenses,
        "material_requests": _fmt_materials,
    }
    
    # Security: Masters can only VIEW their orders. All mutations go through
    # dedicated custom pages (confirm, status change, usta assign, expenses).
    can_create = False
    can_edit = False
    can_delete = False
    can_export = False
    can_view_details = True
    page_size = 25
    
    def is_accessible(self, request: Request) -> bool:
        """Check if user is a master"""
        user_role = request.session.get('user_role')
        return user_role == 'master'
    
    def list_query(self, request: Request):
        """Filter to show only this master's orders, with eager-loaded relationships."""
        user_id = request.session.get('user_id') or request.session.get('master_user_id')
        q = (
            select(Order)
            .options(
                selectinload(Order.viloyat),
                selectinload(Order.tuman_rel),
                selectinload(Order.usta),
                selectinload(Order.asphalt_type),
                selectinload(Order.region),
            )
        )
        if user_id:
            q = q.where(Order.master_id == user_id)
        return q

    def count_query(self, request: Request):
        """Count only this master's orders."""
        user_id = request.session.get('user_id') or request.session.get('master_user_id')
        q = select(func.count(Order.id))
        if user_id:
            q = q.where(Order.master_id == user_id)
        return q
