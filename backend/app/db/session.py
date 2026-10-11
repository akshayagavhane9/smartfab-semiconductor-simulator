from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.db.database import engine


# Factory for creating database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session and close it after use."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()