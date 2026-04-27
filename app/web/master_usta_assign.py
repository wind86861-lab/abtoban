from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.db.models import Order, OrderStatus, User, UserRole
from app.db.session import async_session_maker


class MasterUstaAssignView(BaseView):
    name = "Usta Tayinlash"
    icon = "fa-solid fa-hard-hat"

    @expose("/usta-assign", methods=["GET"])
    async def usta_assign_page(self, request: Request):
        user_id = request.session.get("user_id") or request.session.get("master_user_id")
        if not user_id:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        async with async_session_maker() as session:
            # Orders belonging to this master (not cancelled)
            orders_result = await session.execute(
                select(Order)
                .where(
                    Order.master_id == user_id,
                    Order.status != OrderStatus.CANCELLED,
                )
                .order_by(Order.created_at.desc())
                .limit(50)
            )
            orders = orders_result.scalars().all()

            # All active ustas
            ustas_result = await session.execute(
                select(User).where(
                    User.role == UserRole.USTA,
                    User.is_active.is_(True),
                )
            )
            ustas = ustas_result.scalars().all()

        return await self.templates.TemplateResponse(
            request,
            "master_usta.html",
            context={"orders": orders, "ustas": ustas},
        )

    @expose("/usta-assign/save", methods=["POST"])
    async def usta_assign_save(self, request: Request):
        user_id = request.session.get("user_id") or request.session.get("master_user_id")
        if not user_id:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        form = await request.form()
        order_id = int(form.get("order_id", 0))
        usta_id = form.get("usta_id", "")
        usta_wage = form.get("usta_wage", "")

        if not order_id:
            return RedirectResponse(url="/master-panel/admin/usta-assign", status_code=302)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Order).where(
                    Order.id == order_id,
                    Order.master_id == user_id,
                )
            )
            order = result.scalar_one_or_none()
            if order:
                order.usta_id = int(usta_id) if usta_id else None
                if usta_wage:
                    from decimal import Decimal
                    try:
                        order.usta_wage = Decimal(usta_wage)
                    except Exception:
                        pass
                await session.commit()

        return RedirectResponse(url="/master-panel/admin/usta-assign", status_code=303)
