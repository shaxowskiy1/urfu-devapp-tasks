from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class OrderResponse:
    id: UUID
    user_id: UUID
    address_id: UUID
    product_id: UUID
    quantity: int
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime

