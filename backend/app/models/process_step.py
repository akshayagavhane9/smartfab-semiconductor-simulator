
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    route_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("process_routes.route_id"),
        nullable=False
    )

    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    step_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "step_order >= 0",
            name="ck_process_step_order_nonnegative"
        ),
        UniqueConstraint(
            "route_id",
            "step_order",
            name="uq_process_route_step_order"
        ),
    )
