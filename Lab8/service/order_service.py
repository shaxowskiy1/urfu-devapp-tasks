from sqlite3 import IntegrityError
from typing import Optional

from models import Order
from repositories.order_repository import OrderRepository
from repositories.user_repository import UserRepository
from repositories.product_repository import ProductRepository
from repositories.address_repository import AddressRepository


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        address_repository: AddressRepository
    ):
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.product_repository = product_repository
        self.address_repository = address_repository

    async def get_by_id(self, order_id) -> Optional[Order]:
        if not order_id:
            raise ValueError("Order ID is required")

        order = await self.order_repository.get_by_id(order_id)

        if not order:
            return None

        return order

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[Order]:
        if count <= 0:
            raise ValueError("Count must be positive")
        if page <= 0:
            raise ValueError("Page must be positive")

        valid_filters = {}
        for key, value in kwargs.items():
            if value is not None and hasattr(Order, key):
                valid_filters[key] = value

        orders = await self.order_repository.get_by_filter(
            count, page, **valid_filters
        )
        return orders

    async def create(self, order_data) -> Order:
        if not order_data.user_id or not order_data.product_id or not order_data.address_id:
            raise ValueError("User ID, product ID, and address ID are required")

        if order_data.quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Verify user exists
        user = await self.user_repository.get_by_id(order_data.user_id)
        if not user:
            raise ValueError(f"User with ID {order_data.user_id} not found")

        # Verify product exists
        product = await self.product_repository.get_by_id(order_data.product_id)
        if not product:
            raise ValueError(f"Product with ID {order_data.product_id} not found")

        # Verify address exists and belongs to user
        address = await self.address_repository.get_by_id(order_data.address_id)
        if not address:
            raise ValueError(f"Address with ID {order_data.address_id} not found")
        if address.user_id != order_data.user_id:
            raise ValueError("Address does not belong to the specified user")

        # Calculate total price if not provided
        if order_data.total_price == 0.0:
            order_data.total_price = product.price * order_data.quantity

        try:
            order = await self.order_repository.create(order_data)
            await self.order_repository.session.commit()
            return order
        except IntegrityError as e:
            await self.order_repository.session.rollback()
            raise ValueError(f"Order creation failed: {str(e)}")
        except Exception as e:
            await self.order_repository.session.rollback()
            raise ValueError(f"Failed to create order: {str(e)}")

    async def update(
            self, order_id, order_data
    ) -> Order:
        if not order_id:
            raise ValueError("Order ID is required")

        existing_order = await self.get_by_id(order_id)
        if not existing_order:
            raise ValueError(f"Order with ID {order_id} not found")

        if order_data.quantity is not None and order_data.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if order_data.total_price is not None and order_data.total_price < 0:
            raise ValueError("Total price must be non-negative")

        valid_statuses = ["pending", "processing", "completed", "cancelled"]
        if order_data.status is not None and order_data.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        try:
            order = await self.order_repository.update(order_id, order_data)
            await self.order_repository.session.commit()
            return order
        except IntegrityError as e:
            await self.order_repository.session.rollback()
            raise ValueError(f"Update failed due to integrity constraints: {str(e)}")
        except Exception as e:
            await self.order_repository.session.rollback()
            raise ValueError(f"Failed to update order: {str(e)}")

    async def delete(self, order_id) -> None:
        if not order_id:
            raise ValueError("Order ID is required")

        existing_order = await self.get_by_id(order_id)
        if not existing_order:
            raise ValueError(f"Order with ID {order_id} not found")

        try:
            await self.order_repository.delete(order_id)
            await self.order_repository.session.commit()
        except Exception as e:
            await self.order_repository.session.rollback()
            raise ValueError(f"Failed to delete order: {str(e)}")

    async def get_by_user_id(self, user_id) -> list[Order]:
        return await self.order_repository.get_by_user_id(user_id)

    async def get_all(self) -> list[Order]:
        return await self.order_repository.get_all()


