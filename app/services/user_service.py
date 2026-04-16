from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditLog, Region, User, UserRole


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.region))
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.region), selectinload(User.zavod))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)

        if user:
            changed = False
            if user.username != username:
                user.username = username
                changed = True
            if user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if changed:
                await self.session.flush()
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=UserRole.KLIENT,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_role(
        self,
        user_id: int,
        new_role: UserRole,
        changed_by_id: Optional[int] = None,
    ) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        old_role = user.role
        user.role = new_role
        await self.session.flush()

        if changed_by_id:
            log = AuditLog(
                user_id=changed_by_id,
                action="role_change",
                entity_type="user",
                entity_id=user_id,
                old_value=old_role.value,
                new_value=new_role.value,
            )
            self.session.add(log)
            await self.session.flush()

        return user

    async def update_phone(self, user_id: int, phone: str) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.phone = phone
        await self.session.flush()
        return user

    async def update_language(self, user_id: int, language: str) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.language = language
        await self.session.flush()
        return user

    async def set_active(
        self,
        user_id: int,
        is_active: bool,
        changed_by_id: Optional[int] = None,
    ) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        old_value = str(user.is_active)
        user.is_active = is_active
        await self.session.flush()

        if changed_by_id:
            log = AuditLog(
                user_id=changed_by_id,
                action="set_active" if is_active else "set_inactive",
                entity_type="user",
                entity_id=user_id,
                old_value=old_value,
                new_value=str(is_active),
            )
            self.session.add(log)
            await self.session.flush()

        return user

    async def get_all(
        self,
        role: Optional[UserRole] = None,
        only_active: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> List[User]:
        query = select(User)
        if only_active:
            query = query.where(User.is_active == True)
        if role:
            query = query.where(User.role == role)
        query = query.order_by(User.id).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(
        self,
        role: Optional[UserRole] = None,
        only_active: bool = True,
    ) -> int:
        from sqlalchemy import func
        query = select(func.count(User.id))
        if only_active:
            query = query.where(User.is_active == True)
        if role:
            query = query.where(User.role == role)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def update_region(
        self,
        user_id: int,
        region_id: int,
        changed_by_id: Optional[int] = None,
    ) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        old_region = str(user.region_id) if user.region_id else "none"
        user.region_id = region_id
        await self.session.flush()

        if changed_by_id:
            log = AuditLog(
                user_id=changed_by_id,
                action="region_change",
                entity_type="user",
                entity_id=user_id,
                old_value=old_region,
                new_value=str(region_id),
            )
            self.session.add(log)
            await self.session.flush()
        return user

    async def get_by_role_and_region(
        self,
        role: UserRole,
        region_id: int,
        only_active: bool = True,
    ) -> List[User]:
        query = select(User).where(User.role == role, User.region_id == region_id)
        if only_active:
            query = query.where(User.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_regions(self) -> List[Region]:
        result = await self.session.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        return list(result.scalars().all())

    async def get_zavods(self) -> list:
        from app.db.models import Zavod
        result = await self.session.execute(
            select(Zavod).where(Zavod.is_active == True).order_by(Zavod.name)
        )
        return list(result.scalars().all())

    async def update_zavod(
        self,
        user_id: int,
        zavod_id: int,
        changed_by_id: Optional[int] = None,
    ) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        old_zavod = str(user.zavod_id) if user.zavod_id else "none"
        user.zavod_id = zavod_id
        await self.session.flush()

        if changed_by_id:
            log = AuditLog(
                user_id=changed_by_id,
                action="zavod_change",
                entity_type="user",
                entity_id=user_id,
                old_value=old_zavod,
                new_value=str(zavod_id),
            )
            self.session.add(log)
            await self.session.flush()
        return user
