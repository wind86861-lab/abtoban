import hashlib
import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqladmin import Admin
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.db.models import User, UserRole
from app.db.session import async_session_maker, engine
from app.web.master_auth import MasterAuth
from app.web.master_views import MasterOrderAdmin
from app.web.master_dashboard import MasterDashboardView
from app.web.master_clients import MasterClientsView
from app.web.master_commission import MasterCommissionView
from app.web.master_usta_assign import MasterUstaAssignView
from app.web.master_expense_entry import MasterExpenseView
from app.web.master_order_actions import MasterOrderActionsView
from app.web.web_lang import WebLangMiddleware, patch_admin_i18n, SUPPORTED_LANGS

_TEMPLATES = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# Create Master panel app
master_app = FastAPI(title="Master Panel", docs_url=None, redoc_url=None)


class FixRedirectMiddleware(BaseHTTPMiddleware):
    """Rewrite redirect Location headers that point to the main /sqladmin
    panel so that Master users are kept inside /master-panel/admin."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        location = response.headers.get("location")
        if location and "/sqladmin" in location:
            new_location = location.replace("/sqladmin", "/master-panel/admin")
            response.headers["location"] = new_location
        return response


master_app.add_middleware(FixRedirectMiddleware)
master_app.add_middleware(WebLangMiddleware)
master_app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# ── Custom login routes registered BEFORE SQLAdmin so they take priority ──────

@master_app.get("/admin/login", response_class=HTMLResponse)
async def master_login_page(request: Request, error: str = ""):
    return _TEMPLATES.TemplateResponse(
        "master_login.html", {"request": request, "error": error}
    )


@master_app.post("/admin/login", response_class=HTMLResponse)
async def master_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    phone = username.strip()

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(
                User.phone == phone,
                User.role == UserRole.MASTER,
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()

    if not user:
        return _TEMPLATES.TemplateResponse(
            "master_login.html",
            {"request": request, "error": "Telefon raqam topilmadi yoki siz Master emassiz."},
            status_code=200,
        )

    if not user.password_hash:
        return _TEMPLATES.TemplateResponse(
            "master_login.html",
            {
                "request": request,
                "error": (
                    "Siz hali web panel uchun parol o'rnatmagansiz. "
                    "Iltimos, Telegram botda <b>⚙️ Parolni O'zgartirish</b> tugmasini bosib parol o'rnating."
                ),
            },
            status_code=200,
        )

    if _hash(password) != user.password_hash:
        return _TEMPLATES.TemplateResponse(
            "master_login.html",
            {"request": request, "error": "Parol noto'g'ri. Qayta urinib ko'ring."},
            status_code=200,
        )

    request.session["master_token"] = "authenticated"
    request.session["master_user_id"] = user.id
    request.session["user_id"] = user.id
    request.session["user_role"] = "master"
    request.session["token"] = "master_authenticated"
    return RedirectResponse(url="/master-panel/admin/dashboard", status_code=303)


@master_app.get("/admin/")
async def master_index_redirect(request: Request):
    """Always redirect master panel index to dashboard."""
    return RedirectResponse(url="/master-panel/admin/dashboard", status_code=302)


@master_app.get("/admin/logout")
async def master_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/master-panel/admin/login", status_code=303)

# ──────────────────────────────────────────────────────────────────────────────

# Setup Master authentication
master_auth = MasterAuth(secret_key=settings.SECRET_KEY)

# Create Admin panel for Master
master_admin = Admin(
    app=master_app,
    engine=engine,
    authentication_backend=master_auth,
    title="🏗 Avtoban Stroy - Master Panel",
    base_url="/admin",
    templates_dir=os.path.join(os.path.dirname(__file__), "templates"),
)

patch_admin_i18n(master_admin)

# Add Master views - Dashboard first, then main functionality
master_admin.add_view(MasterDashboardView)
master_admin.add_view(MasterOrderAdmin)
master_admin.add_view(MasterOrderActionsView)
master_admin.add_view(MasterUstaAssignView)
master_admin.add_view(MasterExpenseView)
master_admin.add_view(MasterClientsView)
master_admin.add_view(MasterCommissionView)


@master_app.get("/set-lang")
async def master_set_language(request: Request, lang: str = "uz_lat", next: str = "/master-panel/admin/"):
    if lang in SUPPORTED_LANGS:
        request.session["web_lang"] = lang
    return RedirectResponse(url=next, status_code=303)
