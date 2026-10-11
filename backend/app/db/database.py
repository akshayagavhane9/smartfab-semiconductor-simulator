
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


# Locate the SmartFab root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load local environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")


# Database connection settings
# Local Mac defaults:
#   host = 127.0.0.1
#   port = 5433
#
# Docker Compose will override these:
#   host = postgres
#   port = 5432

DATABASE_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
DATABASE_PORT = int(os.getenv("POSTGRES_PORT", "5433"))


# Construct the PostgreSQL connection URL
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    database=os.getenv("POSTGRES_DB"),
)


# Create the SQLAlchemy database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
