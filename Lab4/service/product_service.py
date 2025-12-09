from sqlite3 import IntegrityError
from typing import Optional

from models import Product
from repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def get_by_id(self, product_id) -> Optional[Product]:
        if not product_id:
            raise ValueError("Product ID is required")

        product = await self.product_repository.get_by_id(product_id)

        if not product:
            return None

        return product

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[Product]:
        if count <= 0:
            raise ValueError("Count must be positive")
        if page <= 0:
            raise ValueError("Page must be positive")

        valid_filters = {}
        for key, value in kwargs.items():
            if value is not None and hasattr(Product, key):
                valid_filters[key] = value

        products = await self.product_repository.get_by_filter(
            count, page, **valid_filters
        )
        return products

    async def create(self, product_data) -> Product:
        if not product_data.name:
            raise ValueError("Product name is required")
        if product_data.price < 0:
            raise ValueError("Product price must be non-negative")

        try:
            product = await self.product_repository.create(product_data)
            await self.product_repository.session.commit()
            return product
        except IntegrityError as e:
            await self.product_repository.session.rollback()
            raise ValueError(f"Product creation failed: {str(e)}")
        except Exception as e:
            await self.product_repository.session.rollback()
            raise ValueError(f"Failed to create product: {str(e)}")

    async def update(
            self, product_id, product_data
    ) -> Product:
        if not product_id:
            raise ValueError("Product ID is required")

        existing_product = await self.get_by_id(product_id)
        if not existing_product:
            raise ValueError(f"Product with ID {product_id} not found")

        if product_data.price is not None and product_data.price < 0:
            raise ValueError("Product price must be non-negative")

        try:
            product = await self.product_repository.update(product_id, product_data)
            await self.product_repository.session.commit()
            return product
        except IntegrityError as e:
            await self.product_repository.session.rollback()
            raise ValueError(f"Update failed due to integrity constraints: {str(e)}")
        except Exception as e:
            await self.product_repository.session.rollback()
            raise ValueError(f"Failed to update product: {str(e)}")

    async def delete(self, product_id) -> None:
        if not product_id:
            raise ValueError("Product ID is required")

        existing_product = await self.get_by_id(product_id)
        if not existing_product:
            raise ValueError(f"Product with ID {product_id} not found")

        if existing_product.orders:
            raise ValueError("Cannot delete product with existing orders")

        try:
            await self.product_repository.delete(product_id)
            await self.product_repository.session.commit()
        except Exception as e:
            await self.product_repository.session.rollback()
            raise ValueError(f"Failed to delete product: {str(e)}")

    async def get_all(self) -> list[Product]:
        return await self.product_repository.get_all()

