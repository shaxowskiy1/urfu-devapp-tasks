from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AddressResponse:
    id: UUID
    user_id: UUID
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

