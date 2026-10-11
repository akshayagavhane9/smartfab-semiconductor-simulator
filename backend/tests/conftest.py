
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import DATABASE_URL
from app.db.session import get_db
from app.main import app
from app.models.base import Base

# Import every model so SQLAlchemy knows all tables and relationships.
from app.models import (
    carrier,
    equipment,
    process_route,
    process_step,
    transport_job,
    wafer_lot,
)


TEST_DATABASE_NAME = "smartfab_test_db"

# Safety check: the development database must remain separate.
if DATABASE_URL.database == TEST_DATABASE_NAME:
    raise RuntimeError(
        "Development database configuration points to the test database."
    )

# Reuse the existing PostgreSQL connection settings,
# but explicitly select the dedicated test database.
TEST_DATABASE_URL = DATABASE_URL.set(
    database=TEST_DATABASE_NAME
)


@pytest.fixture(scope="session")
def test_engine():
    """Create a database engine exclusively for automated tests."""

    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

    # Refuse to create tables in any unexpected database.
    if engine.url.database != TEST_DATABASE_NAME:
        engine.dispose()
        raise RuntimeError("Unsafe test database configuration.")

    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()


@pytest.fixture()
def db_connection(test_engine):
    """Open a transaction that is rolled back after each test."""

    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            yield connection
        finally:
            transaction.rollback()


@pytest.fixture()
def db_session(db_connection):
    """Provide a database session for preparing test records."""

    with Session(
        bind=db_connection,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    ) as session:
        yield session


@pytest.fixture()
def client(db_connection):
    """Send API requests using the isolated test database."""

    def override_get_db():
        with Session(
            bind=db_connection,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session

    # Replace the application's normal database dependency.
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
