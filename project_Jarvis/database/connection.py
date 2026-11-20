from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings


def _database_url() -> str:
    configured = settings.get("database.url") or settings.get("DATABASE_URL")
    if configured:
        return configured

    host = settings.get("MYSQL_HOST", "localhost")
    port = settings.get("MYSQL_PORT", 3306)
    database = settings.get("MYSQL_DATABASE", "jarvis_db")
    user = settings.get("MYSQL_USER", "root")
    password = settings.get("MYSQL_PASSWORD", "")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


DATABASE_URL = _database_url()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def ensure_database_exists() -> None:
    """Cria o banco configurado antes de abrir conexões que o selecionem."""
    database_url = make_url(DATABASE_URL)
    database_name = database_url.database
    if not database_name:
        return

    server_url = database_url._replace(database=None)
    server_engine = create_engine(server_url, future=True)
    try:
        escaped_name = database_name.replace("`", "``")
        with server_engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{escaped_name}`"))
            connection.commit()
    finally:
        server_engine.dispose()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Abre uma sessão independente e garante commit ou rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """Dependência do FastAPI para uma sessão por requisição."""
    with session_scope() as session:
        yield session
