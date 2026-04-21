from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Order, OrderStatus, Region, User, UserRole, user_hududlar


class UstaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_available_ustas(
        self,
        region_id: Optional[int] = None,
        viloyat_id: Optional[int] = None,
    ) -> List[Tuple[User, int]]:
        """Returns (usta, active_order_count) sorted by lowest workload first.

        Matching priority:
        1. By viloyat_id (User.viloyat_id matches order viloyat)
        2. By region_id or user_hududlar (legacy)
        3. By viloyat name similarity fallback
        4. Ustas with no region/hudud assigned
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

        def _dedup(rows):
            seen = set()
            results = []
            for row in rows.all():
                if row[0].id not in seen:
                    seen.add(row[0].id)
                    results.append((row[0], int(row[1])))
            return results

        # Step 1: match by viloyat_id (new system)
        if viloyat_id:
            viloyat_query = base_query.where(User.viloyat_id == viloyat_id)
            rows = await self.session.execute(viloyat_query)
            results = _dedup(rows)
            if results:
                return results

        # Step 2: match by region_id or user_hududlar
        if region_id:
            hudud_subq = (
                select(user_hududlar.c.user_id)
                .where(user_hududlar.c.hudud_id == region_id)
            )
            region_query = base_query.where(
                or_(
                    User.region_id == region_id,
                    User.id.in_(hudud_subq),
                )
            )
            rows = await self.session.execute(region_query)
            results = _dedup(rows)
            if results:
                return results

            # Step 2b: viloyat-level fallback — find sibling regions by name prefix
            region_row = await self.session.execute(
                select(Region).where(Region.id == region_id)
            )
            region_obj = region_row.scalar_one_or_none()
            if region_obj:
                name_root = region_obj.name.split()[0] if region_obj.name else None
                if name_root:
                    sibling_ids_q = await self.session.execute(
                        select(Region.id).where(Region.name.ilike(f"{name_root}%"))
                    )
                    sibling_ids = [r[0] for r in sibling_ids_q.all() if r[0] != region_id]
                    if sibling_ids:
                        sib_hudud_subq = (
                            select(user_hududlar.c.user_id)
                            .where(user_hududlar.c.hudud_id.in_(sibling_ids))
                        )
                        sib_query = base_query.where(
                            or_(
                                User.region_id.in_(sibling_ids),
                                User.id.in_(sib_hudud_subq),
                            )
                        )
                        rows = await self.session.execute(sib_query)
                        results = _dedup(rows)
                        if results:
                            return results

        # Step 3: match by hududlar region viloyat name (user selected Buxoro in hududlar)
        if viloyat_id:
            from app.db.models import Viloyat
            viloyat_row = await self.session.execute(
                select(Viloyat).where(Viloyat.id == viloyat_id)
            )
            viloyat_obj = viloyat_row.scalar_one_or_none()
            if viloyat_obj:
                hudud_viloyat_subq = (
                    select(user_hududlar.c.user_id)
                    .join(Region, Region.id == user_hududlar.c.hudud_id)
                    .where(Region.name.ilike(f"%{viloyat_obj.name.split()[0]}%"))
                )
                hud_viloyat_query = base_query.where(User.id.in_(hudud_viloyat_subq))
                rows = await self.session.execute(hud_viloyat_query)
                results = _dedup(rows)
                if results:
                    return results

        # Step 4: final fallback — return ALL active ustas so admin can always assign
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

    async def reassign_usta(
        self,
        order_id: int,
        new_usta_id: int,
        assigned_by_id: int,
    ) -> Optional[Order]:
        """Assign or replace usta on an order (master/admin can change usta)."""
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return None
        if order.status in [OrderStatus.DONE, OrderStatus.CANCELLED]:
            return None
        usta_result = await self.session.execute(
            select(User)
            .where(User.id == new_usta_id)
            .where(User.role == UserRole.USTA)
            .where(User.is_active == True)
        )
        usta = usta_result.scalar_one_or_none()
        if not usta:
            return None
        old_usta_id = order.usta_id
        order.usta_id = new_usta_id
        await self.session.flush()
        log = AuditLog(
            user_id=assigned_by_id,
            action="usta_reassigned",
            entity_type="order",
            entity_id=order_id,
            old_value=str(old_usta_id) if old_usta_id else None,
            new_value=str(new_usta_id),
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
