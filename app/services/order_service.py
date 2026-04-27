from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Order, OrderLineItem, OrderStatus, User, UserRole


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_order_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.order_number.like(f"AVT-{today}-%")
            )
        )
        count = result.scalar_one() + 1
        return f"AVT-{today}-{count:04d}"

    async def create(
        self,
        client: User,
        address: str,
        area_m2: Decimal,
        asphalt_type_id: Optional[int] = None,
        notes: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        region_id: Optional[int] = None,
        viloyat_id: Optional[int] = None,
        tuman_id: Optional[int] = None,
    ) -> Order:
        order_number = await self.generate_order_number()
        order = Order(
            order_number=order_number,
            client_id=client.id,
            client_name=client.full_name or "Nomsiz",
            client_phone=client.phone or "",
            address=address,
            latitude=latitude,
            longitude=longitude,
            area_m2=area_m2,
            region_id=region_id,
            viloyat_id=viloyat_id,
            tuman_id=tuman_id,
            asphalt_type_id=asphalt_type_id,
            status=OrderStatus.NEW,
            notes=notes,
            advance_paid=Decimal("0"),
            discount=Decimal("0"),
            debt=Decimal("0"),
        )
        self.session.add(order)
        await self.session.flush()

        log = AuditLog(
            user_id=client.id,
            action="order_created",
            entity_type="order",
            entity_id=order.id,
            new_value=order_number,
        )
        self.session.add(log)
        await self.session.flush()
        return order

    async def create_by_master(
        self,
        master_id: int,
        client_name: str,
        client_phone: str,
        address: str,
        area_m2: Decimal = Decimal("0"),
        region_id: Optional[int] = None,
        asphalt_type_id: Optional[int] = None,
        viloyat_id: Optional[int] = None,
        tuman_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Order:
        order_number = await self.generate_order_number()
        # Try to resolve existing klient user by phone; otherwise use master as fallback
        client_id = master_id
        if client_phone:
            normalized = client_phone.replace("+", "").replace(" ", "").replace("-", "")
            res = await self.session.execute(
                select(User).where(User.phone == normalized, User.role == UserRole.KLIENT)
            )
            existing = res.scalar_one_or_none()
            if existing:
                client_id = existing.id
        order = Order(
            order_number=order_number,
            client_id=client_id,
            client_name=client_name,
            client_phone=client_phone,
            address=address,
            latitude=latitude,
            longitude=longitude,
            area_m2=area_m2,
            region_id=region_id,
            viloyat_id=viloyat_id,
            tuman_id=tuman_id,
            asphalt_type_id=asphalt_type_id,
            status=OrderStatus.NEW,
            advance_paid=Decimal("0"),
            discount=Decimal("0"),
            debt=Decimal("0"),
        )
        self.session.add(order)
        await self.session.flush()

        log = AuditLog(
            user_id=master_id,
            action="order_created_by_master",
            entity_type="order",
            entity_id=order.id,
            new_value=order_number,
        )
        self.session.add(log)
        await self.session.flush()
        return order

    async def create_by_admin(
        self,
        admin_id: int,
        client_id: int,
        client_name: str,
        client_phone: str,
        address: str,
        area_m2: Decimal,
        asphalt_type_id: Optional[int] = None,
        notes: Optional[str] = None,
        region_id: Optional[int] = None,
        viloyat_id: Optional[int] = None,
        tuman_id: Optional[int] = None,
    ) -> Order:
        order_number = await self.generate_order_number()
        order = Order(
            order_number=order_number,
            client_id=client_id,
            client_name=client_name,
            client_phone=client_phone,
            address=address,
            area_m2=area_m2,
            region_id=region_id,
            viloyat_id=viloyat_id,
            tuman_id=tuman_id,
            asphalt_type_id=asphalt_type_id,
            status=OrderStatus.NEW,
            notes=notes,
            advance_paid=Decimal("0"),
            discount=Decimal("0"),
            debt=Decimal("0"),
        )
        self.session.add(order)
        await self.session.flush()

        log = AuditLog(
            user_id=admin_id,
            action="order_created_by_admin",
            entity_type="order",
            entity_id=order.id,
            new_value=order_number,
        )
        self.session.add(log)
        await self.session.flush()
        return order

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_full(self, order_id: int) -> Optional[Order]:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.client),
                selectinload(Order.master),
                selectinload(Order.usta),
                selectinload(Order.asphalt_type),
                selectinload(Order.region),
                selectinload(Order.viloyat),
                selectinload(Order.tuman_rel),
                selectinload(Order.line_items).selectinload(OrderLineItem.asphalt_type),
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client(
        self, client_id: int, limit: int = 20, offset: int = 0
    ) -> List[Order]:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.asphalt_type),
                selectinload(Order.master),
                selectinload(Order.usta),
            )
            .where(Order.client_id == client_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_client(self, client_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Order.id)).where(Order.client_id == client_id)
        )
        return result.scalar_one()

    async def get_by_master(
        self, master_id: int, limit: int = 20, offset: int = 0
    ) -> List[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.client), selectinload(Order.asphalt_type))
            .where(Order.master_id == master_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_usta(
        self,
        usta_id: int,
        status: Optional[OrderStatus] = None,
        limit: int = 50,
    ) -> List[Order]:
        query = (
            select(Order)
            .options(selectinload(Order.asphalt_type))
            .where(Order.usta_id == usta_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        if status:
            query = query.where(Order.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_new_orders(self, limit: int = 30) -> List[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.client), selectinload(Order.asphalt_type))
            .where(Order.status == OrderStatus.NEW)
            .order_by(Order.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(
        self,
        status: Optional[OrderStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Order]:
        query = (
            select(Order)
            .options(selectinload(Order.client), selectinload(Order.master))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(Order.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(self, status: Optional[OrderStatus] = None) -> int:
        query = select(func.count(Order.id))
        if status:
            query = query.where(Order.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def confirm(
        self,
        order_id: int,
        master_id: int,
        area_m2: Decimal,
        total_price: Decimal,
        advance_paid: Decimal,
        address: str,
        work_date: datetime,
        usta_wage: Decimal,
        master_commission: Decimal,
        notes: Optional[str] = None,
        line_items: Optional[List[dict]] = None,
        calculated_total: Optional[Decimal] = None,
    ) -> Optional[Order]:
        order = await self.get_by_id(order_id)
        if not order or order.status != OrderStatus.NEW:
            return None

        now = datetime.now(timezone.utc)
        order.master_id = master_id
        order.area_m2 = area_m2
        order.total_price = total_price
        order.advance_paid = advance_paid
        order.debt = max(Decimal("0"), total_price - advance_paid)
        order.address = address
        order.work_date = work_date
        order.usta_wage = usta_wage
        order.master_commission = master_commission
        order.notes = notes
        order.calculated_total = calculated_total
        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = now
        order.usta_assignment_deadline = now + timedelta(minutes=30)

        # Create line items and set main asphalt_type_id
        calc_total = Decimal("0")
        if line_items:
            main_asphalt_set = False
            for item in line_items:
                at_id = int(item.get("asphalt_type_id") or 0) or None
                area = Decimal(str(item.get("area_m2", area_m2)))
                price = Decimal(str(item.get("price_per_m2", 0)))
                cost = Decimal(str(item.get("cost_price_per_m2", 0)))
                desc = item.get("description")
                is_main = bool(item.get("is_main", False))
                subtotal = area * price

                li = OrderLineItem(
                    order_id=order_id,
                    asphalt_type_id=at_id,
                    description=desc,
                    area_m2=area,
                    price_per_m2=price,
                    cost_price_per_m2=cost,
                    subtotal=subtotal,
                    is_main=is_main,
                )
                self.session.add(li)
                calc_total += subtotal

                # Set main asphalt type on order for backward compat
                if is_main and at_id and not main_asphalt_set:
                    order.asphalt_type_id = at_id
                    main_asphalt_set = True

            if calculated_total is None:
                order.calculated_total = calc_total

        await self.session.flush()

        log = AuditLog(
            user_id=master_id,
            action="order_confirmed",
            entity_type="order",
            entity_id=order_id,
            old_value=OrderStatus.NEW.value,
            new_value=OrderStatus.CONFIRMED.value,
        )
        self.session.add(log)
        await self.session.flush()
        return order

    async def update_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        changed_by_id: int,
    ) -> Optional[Order]:
        order = await self.get_by_id(order_id)
        if not order:
            return None

        old_status = order.status
        order.status = new_status
        if new_status == OrderStatus.DONE:
            order.completed_at = datetime.now(timezone.utc)

        await self.session.flush()

        log = AuditLog(
            user_id=changed_by_id,
            action="status_change",
            entity_type="order",
            entity_id=order_id,
            old_value=old_status.value,
            new_value=new_status.value,
        )
        self.session.add(log)
        await self.session.flush()
        return order
