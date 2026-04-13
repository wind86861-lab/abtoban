from aiogram import Dispatcher

from .admin import router as admin_router
from .common import router as common_router
from .klient import router as klient_router
from .master import router as master_router
from .registration import router as registration_router
from .shofer import router as shofer_router
from .shop import router as shop_router
from .usta import router as usta_router
from .zavod import router as zavod_router


def register_all_routers(dp: Dispatcher) -> None:
    dp.include_router(common_router)
    dp.include_router(registration_router)
    dp.include_router(admin_router)
    dp.include_router(shop_router)
    dp.include_router(klient_router)
    dp.include_router(master_router)
    dp.include_router(usta_router)
    dp.include_router(zavod_router)
    dp.include_router(shofer_router)
