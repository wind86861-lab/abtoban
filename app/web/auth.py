import hashlib

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.config import settings
from app.db.models import User, UserRole
from app.db.session import async_session_maker


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = (form.get("username") or "").strip()
        password = form.get("password") or ""

        # 1) Main admin credentials
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"token": "authenticated", "user_role": "admin"})
            return True

        # 2) Master credentials (phone + password). Allows Masters who landed on
        #    /sqladmin/login to still sign in. The main app has a redirect
        #    middleware that will forward them to /master-panel/admin/.
        if username and password:
            async with async_session_maker() as session: 
                result = await session.execute(
                    select(User).where(
                        User.phone == username,
                        User.role == UserRole.MASTER,
                        User.is_active.is_(True),
                    )
                )
                user = result.scalar_one_or_none()
                if user and user.password_hash and user.password_hash == _hash_password(password):
                    request.session.update({
                        "token": "master_authenticated",
                        "user_id": user.id,
                        "user_role": "master",
                    })
                    return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        role = request.session.get("user_role")
        # Main admin panel is restricted to admin sessions only. Master
        # sessions are redirected away by FixMainRedirectMiddleware.
        if token == "authenticated" and role in (None, "admin"):
            return True
        if token == "master_authenticated":
            # Allow access through so the redirect middleware can send them
            # to /master-panel/admin/ instead of dropping them at /login.
            return True
        return False
