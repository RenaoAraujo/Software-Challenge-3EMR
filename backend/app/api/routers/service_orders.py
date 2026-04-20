from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.audit_session import audit_session_action
from app.api.dependencies import get_current_user, get_database, limit_sensitive, require_csrf_token
from app.models.entities import User
from app.repositories.service_order_repository import ServiceOrderRepository
from app.schemas.service_order import (
    ExportBatchRequest,
    ManualOrderCreate,
    OrderReportItem,
    OrdersReportResponse,
    ServiceOrderOut,
)
from app.services.historico_service import _utc_day_range
from app.services.assignment_service import (
    AssignmentError,
    AssignmentService,
    CancelledOsReuseRequired,
)
from app.services.order_report_export_service import (
    export_batch_order_reports_bytes,
    export_order_report_bytes,
    order_to_report_item,
)
from app.services.robot_service import RobotService
from app.services.service_order_service import ServiceOrderService

router = APIRouter(prefix="/service-orders")

# Tamanho interno por consulta ao exportar lote (sem limite no número total de ordens).
_EXPORT_BATCH_PAGE_SIZE = 1000


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
    limit: int = Query(100, ge=1, le=2000, description="Máximo de linhas nesta página."),
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
    preview: bool = Query(
        False,
        description="Se true, não regista auditoria (pré-visualização no modal de lote).",
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

    items: list[OrderReportItem] = []
    for o in orders:
        it = order_to_report_item(db, o)
        if it is not None:
            items.append(it)

    filt = "período completo" if de is None else f"de {de.isoformat()} a {ate.isoformat()}"
    if not preview:
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


@router.post("/export-batch")
def export_batch_order_reports(
    request: Request,
    payload: ExportBatchRequest,
    db: Session = Depends(get_database),
    user: User = Depends(get_current_user),
    _: None = Depends(require_csrf_token),
) -> Response:
    """Exporta várias OS filtradas num único CSV ou Excel (POST para suportar muitos `order_ids`)."""
    situacao = payload.situacao
    de = payload.de
    ate = payload.ate
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

    restrict_export_ids: list[int] | None = None
    if payload.order_ids is not None:
        if len(payload.order_ids) == 0:
            raise HTTPException(
                status_code=400,
                detail="Informe pelo menos um id em order_ids ou omita o campo para exportar todas as ordens do filtro.",
            )
        restrict_export_ids = list(dict.fromkeys(payload.order_ids))

    # Lista explícita de IDs: não aplicar filtros de período nem de texto — a seleção pode
    # juntar ordens de várias pesquisas (ex.: clientes diferentes) no mesmo modal.
    id_only = restrict_export_ids is not None
    q_start = None if id_only else start_utc
    q_end = None if id_only else end_excl
    q_situacao = None if id_only else situacao
    q_os = None if id_only else payload.os
    q_nome = None if id_only else payload.nome
    q_cliente = None if id_only else payload.cliente
    q_nsep = None if id_only else payload.nome_separador
    q_csep = None if id_only else payload.codigo_separador

    repo = ServiceOrderRepository(db)
    items: list[OrderReportItem] = []
    total = 0
    offset = 0
    while True:
        orders, total = repo.list_ended_orders_report(
            start_utc=q_start,
            end_utc_exclusive=q_end,
            limit=_EXPORT_BATCH_PAGE_SIZE,
            offset=offset,
            situacao=q_situacao,
            os_contains=q_os,
            nome_cliente_contains=q_nome,
            cliente_contains=q_cliente,
            nome_separador_contains=q_nsep,
            codigo_separador_contains=q_csep,
            restrict_ids=restrict_export_ids,
        )
        for o in orders:
            it = order_to_report_item(db, o)
            if it is not None:
                items.append(it)
        if not orders or len(orders) < _EXPORT_BATCH_PAGE_SIZE:
            break
        offset += _EXPORT_BATCH_PAGE_SIZE

    if not items:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma ordem encerrada encontrada para estes filtros. Ajuste os critérios e tente de novo.",
        )

    data_exportacao = datetime.now(ZoneInfo("America/Sao_Paulo")).date().strftime("%d/%m/%Y")
    stamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S")
    filename_base = f"relatorio_lote_{stamp}"
    file_bytes, media_type, filename = export_batch_order_reports_bytes(
        items,
        payload.format,
        exportado_por=user.username,
        data_exportacao=data_exportacao,
        filename_base=filename_base,
    )
    audit_session_action(
        request,
        db,
        action="export_relatorio_os",
        description=(
            f"Exportou lote de relatórios ({payload.format.upper()}): {len(items)} ordem(ns); "
            f"total no filtro: {total}. Ficheiro: {filename}."
        ),
    )
    safe_fn = filename.encode("ascii", "ignore").decode("ascii") or f"lote.{payload.format}"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_fn}"'},
    )


@router.get("/{order_id}/export")
def export_single_order_report(
    request: Request,
    order_id: int,
    fmt: Literal["csv", "xlsx", "pdf"] = Query(
        ...,
        alias="format",
        description="Formato: csv, xlsx (Excel) ou pdf.",
    ),
    db: Session = Depends(get_database),
    user: User = Depends(get_current_user),
) -> Response:
    """Gera arquivo com os dados de uma OS encerrada (relatório por OS)."""
    repo = ServiceOrderRepository(db)
    order = repo.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")
    item = order_to_report_item(db, order)
    if item is None:
        raise HTTPException(
            status_code=400,
            detail="Só é possível exportar ordens concluídas ou canceladas com data registrada.",
        )
    data_exportacao = datetime.now(ZoneInfo("America/Sao_Paulo")).date().strftime("%d/%m/%Y")
    body, media_type, filename = export_order_report_bytes(
        item,
        fmt,
        exportado_por=user.username,
        data_exportacao=data_exportacao,
    )
    audit_session_action(
        request,
        db,
        action="export_relatorio_os",
        description=f'Exportou relatório da OS "{item.os_code}" em {fmt.upper()}.',
    )
    safe_fn = filename.encode("ascii", "ignore").decode("ascii") or f"relatorio.{fmt}"
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_fn}"'},
    )


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
            body.reopen_cancelled,
        )
    except CancelledOsReuseRequired as e:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "cancelled_os_reuse_required",
                "message": (
                    "Já existe uma OS cancelada com este número. "
                    "Escolha se o separador continua de onde parou ou refaz o pedido inteiro."
                ),
                "cancelled_separated_units": e.cancelled_separated_units,
                "expected_units": e.expected_units,
            },
        ) from e
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
