
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.carrier import Carrier
from app.models.process_route import ProcessRoute


# ============================================
# 1. Test Data Setup
# ============================================

def create_test_carrier(
    client: TestClient,
    db_session: Session,
):
    """Create a temporary lot and carrier for AMHS testing."""

    route = ProcessRoute(
        route_id="TEST-AMHS-ROUTE",
        name="AMHS Test Route",
    )

    db_session.add(route)
    db_session.commit()

    lot_response = client.post(
        "/lots",
        json={
            "lot_id": "TEST-AMHS-LOT",
            "wafer_count": 25,
            "route_id": "TEST-AMHS-ROUTE",
        },
    )

    assert lot_response.status_code == 201

    carrier = Carrier(
        carrier_id="TEST-CARR-101",
        lot_id="TEST-AMHS-LOT",
        current_station="STOCKER-01",
        status="AVAILABLE",
    )

    db_session.add(carrier)
    db_session.commit()


# ============================================
# 2. Successful AMHS Lifecycle
# ============================================

def test_full_amhs_transport_lifecycle(
    client: TestClient,
    db_session: Session,
):
    """Move a carrier from STOCKER-01 to DEP-01."""

    create_test_carrier(client, db_session)

    # Create a transport job
    response = client.post(
        "/amhs/jobs",
        json={
            "job_id": "TEST-JOB-101",
            "carrier_id": "TEST-CARR-101",
            "destination_station": "DEP-01",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "QUEUED"
    assert response.json()["origin_station"] == "STOCKER-01"

    # Start transportation
    response = client.post(
        "/amhs/jobs/TEST-JOB-101/start"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_TRANSIT"

    # Carrier should be moving
    response = client.get("/amhs/carriers")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "MOVING"
    assert (
        response.json()[0]["current_station"]
        == "STOCKER-01"
    )

    # Complete delivery
    response = client.post(
        "/amhs/jobs/TEST-JOB-101/deliver"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "DELIVERED"

    # Verify carrier state and location
    response = client.get("/amhs/carriers")

    assert response.status_code == 200

    carrier = response.json()[0]

    assert carrier["status"] == "AVAILABLE"
    assert carrier["current_station"] == "DEP-01"
    assert carrier["lot_id"] == "TEST-AMHS-LOT"

    # Prevent duplicate delivery
    response = client.post(
        "/amhs/jobs/TEST-JOB-101/deliver"
    )

    assert response.status_code == 409


# ============================================
# 3. Invalid AMHS Operations
# ============================================

def test_nonexistent_carrier_rejected(
    client: TestClient,
):
    """Cannot create transport for a missing carrier."""

    response = client.post(
        "/amhs/jobs",
        json={
            "job_id": "TEST-MISSING-CARRIER-JOB",
            "carrier_id": "DOES-NOT-EXIST",
            "destination_station": "DEP-01",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Carrier not found"


def test_cannot_deliver_queued_job(
    client: TestClient,
    db_session: Session,
):
    """A job must start before it can be delivered."""

    create_test_carrier(client, db_session)

    create_response = client.post(
        "/amhs/jobs",
        json={
            "job_id": "TEST-QUEUED-JOB",
            "carrier_id": "TEST-CARR-101",
            "destination_station": "DEP-01",
        },
    )

    assert create_response.status_code == 201

    # Attempt delivery without starting transportation
    response = client.post(
        "/amhs/jobs/TEST-QUEUED-JOB/deliver"
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Transport job is not in transit"
    )


def test_second_active_transport_job_rejected(
    client: TestClient,
    db_session: Session,
):
    """One carrier cannot have two active transport jobs."""

    create_test_carrier(client, db_session)

    first_job = client.post(
        "/amhs/jobs",
        json={
            "job_id": "TEST-JOB-FIRST",
            "carrier_id": "TEST-CARR-101",
            "destination_station": "DEP-01",
        },
    )

    assert first_job.status_code == 201

    # The first job is still QUEUED.
    # Attempt to create another active job for the same carrier.
    second_job = client.post(
        "/amhs/jobs",
        json={
            "job_id": "TEST-JOB-SECOND",
            "carrier_id": "TEST-CARR-101",
            "destination_station": "LITHO-01",
        },
    )

    assert second_job.status_code == 409
    assert (
        second_job.json()["detail"]
        == "Carrier already has an active transport job"
    )
