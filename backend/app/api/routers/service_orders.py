from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.audit_session import audit_session_action
from app.api.dependencies import get_database, limit_sensitive, require_csrf_token
from app.repositories.service_order_repository import ServiceOrderRepository
from app.schemas.service_order import ManualOrderCreate, ServiceOrderOut
from app.services.assignment_service import AssignmentError, AssignmentService
from app.services.robot_service import RobotService
from app.services.service_order_service import ServiceOrderService

router = APIRouter(prefix="/service-orders")


@router.get("", response_model=list[ServiceOrderOut])
def list_assignable_orders(db: Session = Depends(get_database)) -> list[ServiceOrderOut]:
    repo = ServiceOrderRepository(db)
    orders = repo.list_assignable()
    return [ServiceOrderOut.model_validate(o) for o in orders]


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
