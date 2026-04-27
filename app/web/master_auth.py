import hashlib
import logging
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserRole
from app.db.session import async_session_maker

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


class MasterAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        phone = form.get("username", "").strip()
        password = form.get("password", "")
        
        logger.info(f"Master login attempt - Phone: {phone}")
        
        if not phone or not password:
            logger.warning("Missing phone or password")
            return False
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(
                    User.phone == phone,
                    User.role == UserRole.MASTER,
                    User.is_active == True
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"User not found: {phone}")
                return False
            
            # Check if user has set a password
            if not user.password_hash:
                logger.warning(f"User {phone} has no password set")
                return False
            
            # Verify password hash
            password_hash = hash_password(password)
            if password_hash == user.password_hash:
                logger.info(f"Login successful for {phone}")
                request.session.update({
                    "token": "master_authenticated",
                    "user_id": user.id,
                    "user_role": "master"
                })
                return True
            else:
                logger.warning(f"Invalid password for {phone}")
                return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # New custom-login token (set by master_app custom /admin/login POST)
        if request.session.get("master_token") == "authenticated":
            return True
        # Legacy fallback: old sqladmin-based login token
        if (request.session.get("token") == "master_authenticated"
                and request.session.get("user_role") == "master"):
            return True
        return False
