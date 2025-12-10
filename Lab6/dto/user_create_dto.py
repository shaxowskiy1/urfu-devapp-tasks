from dataclasses import dataclass
from typing import Optional

@dataclass
class UserCreate():
    username: str
    email: str
    description: Optional[str] = None