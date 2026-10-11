from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.carrier import Carrier
from app.models.transport_job import TransportJob


router = APIRouter(prefix="/amhs", tags=["AMHS"])


class TransportJobCreate(BaseModel):
    job_id: str = Field(min_length=1, max_length=30)
    carrier_id: str = Field(min_length=1, max_length=30)
    destination_station: str = Field(min_length=1, max_length=50)


class TransportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    carrier_id: str
    origin_station: str
    destination_station: str
    status: str
    created_at: datetime


@router.post(
    "/jobs",
    response_model=TransportJobResponse,
    status_code=201,
)
def create_transport_job(
    job_data: TransportJobCreate,
    db: Session = Depends(get_db),
):
    # A transport job ID must be unique
    if db.get(TransportJob, job_data.job_id) is not None:
        raise HTTPException(
            status_code=409,
            detail="Transport job ID already exists",
        )

    # Check that the carrier exists
    carrier = db.get(Carrier, job_data.carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    if carrier.status != "AVAILABLE":
        raise HTTPException(
            status_code=409,
            detail="Carrier is not available",
        )

    # Origin comes from the carrier's actual stored location
    if carrier.current_station == job_data.destination_station:
        raise HTTPException(
            status_code=422,
            detail="Carrier is already at the destination",
        )

    # Avoid assigning another active job to the same carrier
    active_job = db.scalar(
        select(TransportJob).where(
            TransportJob.carrier_id == carrier.carrier_id,
            TransportJob.status.in_(["QUEUED", "IN_TRANSIT"]),
        )
    )

    if active_job is not None:
        raise HTTPException(
            status_code=409,
            detail="Carrier already has an active transport job",
        )

    job = TransportJob(
        job_id=job_data.job_id,
        carrier_id=carrier.carrier_id,
        origin_station=carrier.current_station,
        destination_station=job_data.destination_station,
        status="QUEUED",
    )

    db.add(job)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Transport job conflicts with existing data",
        )

    db.refresh(job)
    return job

@router.post(
    "/jobs/{job_id}/start",
    response_model=TransportJobResponse,
)
def start_transport_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    # Find the transport job
    job = db.get(TransportJob, job_id, with_for_update=True)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Transport job not found",
        )

    # Only queued jobs can be started
    if job.status != "QUEUED":
        raise HTTPException(
            status_code=409,
            detail="Transport job is not queued",
        )

    # Find and lock the carrier
    carrier = db.get(Carrier, job.carrier_id, with_for_update=True)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    if carrier.status != "AVAILABLE":
        raise HTTPException(
            status_code=409,
            detail="Carrier is not available",
        )

    if carrier.current_station != job.origin_station:
        raise HTTPException(
            status_code=409,
            detail="Carrier is not at the job origin",
        )

    # Begin simulated transportation
    job.status = "IN_TRANSIT"
    carrier.status = "MOVING"

    # Save both changes together
    db.commit()
    db.refresh(job)

    return job

@router.post(
    "/jobs/{job_id}/deliver",
    response_model=TransportJobResponse,
)
def deliver_transport_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    # Find and lock the transport job
    job = db.get(TransportJob, job_id, with_for_update=True)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Transport job not found",
        )

    # Only jobs currently in transit can be delivered
    if job.status != "IN_TRANSIT":
        raise HTTPException(
            status_code=409,
            detail="Transport job is not in transit",
        )

    # Find and lock the assigned carrier
    carrier = db.get(Carrier, job.carrier_id, with_for_update=True)

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    if carrier.status != "MOVING":
        raise HTTPException(
            status_code=409,
            detail="Carrier is not moving",
        )

    # Check the last confirmed station
    if carrier.current_station != job.origin_station:
        raise HTTPException(
            status_code=409,
            detail="Carrier location does not match job origin",
        )

    # Complete the simulated delivery
    job.status = "DELIVERED"
    carrier.current_station = job.destination_station
    carrier.status = "AVAILABLE"

    # Persist all three changes in one transaction
    db.commit()
    db.refresh(job)

    return job

# -----------------------------------
# AMHS Monitoring — Read Endpoints
# -----------------------------------

class CarrierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    carrier_id: str
    lot_id: str
    current_station: str
    status: str


@router.get(
    "/carriers",
    response_model=list[CarrierResponse],
)
def list_carriers(
    db: Session = Depends(get_db),
):
    carriers = db.scalars(
        select(Carrier).order_by(Carrier.carrier_id)
    ).all()

    return carriers


@router.get(
    "/jobs",
    response_model=list[TransportJobResponse],
)
def list_transport_jobs(
    db: Session = Depends(get_db),
):
    jobs = db.scalars(
        select(TransportJob).order_by(TransportJob.job_id)
    ).all()

    return jobs