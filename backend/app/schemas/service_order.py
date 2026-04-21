from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ManualOrderCreate(BaseModel):
    """Criação manual de OS para testes (itens gerados automaticamente)."""

    os_code: str = Field(..., min_length=1, max_length=64)
    client_name: str = Field(default="", max_length=256)
    robot_id: int = Field(..., ge=1)
    quantidade_remedios: int = Field(..., ge=1, le=500)
    reopen_cancelled: Literal["resume", "restart"] | None = Field(
        default=None,
        description=(
            "Ao reutilizar o código de uma OS cancelada: retomar progresso (resume) "
            "ou refazer lista e contagem (restart). Omitir na primeira tentativa para receber 409."
        ),
    )


class MedicineReportLine(BaseModel):
    """Uma linha de medicamento no export (lista da OS, ordem = coleta)."""

    remedio_id: str = ""
    remedio: str = ""
    tipo_remedio: str = ""
    classe_remedio: str = ""
    numero: int = 0
    tempo_gasto: str = ""
    situacao_coleta: Literal["concluida", "cancelada"] = Field(
        default="concluida",
        description="Por remédio: coleta individual concluída ou não (coluna «Status do Remédio» no export).",
    )


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
    quantidade_total: int = Field(ge=0, description="Unidades previstas (meta) da OS.")
    quantidade_separada: int = Field(ge=0, description="Unidades separadas ao encerrar.")
    tempo_medio_por_remedio: str = Field(
        default="",
        description="Tempo médio por unidade, texto tipo «X min Y s», ou vazio.",
    )
    unidades_totais: int = Field(
        ge=0,
        description="Compat.: igual a quantidade_separada (unidades ao encerrar).",
    )
    situacao: Literal["concluida", "cancelada"]
    erro_descricao: str = Field(default="", description="Preenchido se a OS foi cancelada e houver registro.")
    erro_codigo: str = Field(default="", description="Preenchido se a OS foi cancelada e houver registro.")
    medicine_lines: list[MedicineReportLine] = Field(
        default_factory=list,
        description="Itens da OS para exportação (ordem de coleta).",
    )
    numero_pausas: int = Field(default=0, ge=0)
    separador_codigo: str = Field(default="", description="Código do separador no cadastro.")
    robot_id: int | None = Field(
        default=None,
        description="ID do robô que concluiu ou cancelou a OS (snapshot na conclusão/cancelamento).",
    )
    porcentagem_conclusao: str = Field(
        default="",
        description="Percentual separado/previsto, formato pt-BR (ex.: 87,5%).",
    )
    tempo_total_separacao: str = Field(
        default="",
        description="Duração total atribuição → encerramento, texto tipo «X min Y s».",
    )
    tempo_liquido_separacao: str = Field(
        default="",
        description="Tempo efetivo de execução (total menos pausas), «X min Y s»; vazio se indisponível.",
    )


class OrdersReportResponse(BaseModel):
    total: int = Field(ge=0, description="Total de linhas que batem o filtro (não só esta página).")
    items: list[OrderReportItem] = Field(default_factory=list)


class ExportBatchRequest(BaseModel):
    """Corpo do export em lote (POST): filtros iguais ao relatório; `order_ids` opcional restringe as ordens."""

    format: Literal["csv", "xlsx", "pdf"]
    de: date | None = None
    ate: date | None = None
    os: str | None = Field(None, max_length=64)
    nome: str | None = Field(None, max_length=128)
    cliente: str | None = Field(None, max_length=256)
    nome_separador: str | None = Field(None, max_length=128)
    codigo_separador: str | None = Field(None, max_length=32)
    situacao: str | None = None
    order_ids: list[int] | None = Field(
        None,
        description="Se preenchido, exporta só estes IDs (intersecção com o filtro). Omitir para todas as ordens do filtro.",
    )
