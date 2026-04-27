from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PaymentTransfer


class PaymentTransferService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        order_id: int,
        usta_id: int,
        collected: Decimal,
        wage: Decimal,
        sent: Decimal,
    ) -> PaymentTransfer:
        transfer = PaymentTransfer(
            order_id=order_id,
            usta_id=usta_id,
            usta_collected=collected,
            usta_wage_taken=wage,
            usta_sent=sent,
            status="usta_submitted",
        )
        self.session.add(transfer)
        await self.session.flush()
        return transfer

    async def get_by_order(self, order_id: int) -> Optional[PaymentTransfer]:
        result = await self.session.execute(
            select(PaymentTransfer).where(PaymentTransfer.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, transfer_id: int) -> Optional[PaymentTransfer]:
        result = await self.session.execute(
            select(PaymentTransfer).where(PaymentTransfer.id == transfer_id)
        )
        return result.scalar_one_or_none()

    async def confirm_by_zavod(
        self, transfer_id: int, zavod_user_id: int, received: Decimal
    ) -> Optional[PaymentTransfer]:
        transfer = await self.get_by_id(transfer_id)
        if not transfer:
            return None
        transfer.zavod_received = received
        transfer.zavod_user_id = zavod_user_id
        transfer.zavod_confirmed_at = datetime.now(timezone.utc)
        transfer.status = "zavod_confirmed"
        await self.session.flush()
        return transfer

    async def is_confirmed(self, order_id: int) -> bool:
        transfer = await self.get_by_order(order_id)
        return transfer is not None and transfer.status == "zavod_confirmed"
