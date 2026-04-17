from pydantic import BaseModel, Field


class AssignOrderBody(BaseModel):
    service_order_id: int = Field(..., ge=1)
