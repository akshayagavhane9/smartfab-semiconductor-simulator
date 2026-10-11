
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.process_route import ProcessRoute
from app.models.process_step import ProcessStep


# ============================================
# 1. Test Data Setup
# ============================================

def create_test_route(db_session: Session):
    """Create a route in the isolated test database."""

    route = ProcessRoute(
        route_id="TEST-ROUTE",
        name="Test Manufacturing Route",
    )

    db_session.add(route)
    db_session.commit()


def create_test_steps(db_session: Session):
    """Create the four semiconductor manufacturing steps."""

    steps = [
        ProcessStep(
            route_id="TEST-ROUTE",
            step_order=0,
            step_name="Deposition",
        ),
        ProcessStep(
            route_id="TEST-ROUTE",
            step_order=1,
            step_name="Lithography",
        ),
        ProcessStep(
            route_id="TEST-ROUTE",
            step_order=2,
            step_name="Etching",
        ),
        ProcessStep(
            route_id="TEST-ROUTE",
            step_order=3,
            step_name="Inspection",
        ),
    ]

    db_session.add_all(steps)
    db_session.commit()


# ============================================
# 2. MES Read Tests
# ============================================

def test_list_lots_starts_empty(client: TestClient):
    """The isolated test database should start empty."""

    response = client.get("/lots")

    assert response.status_code == 200
    assert response.json() == []


def test_development_lot_not_visible(client: TestClient):
    """Development lot LOT-101 must not appear in tests."""

    response = client.get("/lots/LOT-101")

    assert response.status_code == 404


# ============================================
# 3. MES Creation Tests
# ============================================

def test_create_wafer_lot(
    client: TestClient,
    db_session: Session,
):
    """A valid wafer lot should be created and retrieved."""

    create_test_route(db_session)

    payload = {
        "lot_id": "TEST-LOT-001",
        "wafer_count": 25,
        "route_id": "TEST-ROUTE",
    }

    response = client.post("/lots", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["lot_id"] == "TEST-LOT-001"
    assert data["wafer_count"] == 25
    assert data["route_id"] == "TEST-ROUTE"
    assert data["status"] == "CREATED"
    assert data["current_step_index"] == 0

    get_response = client.get("/lots/TEST-LOT-001")

    assert get_response.status_code == 200
    assert get_response.json()["lot_id"] == "TEST-LOT-001"


def test_duplicate_lot_id_rejected(
    client: TestClient,
    db_session: Session,
):
    """The API should reject duplicate wafer-lot IDs."""

    create_test_route(db_session)

    payload = {
        "lot_id": "TEST-LOT-002",
        "wafer_count": 25,
        "route_id": "TEST-ROUTE",
    }

    first_response = client.post("/lots", json=payload)
    second_response = client.post("/lots", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "Lot ID already exists"
    )


# ============================================
# 4. MES Validation Tests
# ============================================

@pytest.mark.parametrize("wafer_count", [0, -5])
def test_invalid_wafer_count_rejected(
    client: TestClient,
    wafer_count: int,
):
    """Wafer count must be greater than zero."""

    payload = {
        "lot_id": "TEST-INVALID-LOT",
        "wafer_count": wafer_count,
        "route_id": "TEST-ROUTE",
    }

    response = client.post("/lots", json=payload)

    assert response.status_code == 422


def test_nonexistent_route_rejected(client: TestClient):
    """A wafer lot must reference an existing route."""

    payload = {
        "lot_id": "TEST-LOT-003",
        "wafer_count": 25,
        "route_id": "MISSING-ROUTE",
    }

    response = client.post("/lots", json=payload)

    assert response.status_code == 422

    assert (
        response.json()["detail"]
        == "Manufacturing route does not exist"
    )


# ============================================
# 5. MES Manufacturing Route Tests
# ============================================

def test_full_manufacturing_route(
    client: TestClient,
    db_session: Session,
):
    """Advance a lot through all four manufacturing steps."""

    # Arrange: Create a valid route and its four steps
    create_test_route(db_session)
    create_test_steps(db_session)

    payload = {
        "lot_id": "TEST-LOT-ROUTE",
        "wafer_count": 25,
        "route_id": "TEST-ROUTE",
    }

    create_response = client.post("/lots", json=payload)

    assert create_response.status_code == 201
    assert create_response.json()["current_step_index"] == 0
    assert create_response.json()["status"] == "CREATED"

    expected_steps = [
        "Deposition",
        "Lithography",
        "Etching",
        "Inspection",
    ]

    # Act and Assert: Process each route step
    for index, step_name in enumerate(expected_steps):

        # Confirm the next required manufacturing operation
        next_response = client.get(
            "/lots/TEST-LOT-ROUTE/next-step"
        )

        assert next_response.status_code == 200
        assert next_response.json()["step_order"] == index
        assert next_response.json()["step_name"] == step_name

        # Simulate completing the current manufacturing step
        advance_response = client.post(
            "/lots/TEST-LOT-ROUTE/advance"
        )

        assert advance_response.status_code == 200

        data = advance_response.json()

        assert data["current_step_index"] == index + 1

        if index < len(expected_steps) - 1:
            assert data["status"] == "IN_PROGRESS"
        else:
            assert data["status"] == "COMPLETED"

    # Confirm the final stored MES state
    final_response = client.get("/lots/TEST-LOT-ROUTE")

    assert final_response.status_code == 200
    assert final_response.json()["current_step_index"] == 4
    assert final_response.json()["status"] == "COMPLETED"

    # A completed lot cannot advance again
    duplicate_advance = client.post(
        "/lots/TEST-LOT-ROUTE/advance"
    )

    assert duplicate_advance.status_code == 409
    assert (
        duplicate_advance.json()["detail"]
        == "Lot has already completed its route"
    )


def test_invalid_route_step_order_rejected(
    client: TestClient,
    db_session: Session,
):
    """A route with missing step indexes cannot be advanced."""

    create_test_route(db_session)

    # Deliberately skip step index 1
    invalid_steps = [
        ProcessStep(
            route_id="TEST-ROUTE",
            step_order=0,
            step_name="Deposition",
        ),
        ProcessStep(
            route_id="TEST-ROUTE",
            step_order=2,
            step_name="Etching",
        ),
    ]

    db_session.add_all(invalid_steps)
    db_session.commit()

    payload = {
        "lot_id": "TEST-LOT-INVALID-ROUTE",
        "wafer_count": 25,
        "route_id": "TEST-ROUTE",
    }

    create_response = client.post("/lots", json=payload)

    assert create_response.status_code == 201

    advance_response = client.post(
        "/lots/TEST-LOT-INVALID-ROUTE/advance"
    )

    assert advance_response.status_code == 409

    assert (
        advance_response.json()["detail"]
        == "Manufacturing route steps are not configured correctly"
    )
