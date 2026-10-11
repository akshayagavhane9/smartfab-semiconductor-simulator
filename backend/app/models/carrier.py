from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
    )

    lot_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("wafer_lots.lot_id"),
        unique=True,
        nullable=False,
    )

    current_station: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="AVAILABLE",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('AVAILABLE', 'MOVING')",
            name="ck_carrier_status",
        ),
    )