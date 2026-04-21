import asyncio
import logging

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.auto_assign_usta", bind=True, max_retries=3)
def auto_assign_usta(self, order_id: int) -> dict:
    """
    Auto-assigns an usta by lowest workload (round-robin) if the master did
    not manually assign one within the 30-minute deadline window.
    Retries up to 3 times on unexpected errors.
    """
    try:
        return asyncio.run(_auto_assign_async(order_id))
    except Exception as exc:
        logger.error("auto_assign_usta error for order %s: %s", order_id, exc)
        raise self.retry(exc=exc, countdown=120)


async def _auto_assign_async(order_id: int) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode

    from app.config import settings
    from app.db.models import OrderStatus, UserRole
    from app.services.order_service import OrderService
    from app.services.usta_service import UstaService
    from app.services.user_service import UserService
    from app.bot.keyboards.usta import get_usta_notification_keyboard

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        async with AsyncSessionLocal() as session:
            order_svc = OrderService(session)
            order = await order_svc.get_by_id_full(order_id)

            if not order:
                logger.warning("auto_assign: order %s not found", order_id)
                return {"status": "order_not_found"}

            if order.status != OrderStatus.CONFIRMED:
                return {"status": "skipped", "order_status": order.status.value}

            if order.usta_id is not None:
                return {"status": "already_assigned", "usta_id": order.usta_id}

            usta_svc = UstaService(session)
            user_svc = UserService(session)
            available = await usta_svc.get_available_ustas(region_id=order.region_id, viloyat_id=order.viloyat_id)

            if not available:
                # No ustas — alert admins and master
                admins = await user_svc.get_all(role=UserRole.ADMIN)
                super_admins = await user_svc.get_all(role=UserRole.SUPER_ADMIN)
                alert_text = (
                    f"⚠️ <b>Usta topilmadi!</b>\n\n"
                    f"Zakaz #{order.order_number}\n"
                    f"Barcha ustalar band yoki faol emas.\n"
                    f"Qo'lda tayinlang."
                )
                for admin in admins + super_admins:
                    try:
                        await bot.send_message(admin.telegram_id, alert_text)
                    except Exception:
                        pass
                if order.master:
                    try:
                        await bot.send_message(order.master.telegram_id, alert_text)
                    except Exception:
                        pass
                await session.commit()
                return {"status": "no_ustas_available"}

            # Pick usta with lowest active workload
            selected_usta, active_count = available[0]

            await usta_svc.assign_usta_to_order(
                order_id=order_id,
                usta_id=selected_usta.id,
                assigned_by_id=selected_usta.id,
            )
            await session.commit()

            logger.info(
                "auto_assign: order %s → usta %s (active=%s)",
                order_id, selected_usta.id, active_count,
            )

        # Re-open session for read-only notification data
        async with AsyncSessionLocal() as session:
            order_svc = OrderService(session)
            order = await order_svc.get_by_id_full(order_id)

            asphalt = order.asphalt_type.name if order.asphalt_type else "—"
            wage = float(order.usta_wage) if order.usta_wage else 0
            work_date = (
                order.work_date.strftime("%d.%m.%Y") if order.work_date else "—"
            )

            notify_usta = (
                f"👷 <b>Sizga zakaz avtomatik tayinlandi!</b>\n\n"
                f"🔢 #{order.order_number}\n"
                f"📍 {order.address or '—'}\n"
                f"📐 {order.area_m2} m²\n"
                f"🏗 {asphalt}\n"
                f"📅 Ish sanasi: {work_date}\n"
                f"💰 Usta haqi: {wage:,.0f} so'm\n\n"
                f"Qabul qilasizmi?"
            )
            try:
                await bot.send_message(
                    selected_usta.telegram_id,
                    notify_usta,
                    reply_markup=get_usta_notification_keyboard(order_id),
                )
            except Exception as e:
                logger.warning("Could not notify usta %s: %s", selected_usta.telegram_id, e)

            if order.master:
                try:
                    await bot.send_message(
                        order.master.telegram_id,
                        f"⏰ <b>Usta avtomatik tayinlandi</b>\n\n"
                        f"Zakaz #{order.order_number}\n"
                        f"👷 Usta: {selected_usta.full_name or selected_usta.telegram_id}\n"
                        f"Usta qabul qilishi kutilmoqda.",
                    )
                except Exception:
                    pass

        return {"status": "auto_assigned", "usta_id": selected_usta.id}

    finally:
        await engine.dispose()
        await bot.session.close()
