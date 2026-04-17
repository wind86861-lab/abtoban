import hashlib
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserRole
from app.db.session import async_session_maker


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


class MasterAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        phone = form.get("username", "").strip()
        password = form.get("password", "")
        
        if not phone or not password:
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
            
            if user:
                # Check if user has set a password
                if not user.password_hash:
                    return False
                
                # Verify password hash
                password_hash = hash_password(password)
                if password_hash == user.password_hash:
                    request.session.update({
                        "token": "master_authenticated",
                        "user_id": user.id,
                        "user_role": "master"
                    })
                    return True
        
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        user_role = request.session.get("user_role")
        
        if token == "master_authenticated" and user_role == "master":
            return True
        
        return False
