import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, HTMLResponse

from app.config import settings
from app.db.session import engine
from app.web.auth import AdminAuth
from app.web.web_lang import WebLangMiddleware, patch_admin_i18n, SUPPORTED_LANGS
from app.web.tma_routes import router as tma_router
from app.web.marketplace_routes import router as marketplace_router
from app.web.reports import ReportsView
from app.web.views import (
    AsphaltCategoryAdmin,
    AsphaltSubCategoryAdmin,
    AsphaltTypeAdmin,
    ExpenseAdmin,
    MarketOrderAdmin,
    MaterialRequestAdmin,
    OrderAdmin,
    PortfolioAdmin,
    ProductAdmin,
    RegionAdmin,
    ShopCategoryAdmin,
    TumanAdmin,
    UserAdmin,
    ViloyatAdmin,
    ZavodAdmin,
)

app = FastAPI(title="Avtoban Admin", docs_url=None, redoc_url=None)


class TMAAuthMiddleware:
    """Pure ASGI middleware. Blocks unauthenticated access to /tma-admin and
    /tma-api/* routes. Runs innermost so scope['session'] is already set by
    SessionMiddleware."""

    _PUBLIC = {"/tma-login", "/tma-logout"}
    _PROTECTED_PREFIXES = ("/tma-api/", "/tma-admin")

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        protected = any(path.startswith(p) for p in self._PROTECTED_PREFIXES)
        public = path in self._PUBLIC

        if protected and not public:
            session = scope.get("session") or {}
            token = session.get("tma_token")
            if token not in ("admin_ok", "superadmin_ok"):
                from urllib.parse import urlencode
                qs = urlencode({"next": path})
                location = f"/tma-login?{qs}".encode("latin-1")
                await send({
                    "type": "http.response.start",
                    "status": 302,
                    "headers": [(b"location", location), (b"content-length", b"0")],
                })
                await send({"type": "http.response.body", "body": b""})
                return

        await self.app(scope, receive, send)


class RouteMastersAwayMiddleware:
    """Pure ASGI middleware. Rewrites Location headers on redirect responses
    so that users whose session ends up with ``user_role == 'master'`` get
    sent to ``/master-panel/admin/...`` instead of ``/sqladmin/...``.

    Runs AFTER SessionMiddleware so ``scope['session']`` is always present.
    Using a pure-ASGI wrapper lets us inspect the session at the moment the
    downstream app sends its response-start — which is after the session
    dict has been mutated by the login handler.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                session = scope.get("session") or {}
                if session.get("user_role") == "master":
                    status = message.get("status", 200)
                    if status in (301, 302, 303, 307, 308):
                        headers = [list(h) for h in message.get("headers", [])]
                        for i, (name, value) in enumerate(headers):
                            if name.lower() == b"location":
                                loc = value.decode("latin-1")
                                if "/sqladmin" in loc:
                                    loc = loc.replace(
                                        "/sqladmin", "/master-panel/admin", 1
                                    )
                                    headers[i] = [b"location", loc.encode("latin-1")]
                        message["headers"] = [tuple(h) for h in headers]
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Middleware order: added LAST = outermost = runs FIRST.
# Session must be outermost so scope['session'] is set before inner middleware.
# TMAAuthMiddleware must be innermost (added first) so it can read the session.
app.add_middleware(TMAAuthMiddleware)
app.add_middleware(WebLangMiddleware)
app.add_middleware(RouteMastersAwayMiddleware)
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

patch_admin_i18n(admin)

admin.add_view(ReportsView)
admin.add_view(UserAdmin)
admin.add_view(OrderAdmin)
admin.add_view(ExpenseAdmin)
admin.add_view(MaterialRequestAdmin)
admin.add_view(AsphaltCategoryAdmin)
admin.add_view(AsphaltSubCategoryAdmin)
admin.add_view(AsphaltTypeAdmin)
admin.add_view(ViloyatAdmin)
admin.add_view(TumanAdmin)
admin.add_view(RegionAdmin)
admin.add_view(ZavodAdmin)
admin.add_view(ShopCategoryAdmin)
admin.add_view(ProductAdmin)
admin.add_view(PortfolioAdmin)
admin.add_view(MarketOrderAdmin)

# Mount Master Panel
from app.web.master_app import master_app
app.mount("/master-panel", master_app)

# ── Language switcher endpoint ──────────────────────────────────────────────
@app.get("/set-lang")
async def set_language(request: Request, lang: str = "uz_lat", next: str = "/"):
    if lang in SUPPORTED_LANGS:
        request.session["web_lang"] = lang
    return RedirectResponse(url=next, status_code=303)

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
