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
    assert set(inspector.get_table_names()) == {
        "alembic_version",
        "comments",
        "course_stops",
        "courses",
        "locations",
        "posts",
    }
    foreign_key = inspector.get_foreign_keys("comments")[0]
    assert foreign_key["referred_table"] == "posts"
    assert foreign_key["options"]["ondelete"] == "CASCADE"
    course_stop_foreign_keys = {
        foreign_key["referred_table"]: foreign_key
        for foreign_key in inspector.get_foreign_keys("course_stops")
    }
    assert course_stop_foreign_keys["courses"]["options"]["ondelete"] == "CASCADE"
    assert course_stop_foreign_keys["locations"]["referred_columns"] == ["id"]


def test_downgrade_base_removes_application_tables(tmp_path: Path):
    database_path = tmp_path / "migration.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(config, "head")

    command.downgrade(config, "base")

    inspector = inspect(create_engine(f"sqlite:///{database_path}"))
    assert inspector.get_table_names() == ["alembic_version"]
