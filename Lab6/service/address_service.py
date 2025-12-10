from sqlite3 import IntegrityError
from typing import Optional

from dto.address_update_dto import AddressUpdate
from models import Address
from repositories.address_repository import AddressRepository
from repositories.user_repository import UserRepository


class AddressService:
    def __init__(self, address_repository: AddressRepository, user_repository: UserRepository):
        self.address_repository = address_repository
        self.user_repository = user_repository

    async def get_by_id(self, address_id) -> Optional[Address]:
        if not address_id:
            raise ValueError("Address ID is required")

        address = await self.address_repository.get_by_id(address_id)

        if not address:
            return None

        return address

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[Address]:
        if count <= 0:
            raise ValueError("Count must be positive")
        if page <= 0:
            raise ValueError("Page must be positive")

        valid_filters = {}
        for key, value in kwargs.items():
            if value is not None and hasattr(Address, key):
                valid_filters[key] = value

        addresses = await self.address_repository.get_by_filter(
            count, page, **valid_filters
        )
        return addresses

    async def create(self, address_data) -> Address:
        if not address_data.street or not address_data.city or not address_data.country:
            raise ValueError("Street, city, and country are required")

        user = await self.user_repository.get_by_id(address_data.user_id)
        if not user:
            raise ValueError(f"User with ID {address_data.user_id} not found")

        if address_data.is_primary:
            existing_addresses = await self.address_repository.get_by_user_id(address_data.user_id)
            for addr in existing_addresses:
                if addr.is_primary:
                    update_data = AddressUpdate(is_primary=False)
                    await self.address_repository.update(addr.id, update_data)

        try:
            address = await self.address_repository.create(address_data)
            await self.address_repository.session.commit()
            return address
        except IntegrityError as e:
            await self.address_repository.session.rollback()
            raise ValueError(f"Address creation failed: {str(e)}")
        except Exception as e:
            await self.address_repository.session.rollback()
            raise ValueError(f"Failed to create address: {str(e)}")

    async def update(
            self, address_id, address_data
    ) -> Address:
        if not address_id:
            raise ValueError("Address ID is required")

        existing_address = await self.get_by_id(address_id)
        if not existing_address:
            raise ValueError(f"Address with ID {address_id} not found")

        if hasattr(address_data, 'is_primary') and address_data.is_primary:
            existing_addresses = await self.address_repository.get_by_user_id(existing_address.user_id)
            for addr in existing_addresses:
                if addr.is_primary and addr.id != existing_address.id:
                    update_data = AddressUpdate(is_primary=False)
                    await self.address_repository.update(addr.id, update_data)

        try:
            address = await self.address_repository.update(address_id, address_data)
            await self.address_repository.session.commit()
            return address
        except IntegrityError as e:
            await self.address_repository.session.rollback()
            raise ValueError(f"Update failed due to integrity constraints: {str(e)}")
        except Exception as e:
            await self.address_repository.session.rollback()
            raise ValueError(f"Failed to update address: {str(e)}")

    async def delete(self, address_id) -> None:
        if not address_id:
            raise ValueError("Address ID is required")

        existing_address = await self.get_by_id(address_id)
        if not existing_address:
            raise ValueError(f"Address with ID {address_id} not found")

        if existing_address.orders:
            raise ValueError("Cannot delete address with existing orders")

        try:
            await self.address_repository.delete(address_id)
            await self.address_repository.session.commit()
        except Exception as e:
            await self.address_repository.session.rollback()
            raise ValueError(f"Failed to delete address: {str(e)}")

    async def get_by_user_id(self, user_id) -> list[Address]:
        return await self.address_repository.get_by_user_id(user_id)

    async def get_all(self) -> list[Address]:
        return await self.address_repository.get_all()

