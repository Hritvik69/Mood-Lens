import duckdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from database.models import Base

# SQLAlchemy SQLite setup
DATABASE_URL = f"sqlite:///{settings.DATABASE_PATH}"

# Connect with thread-safety and WAL parameters
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)

# Enable WAL (Write Ahead Logging) and setup other SQLite pragmas
with engine.connect() as connection:
    connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
    connection.exec_driver_sql("PRAGMA synchronous=NORMAL;")
    connection.exec_driver_sql("PRAGMA foreign_keys=ON;")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the SQLite database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency injection session getter for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_duckdb_conn():
    """
    Connects to DuckDB and attaches the SQLite database.
    Allows ultra-fast analytical queries over history tables.
    """
    # DuckDB in-memory session
    conn = duckdb.connect()
    conn.execute("INSTALL sqlite; LOAD sqlite;")
    # Attach sqlite database
    db_path_str = str(settings.DATABASE_PATH.resolve()).replace("\\", "/")
    conn.execute(f"ATTACH '{db_path_str}' AS sqlite_db (TYPE sqlite);")
    return conn
