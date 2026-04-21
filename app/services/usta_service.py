from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Order, OrderStatus, User, UserRole


class UstaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_available_ustas(
        self,
        region_id: Optional[int] = None,
    ) -> List[Tuple[User, int]]:
        """Returns (usta, active_order_count) sorted by lowest workload first.

        If region_id is given, only returns ustas assigned to that region.
        If no ustas found in the region, falls back to ustas with no region set.
        No order limit — ustas can handle multiple orders simultaneously.
        """
        active_sq = (
            select(Order.usta_id, func.count(Order.id).label("cnt"))
            .where(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_WORK]))
            .where(Order.usta_id.isnot(None))
            .group_by(Order.usta_id)
            .subquery()
        )

        base_query = (
            select(User, func.coalesce(active_sq.c.cnt, 0).label("active_cnt"))
            .outerjoin(active_sq, User.id == active_sq.c.usta_id)
            .where(User.role == UserRole.USTA)
            .where(User.is_active == True)
            .order_by(
                func.coalesce(active_sq.c.cnt, 0).asc(),
                User.id.asc(),
            )
        )

        if region_id:
            region_query = base_query.where(User.region_id == region_id)
            rows = await self.session.execute(region_query)
            results = [(row[0], int(row[1])) for row in rows.all()]
            if results:
                return results
            # fallback: ustas with no region assigned
            fallback_query = base_query.where(User.region_id == None)
            rows = await self.session.execute(fallback_query)
            return [(row[0], int(row[1])) for row in rows.all()]

        rows = await self.session.execute(base_query)
        return [(row[0], int(row[1])) for row in rows.all()]

    async def get_pending_usta_orders(self, master_id: int) -> List[Order]:
        """CONFIRMED or IN_WORK orders by this master that still need usta."""
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.asphalt_type))
            .where(Order.master_id == master_id)
            .where(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_WORK]))
            .where(Order.usta_id == None)
            .order_by(Order.usta_assignment_deadline.asc(), Order.id.asc())
        )
        return list(result.scalars().all())

    async def get_all_pending_usta_orders(self) -> List[Order]:
        """All CONFIRMED orders without usta (for admin/auto-assign view)."""
        now = datetime.now(timezone.utc)
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
        if order.status not in [OrderStatus.CONFIRMED, OrderStatus.IN_WORK]:
            return None
        if order.usta_id is not None:
            return None
        usta_result = await self.session.execute(
            select(User)
            .where(User.id == usta_id)
            .where(User.role == UserRole.USTA)
            .where(User.is_active == True)
        )
        usta = usta_result.scalar_one_or_none()
        if not usta:
            return None
        # Removed MAX_ACTIVE_ORDERS check - Ustas can now accept unlimited orders
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
