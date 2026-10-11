
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.process_route import ProcessRoute
from app.models.wafer_lot import WaferLot


def create_sample_lot():
    route_id = "STANDARD-4"

    with Session(engine) as session:

        # Verify the manufacturing route exists.
        route = session.get(ProcessRoute, route_id)

        if route is None:
            raise RuntimeError(
                "STANDARD-4 route does not exist. "
                "Run python -m app.db.seed_route first."
            )

        # Prevent duplicate sample lots.
        existing = session.get(WaferLot, "LOT-101")

        if existing is not None:
            print("LOT-101 already exists. No changes made.")
            return

        # Create a wafer lot assigned to the standard route.
        lot = WaferLot(
            lot_id="LOT-101",
            route_id=route_id,
            wafer_count=25,
            status="CREATED",
            current_step_index=0,
        )

        session.add(lot)
        session.commit()

        print(
            "LOT-101 created successfully "
            "with route STANDARD-4!"
        )


if __name__ == "__main__":
    create_sample_lot()
