
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.wafer_lot import WaferLot


def create_sample_lot():
    with Session(engine) as session:

        existing = session.get(WaferLot, "LOT-101")

        if existing is not None:
            print("LOT-101 already exists.")
            return

        lot = WaferLot(
            lot_id="LOT-101",
            wafer_count=25,
            status="CREATED",
            current_step_index=0,
        )

        session.add(lot)
        session.commit()

        print("Wafer lot LOT-101 created successfully!")


if __name__ == "__main__":
    create_sample_lot()
