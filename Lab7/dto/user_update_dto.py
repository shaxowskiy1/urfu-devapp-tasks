from dataclasses import dataclass
from typing import Optional


@dataclass
class UserUpdate:
    username: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None