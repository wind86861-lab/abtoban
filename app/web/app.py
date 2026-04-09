from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import settings
from app.db.session import engine
from app.web.auth import AdminAuth
from app.web.views import (
    AsphaltTypeAdmin,
    ExpenseAdmin,
    MaterialRequestAdmin,
    OrderAdmin,
    RegionAdmin,
    UserAdmin,
)

app = FastAPI(title="Avtoban Admin", docs_url=None, redoc_url=None)


@app.get("/")
async def root():
    return RedirectResponse(url="/admin")

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="🏗 Avtoban Admin",
    base_url="/admin",
)

admin.add_view(UserAdmin)
admin.add_view(OrderAdmin)
admin.add_view(ExpenseAdmin)
admin.add_view(MaterialRequestAdmin)
admin.add_view(AsphaltTypeAdmin)
admin.add_view(RegionAdmin)
