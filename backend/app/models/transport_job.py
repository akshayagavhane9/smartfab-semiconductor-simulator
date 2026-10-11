from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TransportJob(Base):
    __tablename__ = "transport_jobs"

    job_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
    )

    carrier_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("carriers.carrier_id"),
        nullable=False,
    )

    origin_station: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    destination_station: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="QUEUED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED', 'IN_TRANSIT', 'DELIVERED')",
            name="ck_transport_job_status",
        ),
        CheckConstraint(
            "origin_station <> destination_station",
            name="ck_transport_different_stations",
        ),
    )