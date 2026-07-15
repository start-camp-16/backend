import logging
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from alembic import command


def alembic_config(database_path: Path) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    return config


def test_upgrade_resets_community_and_replaces_tag_with_district_prefix(tmp_path: Path):
    database_path = tmp_path / "migration.db"
    config = alembic_config(database_path)
    command.upgrade(config, "0002_add_courses")
    engine = sa.create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO posts (tag, title, content, password, created_at, updated_at) "
                "VALUES ('자유', '기존 글', '기존 본문', '1234', CURRENT_TIMESTAMP, "
                "CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO comments (post_id, content, password, created_at, updated_at) "
                "VALUES (1, '기존 댓글', '1234', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )

    command.upgrade(config, "head")

    inspector = sa.inspect(engine)
    assert {column["name"] for column in inspector.get_columns("posts")} >= {
        "district",
        "prefix",
    }
    assert "tag" not in {column["name"] for column in inspector.get_columns("posts")}
    indexes = {index["name"]: index for index in inspector.get_indexes("posts")}
    assert indexes.keys() >= {
        "ix_posts_district",
        "ix_posts_prefix",
    }
    assert indexes["ix_posts_district"]["column_names"] == ["district"]
    assert indexes["ix_posts_prefix"]["column_names"] == ["prefix"]
    with engine.begin() as connection:
        assert connection.scalar(sa.text("SELECT count(*) FROM posts")) == 0
        assert connection.scalar(sa.text("SELECT count(*) FROM comments")) == 0
        with pytest.raises(IntegrityError):
            connection.execute(
                sa.text(
                    "INSERT INTO posts "
                    "(district, prefix, title, content, password, created_at, updated_at) "
                    "VALUES ('기타', '자유', '제목', '본문', '1234', CURRENT_TIMESTAMP, "
                    "CURRENT_TIMESTAMP)"
                )
            )
    engine.dispose()


def test_alembic_upgrade_keeps_existing_application_loggers_enabled(tmp_path: Path) -> None:
    app_logger = logging.getLogger("app.main")
    app_logger.disabled = False

    try:
        command.upgrade(alembic_config(tmp_path / "logging.db"), "head")

        assert app_logger.disabled is False
    finally:
        app_logger.disabled = False
