import os

from fastapi import FastAPI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.config import settings
from app.db.session import engine
from app.web.master_auth import MasterAuth
from app.web.master_views import MasterOrderAdmin
from app.web.master_dashboard import MasterDashboardView
from app.web.master_clients import MasterClientsView
from app.web.master_commission import MasterCommissionView

# Create Master panel app
master_app = FastAPI(title="Master Panel", docs_url=None, redoc_url=None)

master_app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
master_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Master authentication
master_auth = MasterAuth(secret_key=settings.SECRET_KEY)

# Create Admin panel for Master
master_admin = Admin(
    app=master_app,
    engine=engine,
    authentication_backend=master_auth,
    title="🏗 Avtoban Stroy - Master Panel",
    base_url="/master",
    templates_dir=os.path.join(os.path.dirname(__file__), "templates"),
)

# Add Master views - Dashboard first, then main functionality
master_admin.add_view(MasterDashboardView)
master_admin.add_view(MasterOrderAdmin)
master_admin.add_view(MasterClientsView)
master_admin.add_view(MasterCommissionView)

# Custom CSS injection
@master_app.on_event("startup")
async def inject_custom_css():
    """Inject custom CSS for orange/black theme"""
    pass
