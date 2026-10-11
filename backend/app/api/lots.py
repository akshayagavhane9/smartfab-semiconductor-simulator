from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.wafer_lot import WaferLot
from app.models.process_route import ProcessRoute


router = APIRouter()

class WaferLotCreate(BaseModel):
    lot_id: str = Field(min_length=1, max_length=30)
    wafer_count: int = Field(gt=0)
    route_id: str = Field(min_length=1, max_length=30)

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

@router.post(
    "/lots",
    response_model=WaferLotResponse,
    status_code=201,
    tags=["MES Lots"],
)
def create_lot(lot_data: WaferLotCreate, db: Session = Depends(get_db)):

    # Check whether the lot ID already exists
    existing_lot = db.get(WaferLot, lot_data.lot_id)

    if existing_lot is not None:
        raise HTTPException(
            status_code=409,
            detail="Lot ID already exists",
        )

    # Check whether the manufacturing route exists
    route = db.get(ProcessRoute, lot_data.route_id)

    if route is None:
        raise HTTPException(
            status_code=422,
            detail="Manufacturing route does not exist",
        )

    # Create the new manufacturing lot
    new_lot = WaferLot(
        lot_id=lot_data.lot_id,
        wafer_count=lot_data.wafer_count,
        route_id=lot_data.route_id,
        status="CREATED",
        current_step_index=0,
    )

    db.add(new_lot)
    db.commit()
    db.refresh(new_lot)

    return new_lot