from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AsphaltType


class AsphaltService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_active(self) -> List[AsphaltType]:
        result = await self.session.execute(
            select(AsphaltType)
            .where(AsphaltType.is_active == True)
            .order_by(AsphaltType.id)
        )
        return list(result.scalars().all())

    async def get_all(self) -> List[AsphaltType]:
        result = await self.session.execute(
            select(AsphaltType).order_by(AsphaltType.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, asphalt_id: int) -> Optional[AsphaltType]:
        result = await self.session.execute(
            select(AsphaltType).where(AsphaltType.id == asphalt_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, price_per_m2: Decimal, cost_price_per_m2: Optional[Decimal] = None) -> AsphaltType:
        at = AsphaltType(
            name=name, 
            cost_price_per_m2=cost_price_per_m2 or Decimal("0"),
            price_per_m2=price_per_m2, 
            is_active=True
        )
        self.session.add(at)
        await self.session.flush()
        return at

    async def update_price(
        self, asphalt_id: int, price_per_m2: Decimal
    ) -> Optional[AsphaltType]:
        at = await self.get_by_id(asphalt_id)
        if not at:
            return None
        at.price_per_m2 = price_per_m2
        await self.session.flush()
        return at

    async def toggle_active(self, asphalt_id: int) -> Optional[AsphaltType]:
        at = await self.get_by_id(asphalt_id)
        if not at:
            return None
        at.is_active = not at.is_active
        await self.session.flush()
        return at
