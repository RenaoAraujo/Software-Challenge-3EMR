from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.audit_session import audit_session_action
from app.api.dependencies import get_database, limit_sensitive, require_csrf_token
from app.schemas.assignment import AssignOrderBody
from app.schemas.historico import RobotHistoricoStats
from app.schemas.progress import UnitsProgressBody
from app.schemas.robot import RobotCreateBody, RobotDetail, RobotSummary, RobotUpdateBody
from app.services.assignment_service import AssignmentError, AssignmentService
from app.services.historico_service import HistoricoService
from app.services.robot_service import RobotService

router = APIRouter(prefix="/robots")


@router.get("", response_model=list[RobotSummary])
def list_robots(
    name: str | None = Query(
        None,
        max_length=128,
        description="Filtra separadores cujo nome contém o texto (sem distinguir maiúsculas/minúsculas).",
    ),
    db: Session = Depends(get_database),
) -> list[RobotSummary]:
    return RobotService(db).list_robots(name_contains=name)


@router.post("", response_model=RobotDetail, status_code=201)
def create_robot(
    body: RobotCreateBody,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    try:
        return RobotService(db).create_robot(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{robot_id}/historico", response_model=RobotHistoricoStats)
def get_robot_historico(
    request: Request,
    robot_id: int,
    de: date = Query(..., description="Início do período (AAAA-MM-DD)."),
    ate: date = Query(..., description="Fim do período (AAAA-MM-DD)."),
    db: Session = Depends(get_database),
) -> RobotHistoricoStats:
    try:
        stats = HistoricoService(db).stats_robot_period(robot_id, de, ate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if stats is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    audit_session_action(
        request,
        db,
        action="view_historico",
        description=(
            f'Consultou histórico do separador "{stats.robot_nome}" (id {robot_id}) '
            f"no período de {de.isoformat()} a {ate.isoformat()}."
        ),
    )
    return stats


@router.post("/{robot_id}/concluir-os", response_model=RobotDetail)
def concluir_ordem_atual(
    request: Request,
    robot_id: int,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    svc = RobotService(db)
    before = svc.get_robot(robot_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    os_code = before.current_order.os_code if before.current_order else None
    try:
        detail = svc.complete_current_order(robot_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    if os_code:
        audit_session_action(
            request,
            db,
            action="os_completed",
            description=f"Separador {before.name} — OS {os_code} concluída manualmente.",
        )
    return detail


@router.post("/{robot_id}/cancelar-os", response_model=RobotDetail)
def cancelar_ordem_atual(
    request: Request,
    robot_id: int,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    svc = RobotService(db)
    before = svc.get_robot(robot_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    os_code = before.current_order.os_code if before.current_order else None
    try:
        detail = svc.cancel_current_order(robot_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    if os_code:
        audit_session_action(
            request,
            db,
            action="os_cancelled",
            description=f"Separador {before.name} — OS {os_code} cancelada.",
        )
    return detail


@router.post("/{robot_id}/pausar", response_model=RobotDetail)
def pausar_separacao(
    request: Request,
    robot_id: int,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    svc = RobotService(db)
    before = svc.get_robot(robot_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    os_code = before.current_order.os_code if before.current_order else None
    try:
        detail = svc.pause_separation(robot_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    if os_code:
        audit_session_action(
            request,
            db,
            action="os_paused",
            description=f"Separador {before.name} — pausa na OS {os_code}.",
        )
    return detail


@router.post("/{robot_id}/retomar", response_model=RobotDetail)
def retomar_separacao(
    request: Request,
    robot_id: int,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    svc = RobotService(db)
    before = svc.get_robot(robot_id)
    if before is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    os_code = before.current_order.os_code if before.current_order else None
    try:
        detail = svc.resume_separation(robot_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Separador não encontrado.")
    if os_code:
        audit_session_action(
            request,
            db,
            action="os_resumed",
            description=f"Separador {before.name} — retomada da OS {os_code}.",
        )
    return detail


@router.get("/{robot_id}", response_model=RobotDetail)
def get_robot(robot_id: int, db: Session = Depends(get_database)) -> RobotDetail:
    detail = RobotService(db).get_robot(robot_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Robô não encontrado.")
    return detail


@router.delete("/{robot_id}", status_code=204)
def delete_robot(
    robot_id: int,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> None:
    if not RobotService(db).delete_robot(robot_id):
        raise HTTPException(status_code=404, detail="Robô não encontrado.")


@router.patch("/{robot_id}", response_model=RobotDetail)
def update_robot(
    robot_id: int,
    body: RobotUpdateBody,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    try:
        detail = RobotService(db).update_robot(robot_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Robô não encontrado.")
    return detail


@router.post("/{robot_id}/assign-order", status_code=204)
def assign_order(
    request: Request,
    robot_id: int,
    body: AssignOrderBody,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> None:
    try:
        AssignmentService(db).assign_order_to_robot(robot_id, body.service_order_id)
    except AssignmentError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    detail = RobotService(db).get_robot(robot_id)
    if detail and detail.current_order:
        audit_session_action(
            request,
            db,
            action="os_started",
            description=f"Separador {detail.name} — início da OS {detail.current_order.os_code}.",
        )


@router.patch("/{robot_id}/units", response_model=RobotDetail)
def update_units(
    request: Request,
    robot_id: int,
    body: UnitsProgressBody,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    try:
        detail, completed_os = RobotService(db).update_units_separated(
            robot_id, body.units_separated
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Robô não encontrado.")
    if completed_os:
        audit_session_action(
            request,
            db,
            action="os_completed_auto",
            description=(
                f"Separador {detail.name} — OS {completed_os} concluída automaticamente "
                "ao atingir a meta de unidades."
            ),
        )
    return detail
