from sqlite3 import IntegrityError
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from dto.user_create_dto import UserCreate
from dto.user_update_dto import UserUpdate
from models import User
from repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, user_id) -> Optional[User]:
        if not user_id:
            raise ValueError("User ID is required")

        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None

        return user

    async def get_by_filter(
            self, count: int, page: int, **kwargs
    ) -> list[User]:
        if count <= 0:
            raise ValueError("Count must be positive")
        if page <= 0:
            raise ValueError("Page must be positive")

        valid_filters = {}
        for key, value in kwargs.items():
            if value is not None and hasattr(User, key):
                valid_filters[key] = value

        users = await self.user_repository.get_by_filter(
            count, page, **valid_filters
        )
        return users

    async def create(self, user_data: UserCreate) -> User:
        if not user_data.username or not user_data.email:
            raise ValueError("Username and email are required")

        existing_users = await self.user_repository.get_by_filter(
            1, 1, username=user_data.username
        )
        if existing_users:
            raise ValueError(f"User with username '{user_data.username}' already exists")

        existing_users = await self.user_repository.get_by_filter(
            1, 1, email=user_data.email
        )
        if existing_users:
            raise ValueError(f"User with email '{user_data.email}' already exists")

        try:
            user = await self.user_repository.create(user_data)
            await self.user_repository.session.commit()
            return user
        except IntegrityError as e:
            await self.user_repository.session.rollback()
            if "username" in str(e).lower():
                raise ValueError(f"Username '{user_data.username}' already exists")
            elif "email" in str(e).lower():
                raise ValueError(f"Email '{user_data.email}' already exists")
            else:
                raise ValueError("User creation failed due to integrity constraints")
        except Exception as e:
            await self.user_repository.session.rollback()
            raise ValueError(f"Failed to create user: {str(e)}")

    async def update(
            self, user_id, user_data: UserUpdate
    ) -> User:
        if not user_id:
            raise ValueError("User ID is required")

        existing_user = await self.get_by_id(user_id)
        if not existing_user:
            raise ValueError(f"User with ID {user_id} not found")

        if user_data.username is not None:
            existing_users = await self.user_repository.get_by_filter(
                1, 1, username=user_data.username
            )
            if existing_users and existing_users[0].id != existing_user.id:
                raise ValueError(f"Username '{user_data.username}' already exists")

        if user_data.email is not None:
            existing_users = await self.user_repository.get_by_filter(
                1, 1, email=user_data.email
            )
            if existing_users and existing_users[0].id != existing_user.id:
                raise ValueError(f"Email '{user_data.email}' already exists")

        try:
            user = await self.user_repository.update(user_id, user_data)
            await self.user_repository.session.commit()
            return user
        except IntegrityError as e:
            await self.user_repository.session.rollback()
            raise ValueError(f"Update failed due to integrity constraints: {str(e)}")
        except Exception as e:
            await self.user_repository.session.rollback()
            raise ValueError(f"Failed to update user: {str(e)}")

    async def delete(self, user_id) -> None:
        if not user_id:
            raise ValueError("User ID is required")

        existing_user = await self.get_by_id(user_id)
        if not existing_user:
            raise ValueError(f"User with ID {user_id} not found")

        if existing_user.orders:
            raise ValueError("Cannot delete user with existing orders")

        try:
            await self.user_repository.delete(user_id)
            await self.user_repository.session.commit()
        except Exception as e:
            await self.user_repository.session.rollback()
            raise ValueError(f"Failed to delete user: {str(e)}")