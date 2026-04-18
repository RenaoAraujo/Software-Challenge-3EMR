from datetime import date

from pydantic import BaseModel, Field


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
