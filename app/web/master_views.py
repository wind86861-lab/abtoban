from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
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
        Order.address,
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
        Order.region,
        Order.address,
        Order.latitude,
        Order.longitude,
        Order.area_m2,
        Order.asphalt_type,
        Order.total_price,
        Order.advance_paid,
        Order.debt,
        Order.master_commission,
        Order.usta_wage,
        Order.status,
        Order.work_date,
        Order.notes,
        Order.created_at,
        Order.updated_at,
    ]
    
    form_columns = [
        Order.client_name,
        Order.client_phone,
        Order.region,
        Order.address,
        Order.latitude,
        Order.longitude,
        Order.area_m2,
        Order.asphalt_type,
        Order.total_price,
        Order.advance_paid,
        Order.master_commission,
        Order.usta_wage,
        Order.work_date,
        Order.notes,
        Order.status,
    ]
    
    column_searchable_list = [Order.order_number, Order.client_name, Order.client_phone]
    column_sortable_list = [Order.id, Order.status, Order.total_price, Order.created_at, Order.work_date]
    column_filters = [Order.status, Order.work_date, Order.created_at]
    
    column_labels = {
        Order.order_number: "Zakaz №",
        Order.client_name: "Klient Ismi",
        Order.client_phone: "Telefon",
        Order.address: "Manzil",
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
    
    # Allow Masters to create and edit their own orders
    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    page_size = 25
    
    async def insert_model(self, request: Request, data: dict) -> Order:
        """Override to set master_id automatically"""
        user_id = request.session.get('user_id')
        if user_id:
            data['master_id'] = user_id
        
        # Calculate debt
        total_price = data.get('total_price', 0)
        advance_paid = data.get('advance_paid', 0)
        data['debt'] = total_price - advance_paid
        
        return await super().insert_model(request, data)
    
    async def update_model(self, request: Request, pk: str, data: dict) -> Order:
        """Override to recalculate debt"""
        total_price = data.get('total_price', 0)
        advance_paid = data.get('advance_paid', 0)
        if total_price is not None and advance_paid is not None:
            data['debt'] = total_price - advance_paid
        
        return await super().update_model(request, pk, data)
    
    def is_accessible(self, request: Request) -> bool:
        """Check if user is a master"""
        user_role = request.session.get('user_role')
        return user_role == 'master'
    
    def get_query(self, request: Request):
        """Filter to show only this master's orders"""
        query = super().get_query(request)
        user_id = request.session.get('user_id')
        if user_id:
            query = query.where(Order.master_id == user_id)
        return query
    
    def get_count_query(self, request: Request):
        """Filter count to show only this master's orders"""
        query = super().get_count_query(request)
        user_id = request.session.get('user_id')
        if user_id:
            query = query.where(Order.master_id == user_id)
        return query
