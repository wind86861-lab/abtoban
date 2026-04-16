from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Expense,
    MaterialRequest,
    Order,
    OrderStatus,
    User,
    UserRole,
)


@dataclass
class OrderSummary:
    total: int = 0
    new: int = 0
    confirmed: int = 0
    in_work: int = 0
    done: int = 0
    cancelled: int = 0
    revenue: Decimal = field(default_factory=lambda: Decimal("0"))
    collected: Decimal = field(default_factory=lambda: Decimal("0"))
    debt: Decimal = field(default_factory=lambda: Decimal("0"))
    month_total: int = 0
    month_revenue: Decimal = field(default_factory=lambda: Decimal("0"))


@dataclass
class MasterStat:
    master: User
    order_count: int
    total_revenue: Decimal
    total_commission: Decimal


@dataclass
class UstaStat:
    usta: User
    order_count: int
    total_wage: Decimal


@dataclass
class ProductProfit:
    product_name: str
    total_area: Decimal
    cost_per_m2: Decimal
    price_per_m2: Decimal
    total_cost: Decimal
    total_revenue: Decimal
    total_profit: Decimal
    order_count: int


@dataclass
class FinancialReport:
    total_revenue: Decimal = field(default_factory=lambda: Decimal("0"))
    total_advance: Decimal = field(default_factory=lambda: Decimal("0"))
    total_debt: Decimal = field(default_factory=lambda: Decimal("0"))
    asphalt_cost: Decimal = field(default_factory=lambda: Decimal("0"))
    asphalt_revenue: Decimal = field(default_factory=lambda: Decimal("0"))
    asphalt_profit: Decimal = field(default_factory=lambda: Decimal("0"))
    material_cost: Decimal = field(default_factory=lambda: Decimal("0"))
    other_expenses: Decimal = field(default_factory=lambda: Decimal("0"))
    total_costs: Decimal = field(default_factory=lambda: Decimal("0"))
    net_profit: Decimal = field(default_factory=lambda: Decimal("0"))
    profit_margin: float = 0.0
    total_orders: int = 0
    product_profits: List["ProductProfit"] = field(default_factory=list)


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self) -> OrderSummary:
        s = OrderSummary()
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        rows = await self.session.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )
        for status, count in rows.all():
            s.total += count
            if status == OrderStatus.NEW:
                s.new = count
            elif status == OrderStatus.CONFIRMED:
                s.confirmed = count
            elif status == OrderStatus.IN_WORK:
                s.in_work = count
            elif status == OrderStatus.DONE:
                s.done = count
            elif status == OrderStatus.CANCELLED:
                s.cancelled = count

        rev = await self.session.execute(
            select(func.sum(Order.total_price))
            .where(Order.status == OrderStatus.DONE)
        )
        s.revenue = rev.scalar_one() or Decimal("0")

        coll = await self.session.execute(
            select(func.sum(Order.advance_paid))
        )
        s.collected = coll.scalar_one() or Decimal("0")

        debt = await self.session.execute(
            select(func.sum(Order.debt))
        )
        s.debt = debt.scalar_one() or Decimal("0")

        month_cnt = await self.session.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= month_start)
        )
        s.month_total = month_cnt.scalar_one() or 0

        month_rev = await self.session.execute(
            select(func.sum(Order.total_price))
            .where(Order.status == OrderStatus.DONE)
            .where(Order.completed_at >= month_start)
        )
        s.month_revenue = month_rev.scalar_one() or Decimal("0")

        return s

    async def get_master_stats(
        self, start: datetime, end: datetime
    ) -> List[MasterStat]:
        rows = await self.session.execute(
            select(
                User,
                func.count(Order.id).label("cnt"),
                func.coalesce(func.sum(Order.total_price), 0).label("rev"),
                func.coalesce(func.sum(Order.master_commission), 0).label("comm"),
            )
            .join(Order, Order.master_id == User.id)
            .where(User.role == UserRole.MASTER)
            .where(Order.created_at.between(start, end))
            .group_by(User.id)
            .order_by(func.count(Order.id).desc())
        )
        return [
            MasterStat(
                master=row[0],
                order_count=row[1],
                total_revenue=Decimal(str(row[2])),
                total_commission=Decimal(str(row[3])),
            )
            for row in rows.all()
        ]

    async def get_usta_stats(
        self, start: datetime, end: datetime
    ) -> List[UstaStat]:
        rows = await self.session.execute(
            select(
                User,
                func.count(Order.id).label("cnt"),
                func.coalesce(func.sum(Order.usta_wage), 0).label("wage"),
            )
            .join(Order, Order.usta_id == User.id)
            .where(User.role == UserRole.USTA)
            .where(Order.created_at.between(start, end))
            .group_by(User.id)
            .order_by(func.count(Order.id).desc())
        )
        return [
            UstaStat(
                usta=row[0],
                order_count=row[1],
                total_wage=Decimal(str(row[2])),
            )
            for row in rows.all()
        ]

    async def get_orders_for_export(
        self, start: datetime, end: datetime
    ) -> List[Order]:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.client),
                selectinload(Order.master),
                selectinload(Order.usta),
                selectinload(Order.asphalt_type),
            )
            .where(Order.created_at.between(start, end))
            .order_by(Order.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_expenses_for_export(
        self, start: datetime, end: datetime
    ) -> List[Expense]:
        result = await self.session.execute(
            select(Expense)
            .options(selectinload(Expense.order))
            .where(Expense.created_at.between(start, end))
            .order_by(Expense.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_material_requests_for_export(
        self, start: datetime, end: datetime
    ) -> List[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order),
                selectinload(MaterialRequest.usta),
            )
            .where(MaterialRequest.created_at.between(start, end))
            .order_by(MaterialRequest.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_financial_report(self) -> FinancialReport:
        """Get comprehensive financial report with profit calculations"""
        report = FinancialReport()
        
        # Total orders and revenue
        order_stats = await self.session.execute(
            select(
                func.count(Order.id),
                func.sum(Order.total_price),
                func.sum(Order.advance_paid),
                func.sum(Order.debt),
            ).where(Order.status != OrderStatus.CANCELLED)
        )
        row = order_stats.first()
        report.total_orders = row[0] or 0
        report.total_revenue = row[1] or Decimal("0")
        report.total_advance = row[2] or Decimal("0")
        report.total_debt = row[3] or Decimal("0")
        
        # Material costs
        material_stats = await self.session.execute(
            select(
                func.sum(
                    func.coalesce(MaterialRequest.material_price, 0) + 
                    func.coalesce(MaterialRequest.delivery_price, 0) + 
                    func.coalesce(MaterialRequest.extra_cost, 0)
                )
            )
        )
        report.material_cost = material_stats.scalar() or Decimal("0")
        
        # Other expenses
        expense_stats = await self.session.execute(
            select(func.sum(Expense.amount))
        )
        report.other_expenses = expense_stats.scalar() or Decimal("0")
        
        # Asphalt cost vs revenue calculation with product-level breakdown
        from app.db.models import AsphaltType
        orders_with_asphalt = await self.session.execute(
            select(Order)
            .options(selectinload(Order.asphalt_type))
            .where(
                Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.DONE]),
                Order.asphalt_type_id.isnot(None),
                Order.area_m2.isnot(None)
            )
        )
        
        # Track product-level profits
        product_stats = {}  # {asphalt_type_id: {name, total_area, cost, revenue, count}}
        
        for order in orders_with_asphalt.scalars():
            if order.asphalt_type:
                area = order.area_m2 or Decimal("0")
                cost_per_m2 = order.asphalt_type.cost_price_per_m2 or Decimal("0")
                price_per_m2 = order.asphalt_type.price_per_m2 or Decimal("0")
                
                report.asphalt_cost += area * cost_per_m2
                report.asphalt_revenue += area * price_per_m2
                
                # Track by product
                type_id = order.asphalt_type.id
                if type_id not in product_stats:
                    product_stats[type_id] = {
                        'name': order.asphalt_type.name,
                        'cost_per_m2': cost_per_m2,
                        'price_per_m2': price_per_m2,
                        'total_area': Decimal("0"),
                        'total_cost': Decimal("0"),
                        'total_revenue': Decimal("0"),
                        'count': 0
                    }
                
                product_stats[type_id]['total_area'] += area
                product_stats[type_id]['total_cost'] += area * cost_per_m2
                product_stats[type_id]['total_revenue'] += area * price_per_m2
                product_stats[type_id]['count'] += 1
        
        # Create ProductProfit objects
        for stats in product_stats.values():
            report.product_profits.append(ProductProfit(
                product_name=stats['name'],
                total_area=stats['total_area'],
                cost_per_m2=stats['cost_per_m2'],
                price_per_m2=stats['price_per_m2'],
                total_cost=stats['total_cost'],
                total_revenue=stats['total_revenue'],
                total_profit=stats['total_revenue'] - stats['total_cost'],
                order_count=stats['count']
            ))
        
        # Sort by profit descending
        report.product_profits.sort(key=lambda x: x.total_profit, reverse=True)
        
        report.asphalt_profit = report.asphalt_revenue - report.asphalt_cost
        report.total_costs = report.asphalt_cost + report.material_cost + report.other_expenses
        report.net_profit = report.total_revenue - report.total_costs
        
        if report.total_revenue > 0:
            report.profit_margin = float(report.net_profit / report.total_revenue * 100)
        
        return report

    @staticmethod
    def period_bounds(period: str) -> tuple[datetime, datetime]:
        now = datetime.utcnow()
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, now
        else:
            start = datetime(2020, 1, 1)
            return start, now
