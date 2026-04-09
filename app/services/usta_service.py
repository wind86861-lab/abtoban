from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Order, OrderStatus, User, UserRole

MAX_ACTIVE_ORDERS = 2


class UstaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_available_ustas(self) -> List[Tuple[User, int]]:
        """Returns (usta, active_order_count) sorted by lowest workload first."""
        active_sq = (
            select(Order.usta_id, func.count(Order.id).label("cnt"))
            .where(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_WORK]))
            .where(Order.usta_id.isnot(None))
            .group_by(Order.usta_id)
            .subquery()
        )
        rows = await self.session.execute(
            select(User, func.coalesce(active_sq.c.cnt, 0).label("active_cnt"))
            .outerjoin(active_sq, User.id == active_sq.c.usta_id)
            .where(User.role == UserRole.USTA)
            .where(User.is_active == True)
            .where(
                (active_sq.c.cnt == None) | (active_sq.c.cnt < MAX_ACTIVE_ORDERS)
            )
            .order_by(
                func.coalesce(active_sq.c.cnt, 0).asc(),
                User.id.asc(),
            )
        )
        return [(row[0], int(row[1])) for row in rows.all()]

    async def get_pending_usta_orders(self, master_id: int) -> List[Order]:
        """CONFIRMED orders by this master that still need usta and are within deadline."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.asphalt_type))
            .where(Order.master_id == master_id)
            .where(Order.status == OrderStatus.CONFIRMED)
            .where(Order.usta_id == None)
            .where(Order.usta_assignment_deadline > now)
            .order_by(Order.usta_assignment_deadline.asc())
        )
        return list(result.scalars().all())

    async def get_all_pending_usta_orders(self) -> List[Order]:
        """All CONFIRMED orders without usta (for admin/auto-assign view)."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.master), selectinload(Order.asphalt_type))
            .where(Order.status == OrderStatus.CONFIRMED)
            .where(Order.usta_id == None)
            .where(Order.usta_assignment_deadline > now)
            .order_by(Order.usta_assignment_deadline.asc())
        )
        return list(result.scalars().all())

    async def assign_usta_to_order(
        self,
        order_id: int,
        usta_id: int,
        assigned_by_id: int,
    ) -> Optional[Order]:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None
        order.usta_id = usta_id
        await self.session.flush()
        log = AuditLog(
            user_id=assigned_by_id,
            action="usta_assigned",
            entity_type="order",
            entity_id=order_id,
            new_value=str(usta_id),
        )
        self.session.add(log)
        await self.session.flush()
        return order

    async def release_usta(self, order_id: int, usta_id: int) -> Optional[Order]:
        """Usta declines — remove assignment from order."""
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .where(Order.usta_id == usta_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None
        order.usta_id = None
        await self.session.flush()
        log = AuditLog(
            user_id=usta_id,
            action="usta_declined",
            entity_type="order",
            entity_id=order_id,
        )
        self.session.add(log)
        await self.session.flush()
        return order

    async def get_active_order_count(self, usta_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Order.id))
            .where(Order.usta_id == usta_id)
            .where(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_WORK]))
        )
        return result.scalar_one()
