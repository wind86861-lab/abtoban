"""
Request-scoped language support for the web panel.

Usage:
    1. Register the middleware in both main app and master_app.
    2. After Admin() creation, call ``patch_admin_i18n(admin)`` to inject ``t()`` into Jinja2 globals.
    3. In templates: ``{{ t('key') }}``
"""

from contextvars import ContextVar
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.web.web_i18n import get_translator

# ── Context variable that holds the current request language ────────────────
_current_lang: ContextVar[str] = ContextVar("web_lang", default="uz_lat")

DEFAULT_LANG = "uz_lat"
SUPPORTED_LANGS = ("uz_lat", "uz_cyr", "ru")
LANG_FLAGS = {"uz_lat": "🇺🇿", "uz_cyr": "🇺🇿", "ru": "🇷🇺"}


def _t_global(key: str) -> str:
    """Jinja2 global ``t('key')`` — resolves from the request-scoped language."""
    lang = _current_lang.get()
    return get_translator(lang)(key)


def _lang_global() -> str:
    """Jinja2 global ``current_lang()`` — returns current language code."""
    return _current_lang.get()


# ── Pure-ASGI middleware (works with both main app and sub-apps) ────────────
class WebLangMiddleware:
    """Reads ``session['web_lang']`` and sets the context-var before each request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            session = scope.get("session") or {}
            lang = session.get("web_lang", DEFAULT_LANG)
            if lang not in SUPPORTED_LANGS:
                lang = DEFAULT_LANG
            token = _current_lang.set(lang)
            try:
                await self.app(scope, receive, send)
            finally:
                _current_lang.reset(token)
        else:
            await self.app(scope, receive, send)


def patch_admin_i18n(admin_instance):
    """Inject ``t`` and ``current_lang`` into the sqladmin Jinja2 environment."""
    env = admin_instance.templates.env
    env.globals["t"] = _t_global
    env.globals["current_lang"] = _lang_global
    env.globals["SUPPORTED_LANGS"] = SUPPORTED_LANGS
    env.globals["LANG_FLAGS"] = LANG_FLAGS


def patch_jinja_i18n(templates):
    """Inject ``t`` and ``current_lang`` into a plain Jinja2Templates instance."""
    env = templates.env
    env.globals["t"] = _t_global
    env.globals["current_lang"] = _lang_global
    env.globals["SUPPORTED_LANGS"] = SUPPORTED_LANGS
    env.globals["LANG_FLAGS"] = LANG_FLAGS
