from pydantic import BaseModel, ConfigDict, Field


class ServiceOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    os_code: str = Field(..., max_length=64)
    description: str
    client_name: str = ""
    expected_units: int
    status: str
    medicines: list[str] = Field(default_factory=list)
