from dataclasses import dataclass
from uuid import UUID


@dataclass
class AddressCreate:
    user_id: UUID
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    is_primary: bool = False


