from __future__ import annotations

from pathlib import Path

import pytest

from quant_evo_nextgen.config import Settings
from quant_evo_nextgen.db.session import Database


@pytest.fixture
def sqlite_database(tmp_path: Path) -> Database:
    database = Database(f"sqlite+pysqlite:///{tmp_path / 'evoq-test.db'}")
    database.create_schema()
    try:
        yield database
    finally:
        database.dispose()


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        repo_root=tmp_path,
        postgres_url=f"sqlite+pysqlite:///{tmp_path / 'evoq-test.db'}",
    )
