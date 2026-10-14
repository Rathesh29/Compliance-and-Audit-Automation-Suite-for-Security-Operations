import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logging_config import logger

Base = declarative_base()


def get_engine():
    db_url = settings.DATABASE_URL
    connect_args = {}

    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_engine(db_url, echo=False, connect_args=connect_args)
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        return engine

    try:
        # Attempt PostgreSQL connection
        engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to primary PostgreSQL database.")
        return engine
    except Exception as e:
        if settings.DATABASE_URL_SQLITE_FALLBACK:
            logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite for robust local execution: {settings.SQLITE_FALLBACK_URL}")
            fallback_engine = create_engine(
                settings.SQLITE_FALLBACK_URL,
                echo=False,
                connect_args={"check_same_thread": False}
            )
            @event.listens_for(fallback_engine, "connect")
            def set_sqlite_pragma_fallback(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            return fallback_engine
        raise e


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
