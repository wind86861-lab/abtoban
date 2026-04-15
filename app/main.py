import asyncio
import logging

from aiogram import Dispatcher
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.bot.handlers import register_all_routers
from app.bot.loader import bot, dp
from app.bot.middlewares.audit import AuditMiddleware
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.db import DbSessionMiddleware
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(dispatcher: Dispatcher) -> None:
    logger.info("Bot starting up...")
    register_all_routers(dispatcher)
    logger.info("All routers registered.")

    # Set menu button → Web Do'kon (shop web app)
    try:
        base_url = settings.WEB_URL.rsplit("/", 1)[0]  # remove /tma-admin
        shop_url = f"{base_url}/shop"
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Web Do'kon",
                web_app=WebAppInfo(url=shop_url),
            )
        )
        logger.info("Menu button set → %s", shop_url)
    except Exception as e:
        logger.warning("Failed to set menu button: %s", e)


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
