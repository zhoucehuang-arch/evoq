from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from quant_evo_nextgen.db.base import Base


def create_sqlalchemy_engine(database_url: str, *, echo: bool = False) -> Engine:
    engine_kwargs: dict[str, object] = {
        "echo": echo,
        "future": True,
    }

    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if database_url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool

    return create_engine(database_url, **engine_kwargs)


class Database:
    def __init__(self, database_url: str, *, echo: bool = False) -> None:
        self.engine = create_sqlalchemy_engine(database_url, echo=echo)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def drop_schema(self) -> None:
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()
