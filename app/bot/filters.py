from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery

from app.db.models import User, UserRole


class RoleFilter(Filter):
    def __init__(self, *roles: UserRole) -> None:
        self.roles = set(roles)

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User,
    ) -> bool:
        return user.role in self.roles


class ActiveUserFilter(Filter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        user: User,
    ) -> bool:
        return user is not None and user.is_active
