from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
    )

    process_step: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="IDLE",
    )

    current_lot_id: Mapped[str | None] = mapped_column(
        String(30),
        ForeignKey("wafer_lots.lot_id"),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('IDLE', 'PROCESSING', 'DOWN')",
            name="ck_equipment_status",
        ),
        CheckConstraint(
            "status <> 'PROCESSING' OR current_lot_id IS NOT NULL",
            name="ck_processing_requires_lot",
        ),
    )