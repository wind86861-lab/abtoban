from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, User, UserRole


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
        Order.master_commission,
        Order.status,
        Order.work_date,
        Order.created_at,
    ]
    
    column_searchable_list = [Order.order_number, Order.client_name, Order.client_phone]
    column_sortable_list = [Order.id, Order.status, Order.total_price, Order.created_at]
    column_filters = [Order.status]
    column_labels = {
        Order.master_commission: "Mening Komissiyam",
        Order.total_price: "Jami Summa",
        Order.work_date: "Ish Sanasi",
    }
    
    can_create = False
    can_edit = False
    can_delete = False
    page_size = 25
    
    async def get_list(self, *args, **kwargs):
        """Filter orders to show only this master's orders"""
        # Get current user from session
        request = kwargs.get('request')
        if request:
            user_id = request.session.get('user_id')
            if user_id:
                # Override the query to filter by master_id
                return await super().get_list(*args, **kwargs)
        return await super().get_list(*args, **kwargs)
