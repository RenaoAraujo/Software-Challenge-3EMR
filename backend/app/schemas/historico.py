from datetime import date

from pydantic import BaseModel, Field


class HistoricoDiaOsConcluidas(BaseModel):
    """Quantidade de OS concluídas em um dia civil (America/Sao_Paulo), sem acumular."""

    data: date
    ordens: int = Field(ge=0, description="Número de OS concluídas neste dia.")


class HistoricoDiaTempoMedioOs(BaseModel):
    """Média do tempo (minutos) entre envio ao separador e conclusão, por dia civil (Brasil)."""

    data: date
    minutos_medio: float | None = Field(
        default=None,
        description=(
            "Média em minutos das OS concluídas neste dia com assigned_at e completed_at válidos; "
            "null se não houver OS com duração neste dia."
        ),
    )


class HistoricoDiaRemedios(BaseModel):
    """Um dia do período (calendário America/Sao_Paulo) com total de remédios naquele dia, sem acumular dias anteriores."""

    data: date
    remedios: int = Field(
        ge=0,
        description="Soma do número de itens de medicamento nas OS concluídas neste dia.",
    )


class RobotHistoricoStats(BaseModel):
    robot_id: int
    robot_nome: str
    de: date = Field(description="Início do período (inclusivo).")
    ate: date = Field(description="Fim do período (inclusivo).")
    ordens_concluidas: int = Field(description="Quantidade de OS concluídas no período.")
    unidades_empacotadas: int = Field(description="Soma das unidades registradas ao concluir cada OS.")
    unidades_previstas_total: int = Field(description="Soma das unidades previstas das OS concluídas.")
    linhas_medicamento_total: int = Field(
        description="Soma do número de itens (linhas) de medicamento nas OS concluídas."
    )
    tempo_medio_minutos: float | None = Field(
        default=None,
        description="Média do tempo entre envio ao separador e conclusão, em minutos.",
    )
    tempo_medio_por_medicamento_segundos: float | None = Field(
        default=None,
        description=(
            "Média de segundos por unidade separada no período: soma dos tempos das OS "
            "com unidades concluídas dividida pela soma dessas unidades."
        ),
    )
    taxa_unidades_percent: float | None = Field(
        default=None,
        description="100 × empacotadas / previstas quando há previstas > 0.",
    )
    ordens_canceladas: int = Field(
        default=0,
        description="OS canceladas neste separador no período (data de cancelamento).",
    )
    ordens_com_pausa: int = Field(
        default=0,
        description=(
            "OS concluídas ou canceladas no período que tiveram ao menos uma pausa registrada nesta execução."
        ),
    )
    remedios_por_dia: list[HistoricoDiaRemedios] = Field(
        default_factory=list,
        description=(
            "Para cada dia entre de e ate (inclusivo), soma das linhas de medicamento por dia civil "
            "(data/hora de conclusão convertida para America/Sao_Paulo). Valores são totais do dia, não acumulados."
        ),
    )
    os_concluidas_por_dia: list[HistoricoDiaOsConcluidas] = Field(
        default_factory=list,
        description=(
            "Para cada dia entre de e ate (inclusivo), quantidade de OS concluídas por dia civil "
            "(America/Sao_Paulo). Um ponto por dia, não cumulativo."
        ),
    )
    tempo_medio_os_por_dia: list[HistoricoDiaTempoMedioOs] = Field(
        default_factory=list,
        description=(
            "Para cada dia entre de e ate (inclusivo), tempo médio (minutos) envio→conclusão das OS "
            "concluídas naquele dia civil (America/Sao_Paulo); null nos dias sem OS com duração válida."
        ),
    )
