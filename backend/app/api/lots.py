from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.wafer_lot import WaferLot


router = APIRouter()


class WaferLotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lot_id: str
    wafer_count: int
    route_id: str | None
    status: str
    current_step_index: int
    created_at: datetime


@router.get("/lots", response_model=list[WaferLotResponse], tags=["MES Lots"])
def list_lots(db: Session = Depends(get_db)):
    statement = select(WaferLot).order_by(WaferLot.lot_id)

    lots = db.scalars(statement).all()

    return lots