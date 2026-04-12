from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TGUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import get_lang
from app.config import settings
from app.db.models import UserRole
from app.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TGUser | None = data.get("event_from_user")

        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        user_service = UserService(session)

        user = await user_service.get_or_create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
        )

        if not user.is_active:
            return None

        if tg_user.id in settings.SUPER_ADMIN_IDS and user.role != UserRole.SUPER_ADMIN:
            user = await user_service.update_role(
                user_id=user.id,
                new_role=UserRole.SUPER_ADMIN,
            )

        data["user"] = user
        data["lang"] = get_lang(user)

        return await handler(event, data)
