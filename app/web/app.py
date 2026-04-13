from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.session import engine
from app.web.auth import AdminAuth
from app.web.tma_routes import router as tma_router
from app.web.views import (
    AsphaltTypeAdmin,
    ExpenseAdmin,
    MaterialRequestAdmin,
    OrderAdmin,
    RegionAdmin,
    UserAdmin,
)

app = FastAPI(title="Avtoban Admin", docs_url=None, redoc_url=None)

app.include_router(tma_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/tma-admin")


@app.get("/admin")
@app.get("/admin/")
async def admin_redirect():
    return RedirectResponse(url="/tma-admin")

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

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
