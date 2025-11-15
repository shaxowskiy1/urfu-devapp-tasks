from datetime import datetime
from uuid import UUID


class UserResponse():
    id: UUID
    created_at: datetime
    updated_at: datetime