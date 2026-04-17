from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database, limit_sensitive, require_csrf_token
from app.schemas.assignment import AssignOrderBody
from app.schemas.progress import UnitsProgressBody
from app.schemas.robot import RobotCreateBody, RobotDetail, RobotSummary, RobotUpdateBody
from app.services.assignment_service import AssignmentError, AssignmentService
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


@router.patch("/{robot_id}/units", response_model=RobotDetail)
def update_units(
    robot_id: int,
    body: UnitsProgressBody,
    db: Session = Depends(get_database),
    _: None = Depends(require_csrf_token),
    __: None = Depends(limit_sensitive),
) -> RobotDetail:
    try:
        detail = RobotService(db).update_units_separated(robot_id, body.units_separated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail="Robô não encontrado.")
    return detail
