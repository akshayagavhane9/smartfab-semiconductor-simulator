from app.db.session import SessionLocal
from app.models.carrier import Carrier
from app.models.wafer_lot import WaferLot


with SessionLocal() as db:

    # Confirm the wafer lot exists
    lot = db.get(WaferLot, "LOT-101")

    if lot is None:
        raise RuntimeError("LOT-101 does not exist")

    # Prevent creating the same carrier twice
    existing_carrier = db.get(Carrier, "CARR-101")

    if existing_carrier is not None:
        print("CARR-101 already exists")

    else:
        carrier = Carrier(
            carrier_id="CARR-101",
            lot_id="LOT-101",
            current_station="STOCKER-01",
            status="AVAILABLE",
        )

        db.add(carrier)
        db.commit()

        print("Carrier CARR-101 created successfully")