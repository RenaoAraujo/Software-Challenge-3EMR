from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class UserSessionOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False
