from datetime import datetime, timezone

from pydantic import BaseModel, field_serializer


class OsCompletionNotificationItem(BaseModel):
    id: int
    created_at: datetime
    description: str
    username: str

    @field_serializer("created_at", when_used="json")
    def serialize_created_at_utc(self, v: datetime) -> str:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        else:
            v = v.astimezone(timezone.utc)
        return v.isoformat().replace("+00:00", "Z")


class OsCompletionFeedOut(BaseModel):
    items: list[OsCompletionNotificationItem]
