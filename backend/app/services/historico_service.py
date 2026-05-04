from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.entities import OrderEventType, ServiceOrder
from app.repositories.order_event_repository import COMPLETION_EVENT_TYPES, OrderEventRepository
from app.repositories.robot_repository import RobotRepository
from app.repositories.service_order_repository import ServiceOrderRepository
from app.schemas.historico import (
    HistoricoClasseMedicamento,
    HistoricoDiaOsConcluidas,
    HistoricoDiaRemedios,
    HistoricoDiaTempoMedioOs,
    RobotHistoricoStats,
)
from app.services.medicine_classification import classify_medicine

# Calendário “por dia” do gráfico alinhado ao horário de Brasília (evita somar 17+18 no mesmo dia UTC).
_BR_TZ = ZoneInfo("America/Sao_Paulo")


def _data_conclusao_calendario_br(completed_at: datetime) -> date:
    ca = completed_at
    if ca.tzinfo is None:
        ca = ca.replace(tzinfo=UTC)
    return ca.astimezone(_BR_TZ).date()


def _utc_day_range(de: date, ate: date) -> tuple[datetime, datetime]:
    start = datetime(de.year, de.month, de.day, tzinfo=UTC)
    end_exclusive = datetime(ate.year, ate.month, ate.day, tzinfo=UTC) + timedelta(days=1)
    return start, end_exclusive


def _remedios_agregados_por_dia(de: date, ate: date, orders: list[ServiceOrder]) -> list[HistoricoDiaRemedios]:
    """Soma por dia civil (America/São Paulo) das linhas de medicamento nas OS concluídas — totais independentes por dia, não cumulativos."""
    by_day: dict[date, int] = defaultdict(int)
    for o in orders:
        if not o.completed_at:
            continue
        dia = _data_conclusao_calendario_br(o.completed_at)
        by_day[dia] += len(o.medicines)
    out: list[HistoricoDiaRemedios] = []
    cur = de
    while cur <= ate:
        out.append(HistoricoDiaRemedios(data=cur, remedios=by_day.get(cur, 0)))
        cur += timedelta(days=1)
    return out


def _os_concluidas_por_dia(de: date, ate: date, orders: list[ServiceOrder]) -> list[HistoricoDiaOsConcluidas]:
    """Contagem por dia civil (America/São Paulo) de OS concluídas — uma OS conta no dia de `completed_at` (BR)."""
    by_day: dict[date, int] = defaultdict(int)
    for o in orders:
        if not o.completed_at:
            continue
        dia = _data_conclusao_calendario_br(o.completed_at)
        by_day[dia] += 1
    out: list[HistoricoDiaOsConcluidas] = []
    cur = de
    while cur <= ate:
        out.append(HistoricoDiaOsConcluidas(data=cur, ordens=by_day.get(cur, 0)))
        cur += timedelta(days=1)
    return out


def _medicamentos_por_classe(orders: list[ServiceOrder]) -> list[HistoricoClasseMedicamento]:
    """Classifica todas as linhas de medicamento do período e devolve contagem + percentual por classe (desc)."""
    counts: dict[str, int] = defaultdict(int)
    for o in orders:
        for med in o.medicines:
            counts[classify_medicine(med)] += 1
    total = sum(counts.values())
    if total == 0:
        return []
    # Ordena do maior para o menor; em empate, ordem alfabética da classe (estável para UI).
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [
        HistoricoClasseMedicamento(
            classe=classe,
            quantidade=qtd,
            percentual=round(100.0 * qtd / total, 1),
        )
        for classe, qtd in items
    ]


def _tempo_medio_os_por_dia(de: date, ate: date, orders: list[ServiceOrder]) -> list[HistoricoDiaTempoMedioOs]:
    """Média (minutos) do intervalo assigned_at → completed_at por dia civil de conclusão (Brasil)."""
    by_day: dict[date, list[float]] = defaultdict(list)
    for o in orders:
        if not o.completed_at or not o.assigned_at:
            continue
        dia = _data_conclusao_calendario_br(o.completed_at)
        a = o.assigned_at
        c = o.completed_at
        if a.tzinfo is None:
            a = a.replace(tzinfo=UTC)
        if c.tzinfo is None:
            c = c.replace(tzinfo=UTC)
        delta_min = (c - a).total_seconds() / 60.0
        if delta_min >= 0:
            by_day[dia].append(delta_min)
    out: list[HistoricoDiaTempoMedioOs] = []
    cur = de
    while cur <= ate:
        mins = by_day.get(cur)
        if mins:
            out.append(HistoricoDiaTempoMedioOs(data=cur, minutos_medio=round(sum(mins) / len(mins), 1)))
        else:
            out.append(HistoricoDiaTempoMedioOs(data=cur, minutos_medio=None))
        cur += timedelta(days=1)
    return out


class HistoricoService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._robots = RobotRepository(db)
        self._orders = ServiceOrderRepository(db)
        self._events = OrderEventRepository(db)

    def stats_robot_period(self, robot_id: int, de: date, ate: date) -> RobotHistoricoStats | None:
        robot = self._robots.get_by_id(robot_id)
        if robot is None:
            return None
        if de > ate:
            raise ValueError("A data inicial não pode ser posterior à data final.")

        start, end_excl = _utc_day_range(de, ate)
        orders = self._orders.list_completed_by_robot_between(robot_id, start, end_excl)
        # Contagens vêm dos OrderEvent (imutáveis): preservam cancelamentos de OS
        # que depois foram reabertas e concluídas — cada evento conta para sempre.
        ordens_canceladas = self._events.count_cancelled_between(start, end_excl, robot_id=robot_id)
        pausas_concluidas = self._events.sum_pause_count_between(
            event_types=COMPLETION_EVENT_TYPES, start_utc=start, end_utc_exclusive=end_excl, robot_id=robot_id,
        )
        pausas_canceladas = self._events.sum_pause_count_between(
            event_types=(OrderEventType.CANCELLED.value,),
            start_utc=start, end_utc_exclusive=end_excl, robot_id=robot_id,
        )
        ordens_com_pausa = self._orders.count_ended_with_pause_by_robot_between(robot_id, start, end_excl)
        return self._aggregate(
            robot.name,
            robot_id,
            de,
            ate,
            orders,
            ordens_canceladas=ordens_canceladas,
            ordens_com_pausa=ordens_com_pausa,
            pausas_concluidas=pausas_concluidas,
            pausas_canceladas=pausas_canceladas,
        )

    def stats_all_robots_period(self, de: date, ate: date) -> RobotHistoricoStats:
        """Estatísticas do período somando OS de todos os separadores."""
        if de > ate:
            raise ValueError("A data inicial não pode ser posterior à data final.")

        start, end_excl = _utc_day_range(de, ate)
        orders = self._orders.list_completed_between(start, end_excl)
        ordens_canceladas = self._events.count_cancelled_between(start, end_excl)
        pausas_concluidas = self._events.sum_pause_count_between(
            event_types=COMPLETION_EVENT_TYPES, start_utc=start, end_utc_exclusive=end_excl,
        )
        pausas_canceladas = self._events.sum_pause_count_between(
            event_types=(OrderEventType.CANCELLED.value,),
            start_utc=start, end_utc_exclusive=end_excl,
        )
        ordens_com_pausa = self._orders.count_ended_with_pause_between(start, end_excl)
        return self._aggregate(
            "Todos os separadores",
            None,
            de,
            ate,
            orders,
            ordens_canceladas=ordens_canceladas,
            ordens_com_pausa=ordens_com_pausa,
            pausas_concluidas=pausas_concluidas,
            pausas_canceladas=pausas_canceladas,
        )

    @staticmethod
    def _aggregate(
        robot_nome: str,
        robot_id: int | None,
        de: date,
        ate: date,
        orders: list[ServiceOrder],
        *,
        ordens_canceladas: int = 0,
        ordens_com_pausa: int = 0,
        pausas_concluidas: int = 0,
        pausas_canceladas: int = 0,
    ) -> RobotHistoricoStats:
        ordens_concluidas = len(orders)
        unidades_empacotadas = sum(int(o.completed_units or 0) for o in orders)
        unidades_previstas = sum(int(o.expected_units) for o in orders)
        linhas_med = sum(len(o.medicines) for o in orders)

        durations_min: list[float] = []
        total_sec_com_units = 0.0
        total_units_completed = 0
        for o in orders:
            if o.assigned_at and o.completed_at:
                a = o.assigned_at
                c = o.completed_at
                if a.tzinfo is None:
                    a = a.replace(tzinfo=UTC)
                if c.tzinfo is None:
                    c = c.replace(tzinfo=UTC)
                delta_sec = (c - a).total_seconds()
                delta_min = delta_sec / 60.0
                if delta_min >= 0:
                    durations_min.append(delta_min)
                    cu = int(o.completed_units or 0)
                    if cu > 0:
                        total_sec_com_units += delta_sec
                        total_units_completed += cu

        tempo_medio = None
        if durations_min:
            tempo_medio = round(sum(durations_min) / len(durations_min), 1)

        tempo_medio_por_medicamento_segundos = None
        if total_units_completed > 0:
            tempo_medio_por_medicamento_segundos = round(
                total_sec_com_units / total_units_completed,
                1,
            )

        taxa = None
        if unidades_previstas > 0:
            taxa = round(100.0 * unidades_empacotadas / unidades_previstas, 1)

        remedios_por_dia = _remedios_agregados_por_dia(de, ate, orders)
        os_concluidas_por_dia = _os_concluidas_por_dia(de, ate, orders)
        tempo_medio_os_por_dia = _tempo_medio_os_por_dia(de, ate, orders)
        medicamentos_por_classe = _medicamentos_por_classe(orders)

        return RobotHistoricoStats(
            robot_id=robot_id,
            robot_nome=robot_nome,
            de=de,
            ate=ate,
            ordens_concluidas=ordens_concluidas,
            unidades_empacotadas=unidades_empacotadas,
            unidades_previstas_total=unidades_previstas,
            linhas_medicamento_total=linhas_med,
            tempo_medio_minutos=tempo_medio,
            tempo_medio_por_medicamento_segundos=tempo_medio_por_medicamento_segundos,
            taxa_unidades_percent=taxa,
            ordens_canceladas=ordens_canceladas,
            ordens_com_pausa=ordens_com_pausa,
            pausas_concluidas=pausas_concluidas,
            pausas_canceladas=pausas_canceladas,
            remedios_por_dia=remedios_por_dia,
            os_concluidas_por_dia=os_concluidas_por_dia,
            tempo_medio_os_por_dia=tempo_medio_os_por_dia,
            medicamentos_por_classe=medicamentos_por_classe,
        )
