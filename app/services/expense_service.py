from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Expense, ExpenseType


EXPENSE_LABELS: dict[ExpenseType, str] = {
    ExpenseType.MATERIAL: "🏗 Material",
    ExpenseType.DELIVERY: "🚚 Yetkazib berish",
    ExpenseType.WAGE: "👷 Ish haqi",
    ExpenseType.BARDYOR: "🔧 Bardyor",
    ExpenseType.EXTRA: "➕ Qo'shimcha",
}


class ExpenseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        order_id: int,
        expense_type: ExpenseType,
        amount: Decimal,
        created_by: int,
        description: Optional[str] = None,
    ) -> Expense:
        expense = Expense(
            order_id=order_id,
            expense_type=expense_type,
            amount=amount,
            description=description,
            created_by=created_by,
        )
        self.session.add(expense)
        await self.session.flush()
        return expense

    async def get_by_order(self, order_id: int) -> List[Expense]:
        result = await self.session.execute(
            select(Expense)
            .where(Expense.order_id == order_id)
            .order_by(Expense.created_at.asc())
        )
        return list(result.scalars().all())

    async def total_by_order(self, order_id: int) -> Decimal:
        result = await self.session.execute(
            select(func.sum(Expense.amount)).where(Expense.order_id == order_id)
        )
        return result.scalar_one() or Decimal("0")
