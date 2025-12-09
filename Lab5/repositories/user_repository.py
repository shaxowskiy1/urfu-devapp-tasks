
from dataclasses import asdict
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.user_create_dto import UserCreate
from dto.user_update_dto import UserUpdate
from models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id) -> Optional[User]:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        query = (
            select(User)
                .options(selectinload(User.addresses), selectinload(User.orders))
                .where(User.id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[User]:
        query = (
            select(User)
                .options(selectinload(User.addresses), selectinload(User.orders))
                .limit(count)
                .offset((page - 1) * count)
        )

        for key, value in kwargs.items():
            if hasattr(User, key) and value is not None:
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(User, key).in_(value))
                else:
                    query = query.where(getattr(User, key) == value)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, user_data: UserCreate) -> User:
        user_dict = asdict(user_data) if hasattr(user_data, '__dataclass_fields__') else user_data.__dict__
        user = User(**user_dict)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(
            self, user_id, user_data: UserUpdate
    ) -> User:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
            
        update_data = {}
        if hasattr(user_data, '__dataclass_fields__'):
            update_data = {k: v for k, v in asdict(user_data).items() if v is not None}
        else:
            update_data = {k: v for k, v in user_data.__dict__.items() if v is not None}

        if not update_data:
            return await self.get_by_id(user_id)

        query = (
            update(User)
                .where(User.id == user_id)
                .values(**update_data)
                .returning(User)
        )

        await self.session.execute(query)
        await self.session.flush()

        return await self.get_by_id(user_id)

    async def delete(self, user_id) -> None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        query = delete(User).where(User.id == user_id)
        await self.session.execute(query)
        await self.session.flush()

    async def get_by_email(self, email: str) -> Optional[User]:
        query = (
            select(User)
                .options(selectinload(User.addresses), selectinload(User.orders))
                .where(User.email == email)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()