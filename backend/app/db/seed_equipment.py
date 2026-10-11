from app.db.session import SessionLocal
from app.models.equipment import Equipment
from app.models.wafer_lot import WaferLot


EQUIPMENT_SPECS = {
    "DEP-01": "Deposition",
    "LITHO-01": "Lithography",
    "ETCH-01": "Etching",
    "INSP-01": "Inspection",
}


with SessionLocal() as db:
    for equipment_id, process_step in EQUIPMENT_SPECS.items():

        # Avoid inserting duplicate equipment records
        existing = db.get(Equipment, equipment_id)

        if existing is not None:
            print(f"Already exists: {equipment_id}")
            continue

        machine = Equipment(
            equipment_id=equipment_id,
            process_step=process_step,
            status="IDLE",
            current_lot_id=None,
        )

        db.add(machine)
        print(f"Registered: {equipment_id} ({process_step})")

    # Save all new machines in one transaction
    db.commit()

print("Equipment seeding complete.")