from datetime import datetime, timedelta
from decimal import Decimal

from sqladmin import BaseView, expose
from sqlalchemy import func, select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.db.models import Order, OrderStatus
from app.db.session import async_session_maker


class MasterCommissionView(BaseView):
    name = "Komissiya Hisoboti"
    icon = "fa-solid fa-money-bill-trend-up"

    @expose("/commission", methods=["GET"])
    async def commission_page(self, request: Request):
        """Master's commission report with detailed breakdown"""
        user_id = request.session.get('user_id') or request.session.get('master_user_id')
        if not user_id:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)
        
        async with async_session_maker() as session:
            # Overall commission stats
            total_stats = await session.execute(
                select(
                    func.count(Order.id),
                    func.sum(Order.total_price),
                    func.sum(Order.master_commission),
                    func.sum(Order.advance_paid),
                    func.sum(Order.debt),
                )
                .where(
                    Order.master_id == user_id,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            row = total_stats.first()
            total_orders = row[0] or 0
            total_revenue = row[1] or Decimal("0")
            total_commission = row[2] or Decimal("0")
            total_advance = row[3] or Decimal("0")
            total_debt = row[4] or Decimal("0")
            
            # This month
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            month_stats = await session.execute(
                select(
                    func.count(Order.id),
                    func.sum(Order.master_commission),
                )
                .where(
                    Order.master_id == user_id,
                    Order.created_at >= month_start,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            month_row = month_stats.first()
            month_orders = month_row[0] or 0
            month_commission = month_row[1] or Decimal("0")
            
            # Last 7 days
            week_start = now - timedelta(days=7)
            week_stats = await session.execute(
                select(
                    func.count(Order.id),
                    func.sum(Order.master_commission),
                )
                .where(
                    Order.master_id == user_id,
                    Order.created_at >= week_start,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            week_row = week_stats.first()
            week_orders = week_row[0] or 0
            week_commission = week_row[1] or Decimal("0")
            
            # Commission by status
            status_breakdown = await session.execute(
                select(
                    Order.status,
                    func.count(Order.id),
                    func.sum(Order.master_commission),
                )
                .where(Order.master_id == user_id)
                .group_by(Order.status)
            )
            
            status_data = []
            for status, count, commission in status_breakdown.all():
                status_data.append({
                    'status': status.value,
                    'count': count,
                    'commission': commission or Decimal("0"),
                })
            
            # Recent commission history (last 10 orders)
            recent_orders = await session.execute(
                select(Order)
                .where(Order.master_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(10)
            )
            
            commission_history = []
            for order in recent_orders.scalars().all():
                commission_history.append({
                    'order_number': order.order_number,
                    'client_name': order.client_name or order.client_phone,
                    'total_price': order.total_price or Decimal("0"),
                    'commission': order.master_commission or Decimal("0"),
                    'status': order.status.value,
                    'date': order.created_at,
                })
        
        return await self.templates.TemplateResponse(
            request,
            "master_commission.html",
            context={
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_commission": total_commission,
                "total_advance": total_advance,
                "total_debt": total_debt,
                "month_orders": month_orders,
                "month_commission": month_commission,
                "week_orders": week_orders,
                "week_commission": week_commission,
                "status_breakdown": status_data,
                "commission_history": commission_history,
            }
        )
