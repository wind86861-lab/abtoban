from aiogram import Router

from .export import router as export_router
from .orders import router as orders_router
from .reports import router as reports_router
from .role_management import router as role_mgmt_router
from .settings import router as settings_router

router = Router()
router.include_router(role_mgmt_router)
router.include_router(orders_router)
router.include_router(settings_router)
router.include_router(reports_router)
router.include_router(export_router)
