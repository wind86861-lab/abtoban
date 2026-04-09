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
