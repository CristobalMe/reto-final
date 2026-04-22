from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection

from config import Settings

_engine: Engine | None = None


def init_engine(settings: Settings) -> Engine:
    global _engine
    _engine = create_engine(
        settings.mysql_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )
    return _engine


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Engine not initialized; call init_engine() at startup.")
    return _engine


def get_connection() -> Iterator[Connection]:
    engine = get_engine()
    with engine.connect() as conn:
        yield conn
