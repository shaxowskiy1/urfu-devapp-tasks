from dataclasses import asdict
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.product_create_dto import ProductCreate
from dto.product_update_dto import ProductUpdate
from models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id) -> Optional[Product]:
        if isinstance(product_id, str):
            product_id = UUID(product_id)
        query = (
            select(Product)
                .options(selectinload(Product.orders))
                .where(Product.id == product_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[Product]:
        query = (
            select(Product)
                .options(selectinload(Product.orders))
                .limit(count)
                .offset((page - 1) * count)
        )

        for key, value in kwargs.items():
            if hasattr(Product, key) and value is not None:
                if isinstance(value, (list, tuple)):
                    query = query.where(getattr(Product, key).in_(value))
                else:
                    query = query.where(getattr(Product, key) == value)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, product_data: ProductCreate) -> Product:
        product_dict = asdict(product_data) if hasattr(product_data, '__dataclass_fields__') else product_data.__dict__
        product = Product(**product_dict)

        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def update(
            self, product_id, product_data: ProductUpdate
    ) -> Product:
        if isinstance(product_id, str):
            product_id = UUID(product_id)
            
        update_data = {}
        if hasattr(product_data, '__dataclass_fields__'):
            update_data = {k: v for k, v in asdict(product_data).items() if v is not None}
        else:
            update_data = {k: v for k, v in product_data.__dict__.items() if v is not None}

        if not update_data:
            return await self.get_by_id(product_id)

        query = (
            update(Product)
                .where(Product.id == product_id)
                .values(**update_data)
                .returning(Product)
        )

        await self.session.execute(query)
        await self.session.flush()

        return await self.get_by_id(product_id)

    async def delete(self, product_id) -> None:
        if isinstance(product_id, str):
            product_id = UUID(product_id)
        query = delete(Product).where(Product.id == product_id)
        await self.session.execute(query)
        await self.session.flush()

    async def get_all(self) -> list[Product]:
        query = select(Product).options(selectinload(Product.orders))
        result = await self.session.execute(query)
        return list(result.scalars().all())

