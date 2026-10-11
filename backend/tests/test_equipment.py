
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.carrier import Carrier
from app.models.equipment import Equipment
from app.models.process_route import ProcessRoute
from app.models.process_step import ProcessStep


# ============================================
# 1. Test Data Setup
# ============================================

def create_equipment_scenario(
    client: TestClient,
    db_session: Session,
):
    """Prepare a lot, route, carrier, and equipment in the test DB."""

    route = ProcessRoute(
        route_id="TEST-EQ-ROUTE",
        name="Equipment Test Route",
    )

    db_session.add(route)
    db_session.flush()

    steps = [
        ProcessStep(
            route_id="TEST-EQ-ROUTE",
            step_order=0,
            step_name="Deposition",
        ),
        ProcessStep(
            route_id="TEST-EQ-ROUTE",
            step_order=1,
            step_name="Lithography",
        ),
    ]

    db_session.add_all(steps)
    db_session.commit()

    lot_response = client.post(
        "/lots",
        json={
            "lot_id": "TEST-EQ-LOT",
            "wafer_count": 25,
            "route_id": "TEST-EQ-ROUTE",
        },
    )

    assert lot_response.status_code == 201

    machine = Equipment(
        equipment_id="TEST-DEP-01",
        process_step="Deposition",
        status="IDLE",
        current_lot_id=None,
    )

    carrier = Carrier(
        carrier_id="TEST-EQ-CARRIER",
        lot_id="TEST-EQ-LOT",
        current_station="TEST-DEP-01",
        status="AVAILABLE",
    )

    db_session.add_all([machine, carrier])
    db_session.commit()


# ============================================
# 2. Successful Equipment Processing
# ============================================

def test_equipment_processing_advances_wafer_lot(
    client: TestClient,
    db_session: Session,
):
    """Completing equipment processing advances the MES route."""

    create_equipment_scenario(client, db_session)

    # Start Deposition
    start_response = client.post(
        "/equipment/TEST-DEP-01/start",
        json={"lot_id": "TEST-EQ-LOT"},
    )

    assert start_response.status_code == 200
    assert start_response.json()["status"] == "PROCESSING"
    assert start_response.json()["current_lot_id"] == "TEST-EQ-LOT"

    # Starting processing must not advance the lot
    lot_response = client.get("/lots/TEST-EQ-LOT")

    assert lot_response.status_code == 200
    assert lot_response.json()["current_step_index"] == 0

    # Complete Deposition
    complete_response = client.post(
        "/equipment/TEST-DEP-01/complete"
    )

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "IDLE"
    assert complete_response.json()["current_lot_id"] is None

    # Check MES advancement
    lot_response = client.get("/lots/TEST-EQ-LOT")

    assert lot_response.status_code == 200
    assert lot_response.json()["current_step_index"] == 1
    assert lot_response.json()["status"] == "IN_PROGRESS"

    next_step = client.get("/lots/TEST-EQ-LOT/next-step")

    assert next_step.status_code == 200
    assert next_step.json()["step_name"] == "Lithography"

    # Reject completing the same operation twice
    duplicate_completion = client.post(
        "/equipment/TEST-DEP-01/complete"
    )

    assert duplicate_completion.status_code == 409


# ============================================
# 3. Idle Equipment Failure and Recovery
# ============================================

def test_equipment_failure_and_recovery(
    client: TestClient,
    db_session: Session,
):
    """An idle machine can fail and recover safely."""

    machine = Equipment(
        equipment_id="TEST-IDLE-01",
        process_step="Etching",
        status="IDLE",
        current_lot_id=None,
    )

    db_session.add(machine)
    db_session.commit()

    # Simulate equipment failure
    fail_response = client.post(
        "/equipment/TEST-IDLE-01/fail"
    )

    assert fail_response.status_code == 200
    assert fail_response.json()["status"] == "DOWN"
    assert fail_response.json()["current_lot_id"] is None

    # A machine cannot fail twice
    duplicate_failure = client.post(
        "/equipment/TEST-IDLE-01/fail"
    )

    assert duplicate_failure.status_code == 409
    assert (
        duplicate_failure.json()["detail"]
        == "Equipment is already down"
    )

    # Recover the machine
    recover_response = client.post(
        "/equipment/TEST-IDLE-01/recover"
    )

    assert recover_response.status_code == 200
    assert recover_response.json()["status"] == "IDLE"

    # A machine that is already IDLE cannot recover again
    duplicate_recovery = client.post(
        "/equipment/TEST-IDLE-01/recover"
    )

    assert duplicate_recovery.status_code == 409
    assert (
        duplicate_recovery.json()["detail"]
        == "Equipment is not down"
    )


# ============================================
# 4. Reject Processing on Failed Equipment
# ============================================

def test_failed_equipment_cannot_start_processing(
    client: TestClient,
    db_session: Session,
):
    """A DOWN machine must reject new wafer processing."""

    create_equipment_scenario(client, db_session)

    # Fail the machine before processing begins
    fail_response = client.post(
        "/equipment/TEST-DEP-01/fail"
    )

    assert fail_response.status_code == 200
    assert fail_response.json()["status"] == "DOWN"

    # Attempt to start processing
    start_response = client.post(
        "/equipment/TEST-DEP-01/start",
        json={"lot_id": "TEST-EQ-LOT"},
    )

    assert start_response.status_code == 409
    assert (
        start_response.json()["detail"]
        == "Equipment is not available"
    )

    # The wafer lot must remain at Deposition
    lot_response = client.get("/lots/TEST-EQ-LOT")

    assert lot_response.status_code == 200
    assert lot_response.json()["current_step_index"] == 0


# ============================================
# 5. Failure During Active Processing
# ============================================

def test_failure_during_processing_preserves_lot(
    client: TestClient,
    db_session: Session,
):
    """An interrupted wafer lot must not be lost or completed."""

    create_equipment_scenario(client, db_session)

    # Start processing the wafer lot
    start_response = client.post(
        "/equipment/TEST-DEP-01/start",
        json={"lot_id": "TEST-EQ-LOT"},
    )

    assert start_response.status_code == 200
    assert start_response.json()["status"] == "PROCESSING"

    # Simulate a failure during processing
    fail_response = client.post(
        "/equipment/TEST-DEP-01/fail"
    )

    assert fail_response.status_code == 200
    assert fail_response.json()["status"] == "DOWN"

    # The interrupted lot must remain assigned
    assert (
        fail_response.json()["current_lot_id"]
        == "TEST-EQ-LOT"
    )

    # Failed equipment cannot complete its operation
    complete_response = client.post(
        "/equipment/TEST-DEP-01/complete"
    )

    assert complete_response.status_code == 409
    assert (
        complete_response.json()["detail"]
        == "Equipment is not processing a lot"
    )

    # Recovery must not silently discard the interrupted lot
    recover_response = client.post(
        "/equipment/TEST-DEP-01/recover"
    )

    assert recover_response.status_code == 409
    assert (
        recover_response.json()["detail"]
        == "Interrupted wafer lot requires resolution"
    )

    # MES must still show the original processing step
    lot_response = client.get("/lots/TEST-EQ-LOT")

    assert lot_response.status_code == 200
    assert lot_response.json()["current_step_index"] == 0
    assert lot_response.json()["status"] == "CREATED"
