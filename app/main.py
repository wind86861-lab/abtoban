import asyncio
import logging

from aiogram import Dispatcher

from app.bot.handlers import register_all_routers
from app.bot.loader import bot, dp
from app.bot.middlewares.audit import AuditMiddleware
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.db import DbSessionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(dispatcher: Dispatcher) -> None:
    logger.info("Bot starting up...")
    register_all_routers(dispatcher)
    logger.info("All routers registered.")


async def on_shutdown(dispatcher: Dispatcher) -> None:
    logger.info("Bot shutting down...")
    await bot.session.close()


async def main() -> None:
    # Middleware order matters: db → auth → audit
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(AuditMiddleware())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    asyncio.run(main())
