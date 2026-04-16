from decimal import Decimal
from typing import Any

from sqladmin import BaseView, expose
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderStatus, User
from app.db.session import async_session_maker


class MasterDashboardView(BaseView):
    name = "Dashboard"
    icon = "fa-solid fa-chart-pie"

    @expose("/dashboard", methods=["GET"])
    async def dashboard_page(self, request):
        """Master dashboard showing orders and commission stats"""
        user_id = request.session.get('user_id')
        
        if not user_id:
            return await self.templates.TemplateResponse(
                request,
                "error.html",
                context={"error": "Unauthorized"}
            )
        
        async with async_session_maker() as session:
            stats = await self._calculate_master_stats(session, user_id)
        
        return await self.templates.TemplateResponse(
            request,
            "master_dashboard.html",
            context={
                "stats": stats,
            }
        )

    async def _calculate_master_stats(self, session: AsyncSession, master_id: int) -> dict[str, Any]:
        """Calculate comprehensive master statistics"""
        
        # Get master info
        master_result = await session.execute(
            select(User).where(User.id == master_id)
        )
        master = master_result.scalar_one_or_none()
        
        # Total orders by status
        status_counts = {}
        status_result = await session.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.master_id == master_id)
            .group_by(Order.status)
        )
        for status, count in status_result.all():
            status_counts[status.value] = count
        
        # Total revenue and commission
        revenue_result = await session.execute(
            select(
                func.count(Order.id),
                func.sum(Order.total_price),
                func.sum(Order.master_commission),
                func.sum(Order.advance_paid),
                func.sum(Order.debt),
            )
            .where(
                Order.master_id == master_id,
                Order.status != OrderStatus.CANCELLED
            )
        )
        row = revenue_result.first()
        
        total_orders = row[0] or 0
        total_revenue = row[1] or Decimal("0")
        total_commission = row[2] or Decimal("0")
        total_advance = row[3] or Decimal("0")
        total_debt = row[4] or Decimal("0")
        
        # This month stats
        from datetime import datetime
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_result = await session.execute(
            select(
                func.count(Order.id),
                func.sum(Order.total_price),
                func.sum(Order.master_commission),
            )
            .where(
                Order.master_id == master_id,
                Order.created_at >= month_start,
                Order.status != OrderStatus.CANCELLED
            )
        )
        month_row = month_result.first()
        
        month_orders = month_row[0] or 0
        month_revenue = month_row[1] or Decimal("0")
        month_commission = month_row[2] or Decimal("0")
        
        # Recent orders
        recent_orders_result = await session.execute(
            select(Order)
            .where(Order.master_id == master_id)
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        recent_orders = list(recent_orders_result.scalars().all())
        
        return {
            "master_name": master.full_name if master else "Master",
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_commission": total_commission,
            "total_advance": total_advance,
            "total_debt": total_debt,
            "month_orders": month_orders,
            "month_revenue": month_revenue,
            "month_commission": month_commission,
            "status_counts": status_counts,
            "recent_orders": recent_orders,
        }
