
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProcessRoute(Base):
    __tablename__ = "process_routes"

    route_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
