from datetime import date, datetime
from typing import Literal

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


class OrderReportItem(BaseModel):
    """Uma linha do relatório por OS (concluída ou cancelada)."""

    id: int
    os_code: str
    client_name: str = ""
    data: date = Field(description="Dia civil (Brasília) da conclusão ou do cancelamento.")
    separador_nome: str | None = Field(
        default=None,
        description="Nome do separador (snapshot ou cadastro atual).",
    )
    unidades_totais: int = Field(ge=0, description="Unidades concluídas (se concluída) ou previstas (se cancelada).")
    situacao: Literal["concluida", "cancelada"]


class OrdersReportResponse(BaseModel):
    total: int = Field(ge=0, description="Total de linhas que batem o filtro (não só esta página).")
    items: list[OrderReportItem] = Field(default_factory=list)
