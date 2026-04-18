from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    username: str
    action: str
    description: str = ""
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def serialize_created_at_utc(self, v: datetime) -> str:
        """SQLite/devolve às vezes naive UTC; o JSON sem fuso faz o browser tratar como local errado."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        else:
            v = v.astimezone(timezone.utc)
        return v.isoformat().replace("+00:00", "Z")


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int


class AuditLogsClearOut(BaseModel):
    deleted: int = Field(ge=0, description="Quantidade de linhas removidas.")
