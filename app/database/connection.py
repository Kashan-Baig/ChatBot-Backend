from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in .env"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # Recycle pooled connections every 3 minutes rather than waiting on
    # pre_ping to catch a stale one — pre_ping doesn't reliably recognize
    # every disconnect message a given driver/SQLAlchemy version can see
    # from Neon, so proactively cycling connections is the more robust
    # defense (paired with the retry-and-reset wrapper in session_manager.py).
    pool_recycle=180,
    # Without this, a wrong host/port/firewall issue on the sync engine
    # hangs forever instead of raising — which is what "server just
    # loads and never comes up" usually turns out to be.
    connect_args={"connect_timeout": 10}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)