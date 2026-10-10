
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.process_route import ProcessRoute
from app.models.process_step import ProcessStep


def create_standard_route():

    with Session(engine) as session:

        route_id = "STANDARD-4"

        existing_route = session.get(
            ProcessRoute, route_id
        )

        if existing_route is not None:
            print("Route already exists.")
            return

        route = ProcessRoute(
            route_id=route_id,
            name="Standard Four-Step Manufacturing"
        )

        session.add(route)
        session.flush()

        steps = [
            "Deposition",
            "Lithography",
            "Etching",
            "Inspection"
        ]

        for index, step_name in enumerate(steps):
            step = ProcessStep(
                route_id=route_id,
                step_order=index,
                step_name=step_name
            )

            session.add(step)

        session.commit()

        print("Manufacturing route created successfully!")


if __name__ == "__main__":
    create_standard_route()
