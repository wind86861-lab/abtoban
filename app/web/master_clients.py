from sqladmin import BaseView, expose
from sqlalchemy import func, select
from starlette.requests import Request

from app.db.models import Order
from app.db.session import async_session_maker


class MasterClientsView(BaseView):
    name = "Klientlar"
    icon = "fa-solid fa-users"

    @expose("/clients", methods=["GET"])
    async def clients_page(self, request: Request):
        """Master's clients list with order history"""
        user_id = request.session.get('user_id')
        
        if not user_id:
            return await self.templates.TemplateResponse(
                request,
                "error.html",
                context={"error": "Unauthorized"}
            )
        
        async with async_session_maker() as session:
            # Get unique clients with their order stats
            clients_query = await session.execute(
                select(
                    Order.client_name,
                    Order.client_phone,
                    func.count(Order.id).label('order_count'),
                    func.sum(Order.total_price).label('total_revenue'),
                    func.sum(Order.master_commission).label('total_commission'),
                    func.max(Order.created_at).label('last_order_date'),
                )
                .where(Order.master_id == user_id)
                .group_by(Order.client_phone, Order.client_name)
                .order_by(func.count(Order.id).desc())
            )
            
            clients = []
            for row in clients_query.all():
                clients.append({
                    'name': row.client_name or 'Noma\'lum',
                    'phone': row.client_phone,
                    'order_count': row.order_count,
                    'total_revenue': row.total_revenue or 0,
                    'total_commission': row.total_commission or 0,
                    'last_order_date': row.last_order_date,
                })
        
        return await self.templates.TemplateResponse(
            request,
            "master_clients.html",
            context={
                "clients": clients,
            }
        )
