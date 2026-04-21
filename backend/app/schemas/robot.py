from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ManualRobotStatus = Literal["offline", "idle", "maintenance", "error"]


class RobotSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str
    model: str
    status: str
    online: bool = Field(description="Indicador simplificado: disponível (online) ou não (offline).")
    current_os_code: str | None = None
    units_separated: int = Field(default=0, description="Unidades já separadas na OS atual (0 se ocioso).")
    expected_units: int | None = Field(default=None, description="Meta da OS atual, se houver.")
    client_name: str | None = Field(default=None, description="Cliente da OS atual, se houver.")
    elapsed_seconds: int | None = Field(
        default=None,
        description="Tempo efetivo da OS em andamento ou pausada; null se não houver OS ativa.",
    )


class ServiceOrderBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    os_code: str
    description: str
    client_name: str = ""
    expected_units: int
    status: str
    medicines: list[str] = Field(default_factory=list, description="Itens da OS a separar.")


class RobotDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str
    model: str
    specifications: str
    max_units_per_hour: int
    status: str
    online: bool
    units_separated: int
    job_started_at: datetime | None
    elapsed_seconds: int | None = Field(
        default=None,
        description="Tempo desde o início da OS atual; null se ocioso.",
    )
    current_order: ServiceOrderBrief | None


class RobotCreateBody(BaseModel):
    code: str = Field(..., min_length=1, max_length=32, description="Código único do separador.")
    name: str = Field(..., min_length=1, max_length=128)
    location: str = Field(default="", max_length=256)
    model: str = Field(default="", max_length=128)
    specifications: str = Field(default="", max_length=16_000)
    max_units_per_hour: int = Field(default=500, ge=1, le=100_000)


class RobotUpdateBody(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=32)
    name: str | None = Field(None, min_length=1, max_length=128)
    location: str | None = Field(None, max_length=256)
    model: str | None = Field(None, max_length=128)
    specifications: str | None = Field(None, max_length=16_000)
    max_units_per_hour: int | None = Field(None, ge=1, le=100_000)
    status: ManualRobotStatus | None = Field(
        None,
        description="Somente ajuste manual: offline, idle, maintenance, error. 'running' é definido pela OS.",
    )


class CancellationReasonOption(BaseModel):
    """Item da lista de motivos de cancelamento (código + rótulo)."""

    code: str
    label: str


class CancelOrderBody(BaseModel):
    """Motivo do cancelamento da OS em execução no separador."""

    reason_code: str = Field(..., min_length=1, max_length=64, description="Código do motivo (preset ou OUTROS).")
    detail: str | None = Field(
        default=None,
        max_length=4000,
        description="Obrigatório quando reason_code é OUTROS: texto livre.",
    )

    @model_validator(mode="after")
    def require_detail_for_outros(self) -> "CancelOrderBody":
        from app.constants.cancellation_reasons import OUTROS_CODE

        if self.reason_code.strip() == OUTROS_CODE:
            if not (self.detail and self.detail.strip()):
                raise ValueError("Informe o motivo ao selecionar «Outros».")
        return self
