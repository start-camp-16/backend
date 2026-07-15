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


def test_upgrade_resets_community_and_adds_new_constraints(tmp_path: Path):
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
    assert {index["name"] for index in inspector.get_indexes("posts")} >= {
        "ix_posts_district",
        "ix_posts_prefix",
    }
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
