from decimal import Decimal

from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.db.models import Expense, ExpenseType, Order, OrderStatus
from app.db.session import async_session_maker


class MasterExpenseView(BaseView):
    name = "Xarajat Kiritish"
    icon = "fa-solid fa-money-bill-wave"

    @expose("/expenses", methods=["GET"])
    async def expenses_page(self, request: Request):
        user_id = request.session.get("user_id") or request.session.get("master_user_id")
        if not user_id:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        msg = request.query_params.get("msg", "")

        async with async_session_maker() as session:
            # Master's active orders
            orders_result = await session.execute(
                select(Order)
                .where(
                    Order.master_id == user_id,
                    Order.status != OrderStatus.CANCELLED,
                )
                .order_by(Order.created_at.desc())
                .limit(100)
            )
            orders = orders_result.scalars().all()

            # Recent expenses for master's orders
            expenses_result = await session.execute(
                select(Expense)
                .join(Order, Expense.order_id == Order.id)
                .where(Order.master_id == user_id)
                .order_by(Expense.created_at.desc())
                .limit(50)
            )
            expenses = expenses_result.scalars().all()

            # Load related orders for display
            order_map = {o.id: o for o in orders}

        expense_types = [(e.value, e.value.capitalize()) for e in ExpenseType]

        return await self.templates.TemplateResponse(
            request,
            "master_expenses.html",
            context={
                "orders": orders,
                "expenses": expenses,
                "order_map": order_map,
                "expense_types": expense_types,
                "msg": msg,
            },
        )

    @expose("/expenses/save", methods=["POST"])
    async def expenses_save(self, request: Request):
        user_id = request.session.get("user_id") or request.session.get("master_user_id")
        if not user_id:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        form = await request.form()
        order_id = int(form.get("order_id", 0))
        expense_type = form.get("expense_type", "")
        amount_str = form.get("amount", "")
        description = form.get("description", "")

        if not order_id or not expense_type or not amount_str:
            return RedirectResponse(
                url="/master-panel/admin/expenses?msg=error_fields", status_code=302
            )

        try:
            amount = Decimal(amount_str.replace(" ", "").replace(",", "."))
        except Exception:
            return RedirectResponse(
                url="/master-panel/admin/expenses?msg=error_amount", status_code=302
            )

        async with async_session_maker() as session:
            # Verify order belongs to this master
            result = await session.execute(
                select(Order).where(
                    Order.id == order_id,
                    Order.master_id == user_id,
                )
            )
            order = result.scalar_one_or_none()
            if not order:
                return RedirectResponse(
                    url="/master-panel/admin/expenses?msg=error_order", status_code=302
                )

            expense = Expense(
                order_id=order_id,
                expense_type=ExpenseType(expense_type),
                amount=amount,
                description=description or None,
                created_by=user_id,
            )
            session.add(expense)
            await session.commit()

        return RedirectResponse(
            url="/master-panel/admin/expenses?msg=ok", status_code=303
        )
