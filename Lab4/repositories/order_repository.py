from dataclasses import asdict
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.order_create_dto import OrderCreate
from dto.order_update_dto import OrderUpdate
from models import Order


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id) -> Optional[Order]:
        if isinstance(order_id, str):
            order_id = UUID(order_id)
        query = (
            select(Order)
                .options(
                    selectinload(Order.user),
                    selectinload(Order.address),
                    selectinload(Order.product)
                )
                .where(Order.id == order_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[Order]:
        query = (
            select(Order)
                .options(
                    selectinload(Order.user),
                    selectinload(Order.address),
                    selectinload(Order.product)
                )
                .limit(count)
                .offset((page - 1) * count)
        )

        for key, value in kwargs.items():
            if hasattr(Order, key) and value is not None:
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(Order, key).in_(value))
                else:
                    query = query.where(getattr(Order, key) == value)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, order_data: OrderCreate) -> Order:
        order_dict = asdict(order_data) if hasattr(order_data, '__dataclass_fields__') else order_data.__dict__
        order = Order(**order_dict)

        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def update(
            self, order_id, order_data: OrderUpdate
    ) -> Order:
        if isinstance(order_id, str):
            order_id = UUID(order_id)
            
        update_data = {}
        if hasattr(order_data, '__dataclass_fields__'):
            update_data = {k: v for k, v in asdict(order_data).items() if v is not None}
        else:
            update_data = {k: v for k, v in order_data.__dict__.items() if v is not None}

        if not update_data:
            return await self.get_by_id(order_id)

        query = (
            update(Order)
                .where(Order.id == order_id)
                .values(**update_data)
                .returning(Order)
        )

        await self.session.execute(query)
        await self.session.flush()

        return await self.get_by_id(order_id)

    async def delete(self, order_id) -> None:
        if isinstance(order_id, str):
            order_id = UUID(order_id)
        query = delete(Order).where(Order.id == order_id)
        await self.session.execute(query)
        await self.session.flush()

    async def get_by_user_id(self, user_id) -> list[Order]:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        query = (
            select(Order)
                .options(
                    selectinload(Order.user),
                    selectinload(Order.address),
                    selectinload(Order.product)
                )
                .where(Order.user_id == user_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(self) -> list[Order]:
        query = (
            select(Order)
                .options(
                    selectinload(Order.user),
                    selectinload(Order.address),
                    selectinload(Order.product)
                )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

