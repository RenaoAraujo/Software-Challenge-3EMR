from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.repositories.service_order_repository import ServiceOrderRepository
from app.schemas.service_order import ServiceOrderOut

router = APIRouter(prefix="/service-orders")


@router.get("", response_model=list[ServiceOrderOut])
def list_assignable_orders(db: Session = Depends(get_database)) -> list[ServiceOrderOut]:
    repo = ServiceOrderRepository(db)
    orders = repo.list_assignable()
    return [ServiceOrderOut.model_validate(o) for o in orders]
