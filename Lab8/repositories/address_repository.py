from dataclasses import asdict
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.address_create_dto import AddressCreate
from dto.address_update_dto import AddressUpdate
from models import Address


class AddressRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, address_id) -> Optional[Address]:
        if isinstance(address_id, str):
            address_id = UUID(address_id)
        query = (
            select(Address)
                .options(selectinload(Address.user), selectinload(Address.orders))
                .where(Address.id == address_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[Address]:
        query = (
            select(Address)
                .options(selectinload(Address.user), selectinload(Address.orders))
                .limit(count)
                .offset((page - 1) * count)
        )

        for key, value in kwargs.items():
            if hasattr(Address, key) and value is not None:
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(Address, key).in_(value))
                else:
                    query = query.where(getattr(Address, key) == value)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, address_data: AddressCreate) -> Address:
        address_dict = asdict(address_data) if hasattr(address_data, '__dataclass_fields__') else address_data.__dict__
        address = Address(**address_dict)

        self.session.add(address)
        await self.session.flush()
        await self.session.refresh(address)
        return address

    async def update(
            self, address_id, address_data: AddressUpdate
    ) -> Address:
        if isinstance(address_id, str):
            address_id = UUID(address_id)
            
        update_data = {}
        if hasattr(address_data, '__dataclass_fields__'):
            update_data = {k: v for k, v in asdict(address_data).items() if v is not None}
        else:
            update_data = {k: v for k, v in address_data.__dict__.items() if v is not None}

        if not update_data:
            return await self.get_by_id(address_id)

        query = (
            update(Address)
                .where(Address.id == address_id)
                .values(**update_data)
                .returning(Address)
        )

        await self.session.execute(query)
        await self.session.flush()

        return await self.get_by_id(address_id)

    async def delete(self, address_id) -> None:
        if isinstance(address_id, str):
            address_id = UUID(address_id)
        query = delete(Address).where(Address.id == address_id)
        await self.session.execute(query)
        await self.session.flush()

    async def get_by_user_id(self, user_id) -> list[Address]:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        query = (
            select(Address)
                .options(selectinload(Address.user), selectinload(Address.orders))
                .where(Address.user_id == user_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(self) -> list[Address]:
        query = select(Address).options(selectinload(Address.user), selectinload(Address.orders))
        result = await self.session.execute(query)
        return list(result.scalars().all())

