
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    CheckConstraint,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WaferLot(Base):
    __tablename__ = "wafer_lots"

    lot_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )
    route_id: Mapped[str | None] = mapped_column(
        String(30),
        ForeignKey("process_routes.route_id"),
        nullable=True
    )

    wafer_count: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), default="CREATED", nullable=False
    )

    current_step_index: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "wafer_count > 0",
            name="ck_wafer_count_positive"
        ),
        CheckConstraint(
            "current_step_index >= 0",
            name="ck_step_index_nonnegative"
        ),
    )
