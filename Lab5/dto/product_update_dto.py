from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductUpdate:
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

