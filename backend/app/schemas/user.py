from pydantic import BaseModel, Field, model_validator


class ChangePasswordBody(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=256)
    new_password: str = Field(..., min_length=6, max_length=256)


class UserSummaryOut(BaseModel):
    id: int
    username: str
    is_admin: bool


class UserListOut(BaseModel):
    users: list[UserSummaryOut]


class CreateUserBody(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=256)
    is_admin: bool = False


class AdminUpdateUserBody(BaseModel):
    new_password: str | None = Field(None, min_length=6, max_length=256)
    is_admin: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "AdminUpdateUserBody":
        if self.new_password is None and self.is_admin is None:
            raise ValueError("Informe nova senha e/ou se o usuário é administrador.")
        return self
