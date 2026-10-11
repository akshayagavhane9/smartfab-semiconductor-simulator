from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.wafer_lot import WaferLot
from app.models.process_route import ProcessRoute
from app.models.process_step import ProcessStep


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

class NextStepResponse(BaseModel):
    lot_id: str
    route_id: str
    step_order: int
    step_name: str

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

@router.get(
    "/lots/{lot_id}",
    response_model=WaferLotResponse,
    tags=["MES Lots"],
)
def get_lot(lot_id: str, db: Session = Depends(get_db)):

    # Retrieve a wafer lot using its primary key
    lot = db.get(WaferLot, lot_id)

    # Return 404 if the lot does not exist
    if lot is None:
        raise HTTPException(
            status_code=404,
            detail="Lot not found",
        )

    return lot

@router.get(
    "/lots/{lot_id}/next-step",
    response_model=NextStepResponse,
    tags=["MES Lots"],
)
def get_next_step(lot_id: str, db: Session = Depends(get_db)):

    # Find the requested wafer lot
    lot = db.get(WaferLot, lot_id)

    if lot is None:
        raise HTTPException(
            status_code=404,
            detail="Lot not found",
        )

    # A lot must have a route to determine its next step
    if lot.route_id is None:
        raise HTTPException(
            status_code=409,
            detail="Lot has no manufacturing route",
        )

    # Find the step matching the lot's current position
    statement = select(ProcessStep).where(
        ProcessStep.route_id == lot.route_id,
        ProcessStep.step_order == lot.current_step_index,
    )

    step = db.scalar(statement)

    if step is None:
        raise HTTPException(
            status_code=404,
            detail="No next manufacturing step found",
        )

    return NextStepResponse(
        lot_id=lot.lot_id,
        route_id=lot.route_id,
        step_order=step.step_order,
        step_name=step.step_name,
    )

@router.post(
    "/lots/{lot_id}/advance",
    response_model=WaferLotResponse,
    tags=["MES Lots"],
)
def advance_lot(lot_id: str, db: Session = Depends(get_db)):

    lot = db.get(WaferLot, lot_id)

    if lot is None:
        raise HTTPException(
            status_code=404,
            detail="Lot not found",
        )

    if lot.status == "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail="Lot has already completed its route",
        )

    if lot.route_id is None:
        raise HTTPException(
            status_code=409,
            detail="Lot has no manufacturing route",
        )

    # Retrieve the ordered steps for this lot's route
    steps = db.scalars(
        select(ProcessStep)
        .where(ProcessStep.route_id == lot.route_id)
        .order_by(ProcessStep.step_order)
    ).all()

    # Ensure the route has consecutive step indexes: 0, 1, 2...
    step_orders = [step.step_order for step in steps]

    if not steps or step_orders != list(range(len(steps))):
        raise HTTPException(
            status_code=409,
            detail="Manufacturing route steps are not configured correctly",
        )

    if not 0 <= lot.current_step_index < len(steps):
        raise HTTPException(
            status_code=409,
            detail="No valid processing step available to advance",
        )

    # Simulate completion of the current step
    lot.current_step_index += 1

    if lot.current_step_index == len(steps):
        lot.status = "COMPLETED"
    else:
        lot.status = "IN_PROGRESS"

    db.commit()
    db.refresh(lot)

    return lot