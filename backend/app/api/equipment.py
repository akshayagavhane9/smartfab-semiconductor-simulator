from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.carrier import Carrier
from app.models.equipment import Equipment
from app.models.process_step import ProcessStep
from app.models.wafer_lot import WaferLot


router = APIRouter(prefix="/equipment", tags=["Equipment"])


class StartProcessingRequest(BaseModel):
    lot_id: str


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equipment_id: str
    process_step: str
    status: str
    current_lot_id: str | None


@router.post(
    "/{equipment_id}/start",
    response_model=EquipmentResponse,
)
def start_processing(
    equipment_id: str,
    request: StartProcessingRequest,
    db: Session = Depends(get_db),
):
    # Find and lock the equipment
    machine = db.get(
        Equipment, equipment_id, with_for_update=True
    )

    if machine is None:
        raise HTTPException(404, "Equipment not found")

    if machine.status != "IDLE" or machine.current_lot_id is not None:
        raise HTTPException(409, "Equipment is not available")

    # Find and lock the manufacturing lot
    lot = db.get(WaferLot, request.lot_id, with_for_update=True)

    if lot is None:
        raise HTTPException(404, "Wafer lot not found")

    if lot.status == "COMPLETED":
        raise HTTPException(409, "Wafer lot is already completed")

    if lot.route_id is None:
        raise HTTPException(409, "Wafer lot has no route")

    # Determine the operation required by the lot
    step = db.scalar(
        select(ProcessStep).where(
            ProcessStep.route_id == lot.route_id,
            ProcessStep.step_order == lot.current_step_index,
        )
    )

    if step is None:
        raise HTTPException(409, "No valid manufacturing step")

    if step.step_name != machine.process_step:
        raise HTTPException(409, "Wrong equipment for manufacturing step")

    # Prevent the lot from processing on another machine
    existing_processing = db.scalar(
        select(Equipment).where(
            Equipment.current_lot_id == lot.lot_id,
            Equipment.status == "PROCESSING",
        )
    )

    if existing_processing is not None:
        raise HTTPException(409, "Wafer lot is already processing")

    # Verify the carrier is at this equipment station
    carrier = db.scalar(
        select(Carrier)
        .where(Carrier.lot_id == lot.lot_id)
        .with_for_update()
    )

    if carrier is None:
        raise HTTPException(409, "No carrier assigned to wafer lot")

    if carrier.current_station != machine.equipment_id:
        raise HTTPException(409, "Carrier is not at the equipment station")

    if carrier.status != "AVAILABLE":
        raise HTTPException(409, "Carrier is not available")

    # Begin simulated wafer processing
    machine.status = "PROCESSING"
    machine.current_lot_id = lot.lot_id

    db.commit()
    db.refresh(machine)

    return machine

@router.post(
    "/{equipment_id}/complete",
    response_model=EquipmentResponse,
)
def complete_processing(
    equipment_id: str,
    db: Session = Depends(get_db),
):
    # Find and lock the equipment
    machine = db.get(
        Equipment, equipment_id, with_for_update=True
    )

    if machine is None:
        raise HTTPException(404, "Equipment not found")

    # Only processing equipment can complete an operation
    if machine.status != "PROCESSING" or machine.current_lot_id is None:
        raise HTTPException(409, "Equipment is not processing a lot")

    # Find and lock the assigned wafer lot
    lot = db.get(
        WaferLot, machine.current_lot_id, with_for_update=True
    )

    if lot is None or lot.status == "COMPLETED" or lot.route_id is None:
        raise HTTPException(409, "Wafer lot cannot be advanced")

    # Retrieve the manufacturing route
    steps = db.scalars(
        select(ProcessStep)
        .where(ProcessStep.route_id == lot.route_id)
        .order_by(ProcessStep.step_order)
    ).all()

    # Check that route steps are configured consecutively
    if not steps or [s.step_order for s in steps] != list(range(len(steps))):
        raise HTTPException(409, "Manufacturing route is invalid")

    if not 0 <= lot.current_step_index < len(steps):
        raise HTTPException(409, "No valid manufacturing step")

    # Confirm equipment matches the operation being completed
    current_step = steps[lot.current_step_index]

    if current_step.step_name != machine.process_step:
        raise HTTPException(409, "Equipment does not match current step")

    # Confirm carrier is still available at this station
    carrier = db.scalar(
        select(Carrier)
        .where(Carrier.lot_id == lot.lot_id)
        .with_for_update()
    )

    if carrier is None:
        raise HTTPException(409, "No carrier assigned to wafer lot")

    if carrier.current_station != machine.equipment_id or carrier.status != "AVAILABLE":
        raise HTTPException(409, "Carrier is not available at equipment")

    # Simulate successful completion of this operation
    lot.current_step_index += 1

    if lot.current_step_index == len(steps):
        lot.status = "COMPLETED"
    else:
        lot.status = "IN_PROGRESS"

    # Release the equipment
    machine.status = "IDLE"
    machine.current_lot_id = None

    # Save equipment and lot changes together
    db.commit()
    db.refresh(machine)

    return machine

@router.post(
    "/{equipment_id}/fail",
    response_model=EquipmentResponse,
)
def fail_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
):
    # Find and lock the equipment
    machine = db.get(
        Equipment, equipment_id, with_for_update=True
    )

    if machine is None:
        raise HTTPException(
            status_code=404,
            detail="Equipment not found",
        )

    # Prevent failing an already failed machine
    if machine.status == "DOWN":
        raise HTTPException(
            status_code=409,
            detail="Equipment is already down",
        )

    # Simulate a machine failure
    machine.status = "DOWN"

    # Preserve any assigned lot if processing was interrupted
    db.commit()
    db.refresh(machine)

    return machine

@router.post(
    "/{equipment_id}/recover",
    response_model=EquipmentResponse,
)
def recover_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
):
    # Find and lock the equipment
    machine = db.get(
        Equipment, equipment_id, with_for_update=True
    )

    if machine is None:
        raise HTTPException(
            status_code=404,
            detail="Equipment not found",
        )

    # Only failed equipment can be recovered
    if machine.status != "DOWN":
        raise HTTPException(
            status_code=409,
            detail="Equipment is not down",
        )

    # Do not discard a lot interrupted by equipment failure
    if machine.current_lot_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Interrupted wafer lot requires resolution",
        )

    # Simulate successful equipment recovery
    machine.status = "IDLE"

    db.commit()
    db.refresh(machine)

    return machine

@router.get(
    "",
    response_model=list[EquipmentResponse],
)
def list_equipment(
    db: Session = Depends(get_db),
):
    machines = db.scalars(
        select(Equipment).order_by(Equipment.equipment_id)
    ).all()

    return machines