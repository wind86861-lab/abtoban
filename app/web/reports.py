from decimal import Decimal
from typing import Any

from sqladmin import BaseView, expose
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AsphaltType, Expense, MaterialRequest, Order, OrderStatus
from app.db.session import async_session_maker


class ReportsView(BaseView):
    name = "Hisobotlar"
    icon = "fa-solid fa-chart-line"

    @expose("/reports", methods=["GET"])
    async def reports_page(self, request):
        """Main reports dashboard showing profit, revenue, costs"""
        async with async_session_maker() as session:
            stats = await self._calculate_stats(session)
        
        return await self.templates.TemplateResponse(
            request,
            "reports.html",
            context={
                "stats": stats,
            }
        )

    async def _calculate_stats(self, session: AsyncSession) -> dict[str, Any]:
        """Calculate comprehensive business statistics"""
        
        # Total orders and revenue
        order_stats = await session.execute(
            select(
                func.count(Order.id).label("total_orders"),
                func.sum(Order.total_price).label("total_revenue"),
                func.sum(Order.advance_paid).label("total_advance"),
                func.sum(Order.debt).label("total_debt"),
            ).where(Order.status != OrderStatus.CANCELLED)
        )
        order_row = order_stats.first()
        
        total_orders = order_row.total_orders or 0
        total_revenue = float(order_row.total_revenue or 0)
        total_advance = float(order_row.total_advance or 0)
        total_debt = float(order_row.total_debt or 0)
        
        # Total expenses
        expense_stats = await session.execute(
            select(func.sum(Expense.amount).label("total_expenses"))
        )
        total_expenses = float(expense_stats.scalar() or 0)
        
        # Material costs
        material_stats = await session.execute(
            select(
                func.sum(
                    (MaterialRequest.material_price or 0) + 
                    (MaterialRequest.delivery_price or 0) + 
                    (MaterialRequest.extra_cost or 0)
                ).label("total_material_cost")
            )
        )
        total_material_cost = float(material_stats.scalar() or 0)
        
        # Calculate asphalt cost vs revenue (profit from asphalt sales)
        # Get all completed orders with asphalt type
        orders_with_asphalt = await session.execute(
            select(Order)
            .options(selectinload(Order.asphalt_type))
            .where(
                Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.DONE]),
                Order.asphalt_type_id.isnot(None),
                Order.area_m2.isnot(None)
            )
        )
        
        asphalt_cost = Decimal("0")
        asphalt_revenue = Decimal("0")
        
        for order in orders_with_asphalt.scalars():
            if order.asphalt_type:
                area = order.area_m2 or Decimal("0")
                cost_per_m2 = order.asphalt_type.cost_price_per_m2 or Decimal("0")
                price_per_m2 = order.asphalt_type.price_per_m2 or Decimal("0")
                
                asphalt_cost += area * cost_per_m2
                asphalt_revenue += area * price_per_m2
        
        asphalt_cost = float(asphalt_cost)
        asphalt_revenue = float(asphalt_revenue)
        asphalt_profit = asphalt_revenue - asphalt_cost
        
        # Total costs = asphalt cost + material costs + other expenses
        total_costs = asphalt_cost + total_material_cost + total_expenses
        
        # Net profit = total revenue - total costs
        net_profit = total_revenue - total_costs
        
        # Profit margin percentage
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Orders by status
        status_counts = {}
        for status in OrderStatus:
            count_result = await session.execute(
                select(func.count(Order.id)).where(Order.status == status)
            )
            status_counts[status.value] = count_result.scalar() or 0
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_advance": total_advance,
            "total_debt": total_debt,
            "asphalt_cost": asphalt_cost,
            "asphalt_revenue": asphalt_revenue,
            "asphalt_profit": asphalt_profit,
            "total_material_cost": total_material_cost,
            "total_expenses": total_expenses,
            "total_costs": total_costs,
            "net_profit": net_profit,
            "profit_margin": profit_margin,
            "status_counts": status_counts,
        }
