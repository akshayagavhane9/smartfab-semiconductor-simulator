
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Locate the SmartFab root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")

# Construct the PostgreSQL connection URL
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host="127.0.0.1",
    port=5433,
    database=os.getenv("POSTGRES_DB"),
)

# Create the SQLAlchemy database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
