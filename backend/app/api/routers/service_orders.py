from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.audit_session import audit_session_action
from app.api.dependencies import get_database, limit_sensitive, require_csrf_token
from app.models.entities import ServiceOrderStatus
from app.repositories.robot_repository import RobotRepository
from app.repositories.service_order_repository import ServiceOrderRepository
from app.schemas.service_order import (
    ManualOrderCreate,
    OrderReportItem,
    OrdersReportResponse,
    ServiceOrderOut,
)
from app.services.historico_service import _data_conclusao_calendario_br, _utc_day_range
from app.services.assignment_service import AssignmentError, AssignmentService
from app.services.robot_service import RobotService
from app.services.service_order_service import ServiceOrderService

router = APIRouter(prefix="/service-orders")


@router.get("", response_model=list[ServiceOrderOut])
def list_assignable_orders(db: Session = Depends(get_database)) -> list[ServiceOrderOut]:
    repo = ServiceOrderRepository(db)
    orders = repo.list_assignable()
    return [ServiceOrderOut.model_validate(o) for o in orders]


@router.get("/completed", response_model=OrdersReportResponse)
def list_service_orders_report(
    request: Request,
    de: date | None = Query(
        None,
        description="Início do período (AAAA-MM-DD). Omitir junto com `ate` para todas as OS encerradas.",
    ),
    ate: date | None = Query(
        None,
        description="Fim do período (AAAA-MM-DD). Omitir junto com `de` para todas as OS encerradas.",
    ),
    limit: int = Query(100, ge=1, le=500, description="Máximo de linhas nesta página."),
    offset: int = Query(0, ge=0),
    filtro_os: str | None = Query(None, max_length=64, alias="os", description="Filtra código da OS (contém)."),
    nome: str | None = Query(None, max_length=128, description="Filtra parte do nome do cliente (contém)."),
    cliente: str | None = Query(None, max_length=256, description="Filtra outra parte do nome do cliente (contém)."),
    nome_separador: str | None = Query(
        None,
        max_length=128,
        description="Filtra nome do separador (snapshot ou cadastro, contém).",
    ),
    codigo_separador: str | None = Query(
        None,
        max_length=32,
        description="Filtra código do separador (contém).",
    ),
    situacao: str | None = Query(
        None,
        description="concluida, cancelada ou omitir para ambas.",
    ),
    db: Session = Depends(get_database),
) -> OrdersReportResponse:
    if situacao is not None and situacao not in ("concluida", "cancelada"):
        raise HTTPException(
            status_code=400,
            detail="Situação inválida. Use concluida, cancelada ou deixe em branco.",
        )
    if (de is None) != (ate is None):
        raise HTTPException(
            status_code=400,
            detail="Informe a data inicial e a final juntas, ou deixe ambas em branco.",
        )
    if de is not None and ate is not None and de > ate:
        raise HTTPException(status_code=400, detail="A data inicial não pode ser posterior à data final.")

    start_utc = None
    end_excl = None
    if de is not None and ate is not None:
        start_utc, end_excl = _utc_day_range(de, ate)

    repo = ServiceOrderRepository(db)
    robots = RobotRepository(db)
    orders, total = repo.list_ended_orders_report(
        start_utc=start_utc,
        end_utc_exclusive=end_excl,
        limit=limit,
        offset=offset,
        situacao=situacao,
        os_contains=filtro_os,
        nome_cliente_contains=nome,
        cliente_contains=cliente,
        nome_separador_contains=nome_separador,
        codigo_separador_contains=codigo_separador,
    )
    rids: set[int] = set()
    for o in orders:
        if o.completed_by_robot_id is not None:
            rids.add(o.completed_by_robot_id)
        if o.cancelled_by_robot_id is not None:
            rids.add(o.cancelled_by_robot_id)
    names = robots.get_names_by_ids(rids)

    items: list[OrderReportItem] = []
    for o in orders:
        if o.status == ServiceOrderStatus.COMPLETED.value:
            ca = o.completed_at
            if ca is None:
                continue
            d = _data_conclusao_calendario_br(ca)
            rid = o.completed_by_robot_id
            snap = (o.completed_by_robot_name or "").strip()
            sep_nome = snap or (names.get(rid) if rid is not None else None) or None
            unidades = (
                int(o.completed_units) if o.completed_units is not None else int(o.expected_units or 0)
            )
            situacao = "concluida"
        elif o.status == ServiceOrderStatus.CANCELLED.value:
            canc = o.cancelled_at
            if canc is None:
                continue
            d = _data_conclusao_calendario_br(canc)
            rid = o.cancelled_by_robot_id
            snap = (o.cancelled_by_robot_name or "").strip()
            sep_nome = snap or (names.get(rid) if rid is not None else None) or None
            unidades = int(o.expected_units or 0)
            situacao = "cancelada"
        else:
            continue

        items.append(
            OrderReportItem(
                id=o.id,
                os_code=o.os_code,
                client_name=o.client_name or "",
                data=d,
                separador_nome=sep_nome,
                unidades_totais=max(0, unidades),
                situacao=situacao,
            )
        )

    filt = "período completo" if de is None else f"de {de.isoformat()} a {ate.isoformat()}"
    audit_session_action(
        request,
        db,
        action="view_relatorio_os",
        description=(
            f'Consultou relatório por OS ({filt}). Linhas nesta página: {len(items)}; '
            f"total no filtro: {total}."
        ),
    )
    return OrdersReportResponse(total=total, items=items)


@router.post("/manual", response_model=ServiceOrderOut, status_code=201)
def create_manual_service_order(
    request: Request,
    body: ManualOrderCreate,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> ServiceOrderOut:
    try:
        order = AssignmentService(db).create_manual_order_and_assign(
            body.robot_id,
            body.os_code,
            body.client_name,
            body.quantidade_remedios,
        )
    except AssignmentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    detail = RobotService(db).get_robot(body.robot_id)
    if detail and detail.current_order:
        audit_session_action(
            request,
            db,
            action="os_started",
            description=(
                f"Separador {detail.name} — início da OS {order.os_code} "
                "(OS manual de teste)."
            ),
        )
    return ServiceOrderOut.model_validate(order)


@router.delete("/{order_id}", status_code=204)
def delete_service_order(
    order_id: int,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> None:
    if not ServiceOrderService(db).delete_order(order_id):
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")
