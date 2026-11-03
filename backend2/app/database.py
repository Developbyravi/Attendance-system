from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings
from app.core.logging import logger

connect_args = {}
if settings.is_sqlite:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DB_ECHO,
    pool_pre_ping=True
)

# Enable Foreign Key enforcement for SQLite
if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a transactional database session.
    Closes automatically after request completion.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database schema tables if they do not exist.
    """
    logger.info("Initializing database schema...")
    import app.models # Ensure all models are registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

