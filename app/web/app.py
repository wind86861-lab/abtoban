import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, HTMLResponse

from app.config import settings
from app.db.session import engine
from app.web.auth import AdminAuth
from app.web.tma_routes import router as tma_router
from app.web.marketplace_routes import router as marketplace_router
from app.web.reports import ReportsView
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

# Static files for uploads and custom CSS
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)

admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="🏗 Avtoban Stroy - Admin Panel",
    base_url="/sqladmin",
    templates_dir=os.path.join(os.path.dirname(__file__), "templates"),
)

admin.add_view(ReportsView)
admin.add_view(UserAdmin)
admin.add_view(OrderAdmin)
admin.add_view(ExpenseAdmin)
admin.add_view(MaterialRequestAdmin)
admin.add_view(AsphaltTypeAdmin)
admin.add_view(RegionAdmin)

# Mount Master Panel
from app.web.master_app import master_app
app.mount("/master-panel", master_app)

# Include TMA routes and redirects AFTER SQLAdmin to override /admin
app.include_router(tma_router)
app.include_router(marketplace_router)

# Inject custom CSS
@app.get("/custom-admin-css")
async def custom_admin_css():
    return HTMLResponse("""
    <link rel="stylesheet" href="/static/custom_admin.css">
    <style>
        /* Additional inline styles for SQLAdmin */
        .navbar-brand::before {
            content: "🏗 ";
        }
    </style>
    """)


@app.get("/")
async def root():
    return RedirectResponse(url="/tma-admin")


@app.get("/admin")
@app.get("/admin/")
async def admin_redirect():
    return RedirectResponse(url="/tma-admin")
