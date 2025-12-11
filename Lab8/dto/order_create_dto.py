from dataclasses import dataclass
from uuid import UUID


@dataclass
class OrderCreate:
    user_id: UUID
    address_id: UUID
    product_id: UUID
    quantity: int = 1
    total_price: float = 0.0
    status: str = "pending"


