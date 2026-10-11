
from app.db.database import engine
from app.models.base import Base
from app.models.wafer_lot import WaferLot
from app.models.process_route import ProcessRoute
from app.models.process_step import ProcessStep
from app.models.carrier import Carrier
from app.models.transport_job import TransportJob
from app.models.equipment import Equipment


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")


if __name__ == "__main__":
    init_db()
