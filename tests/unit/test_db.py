from sqlalchemy import text

from app.db import create_database_engine


def test_sqlite_connections_enable_foreign_keys(tmp_path):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'test.db'}")

    with engine.connect() as connection:
        enabled = connection.scalar(text("PRAGMA foreign_keys"))

    assert enabled == 1
