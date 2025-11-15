from typing import Optional

from typing import Optional
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.user_create_dto import UserCreate
from dto.user_update_dto import UserUpdate
from models import User


class UserRepository:
    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        query = (
            select(User)
                .options(selectinload(User.addresses), selectinload(User.orders))
                .where(User.id == user_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_filter(
            self, session: AsyncSession, count: int, page: int, **kwargs
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

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, user_data: UserCreate) -> User:
        user_dict = user_data.model_dump() if hasattr(user_data, 'model_dump') else user_data.dict()
        user = User(**user_dict)

        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def update(
            self, session: AsyncSession, user_id: int, user_data: UserUpdate
    ) -> User:
        update_data = {}
        if hasattr(user_data, 'model_dump'):
            update_data = user_data.model_dump(exclude_unset=True)
        else:
            update_data = user_data.dict(exclude_unset=True)

        if not update_data:
            return await self.get_by_id(session, user_id)

        query = (
            update(User)
                .where(User.id == user_id)
                .values(**update_data)
                .returning(User)
        )

        result = await session.execute(query)
        await session.flush()

        return await self.get_by_id(session, user_id)

    async def delete(self, session: AsyncSession, user_id: int) -> None:
        query = delete(User).where(User.id == user_id)
        await session.execute(query)
        await session.flush()