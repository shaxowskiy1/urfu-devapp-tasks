from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class UserResponse:
    id: UUID
    username: str
    email: str
    description: str | None
    created_at: datetime
    updated_at: datetime