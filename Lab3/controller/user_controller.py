from typing import List, Optional
from litestar import Controller, get, post, put, delete
from litestar.di import Provide
from litestar.params import Parameter
from litestar.exceptions import NotFoundException

from dto.user_create_dto import UserCreate
from dto.user_response import UserResponse
from service.user_service import UserService
import traceback

class UserController(Controller):
    path = "/users"
    dependencies = {"user_service": Provide(UserService)}

    @get("/{user_id:int}")
    async def get_user_by_id(
            self,
            user_service: UserService,
            user_id: int = Parameter(gt=0),
    ) -> UserResponse:
        """Получить пользователя по ID"""
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse

    @get()
    async def get_all_users(
            self,
            user_service: UserService,
            count: int = Parameter(gt=0, le=100, default=10),
            page: int = Parameter(gt=0, default=1),
            username: Optional[str] = None,
            email: Optional[str] = None,
    ) -> List[UserResponse]:
        """Получить список пользователей с пагинацией и фильтрацией"""
        filters = {}
        if username:
            filters["username"] = username
        if email:
            filters["email"] = email

        users = await user_service.get_by_filter(count, page, **filters)
        return [UserResponse.model_validate(user) for user in users]

    @post()
    async def create_user(
            self,
            user_service: UserService,
            user_data: UserCreate,
    ) -> UserResponse:
        user = await user_service.create(user_data)
        return UserResponse.model_validate(user)

    @delete("/{user_id:int}")
    async def delete_user(
            self,
            user_service: UserService,
            user_id: int = Parameter(gt=0),
    ) -> None:
        await user_service.delete(user_id)

    @put("/{user_id:int}")
    async def update_user(
            self,
            user_service: UserService,
            user_id: int = Parameter(gt=0)
    ) -> UserResponse:
        user = await user_service.update(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)