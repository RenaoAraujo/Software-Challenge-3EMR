from pydantic import BaseModel, ConfigDict, Field


class ManualOrderCreate(BaseModel):
    """Criação manual de OS para testes (itens gerados automaticamente)."""

    os_code: str = Field(..., min_length=1, max_length=64)
    client_name: str = Field(default="", max_length=256)
    robot_id: int = Field(..., ge=1)
    quantidade_remedios: int = Field(..., ge=1, le=500)


class ServiceOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    os_code: str = Field(..., max_length=64)
    description: str
    client_name: str = ""
    expected_units: int
    status: str
    medicines: list[str] = Field(default_factory=list)
