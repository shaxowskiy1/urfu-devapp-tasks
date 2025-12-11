from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderUpdate:
    quantity: Optional[int] = None
    total_price: Optional[float] = None
    status: Optional[str] = None


