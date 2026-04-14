import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.session import engine
from app.web.auth import AdminAuth
from app.web.tma_routes import router as tma_router
from app.web.marketplace_routes import router as marketplace_router
from app.web.views import (
    AsphaltTypeAdmin,
    ExpenseAdmin,
    MaterialRequestAdmin,
    OrderAdmin,
    RegionAdmin,
    UserAdmin,
)

app = FastAPI(title="Avtoban Admin", docs_url=None, redoc_url=None)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Static files for uploads
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="🏗 Avtoban Admin",
    base_url="/sqladmin",
)

admin.add_view(UserAdmin)
admin.add_view(OrderAdmin)
admin.add_view(ExpenseAdmin)
admin.add_view(MaterialRequestAdmin)
admin.add_view(AsphaltTypeAdmin)
admin.add_view(RegionAdmin)

# Include TMA routes and redirects AFTER SQLAdmin to override /admin
app.include_router(tma_router)
app.include_router(marketplace_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/tma-admin")


@app.get("/admin")
@app.get("/admin/")
async def admin_redirect():
    return RedirectResponse(url="/tma-admin")
