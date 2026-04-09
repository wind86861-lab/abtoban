import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("user")

        if isinstance(event, Message) and user:
            logger.info(
                "MSG  | tg_id=%-12s | role=%-12s | text=%s",
                user.telegram_id,
                user.role.value,
                event.text or f"[{event.content_type}]",
            )
        elif isinstance(event, CallbackQuery) and user:
            logger.info(
                "CB   | tg_id=%-12s | role=%-12s | data=%s",
                user.telegram_id,
                user.role.value,
                event.data,
            )

        return await handler(event, data)
