from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


def test_upgrade_head_creates_expected_schema(tmp_path: Path):
    database_path = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")

    inspector = inspect(create_engine(f"sqlite:///{database_path}"))
    assert set(inspector.get_table_names()) == {"alembic_version", "comments", "locations", "posts"}
    foreign_key = inspector.get_foreign_keys("comments")[0]
    assert foreign_key["referred_table"] == "posts"
    assert foreign_key["options"]["ondelete"] == "CASCADE"


def test_downgrade_base_removes_application_tables(tmp_path: Path):
    database_path = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(config, "head")

    command.downgrade(config, "base")

    inspector = inspect(create_engine(f"sqlite:///{database_path}"))
    assert inspector.get_table_names() == ["alembic_version"]
