from typing import Optional


class UserCreate():
    username: str
    email: str
    description: Optional[str] = None