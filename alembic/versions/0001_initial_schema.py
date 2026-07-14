"""Create locations, posts, and comments tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("address1", sa.String(length=500), nullable=True),
        sa.Column("address2", sa.String(length=500), nullable=True),
        sa.Column("district", sa.String(length=20), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=100), nullable=True),
        sa.Column("source_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "category IN ('관광지','레포츠','문화시설','쇼핑','숙박','여행코스','축제공연행사')",
            name="ck_locations_category",
        ),
        sa.CheckConstraint("source_order >= 1", name="ck_locations_source_order"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id"),
    )
    op.create_index(
        "ix_locations_category_district_order",
        "locations",
        ["category", "district", "source_order"],
        unique=False,
    )
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=10), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("password", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "tag IN ('관광','맛집','문화','행사','숙박','쇼핑','자유')",
            name="ck_posts_tag",
        ),
        sa.CheckConstraint("length(title) BETWEEN 1 AND 100", name="ck_posts_title_length"),
        sa.CheckConstraint("length(content) BETWEEN 1 AND 5000", name="ck_posts_content_length"),
        sa.CheckConstraint("length(password) BETWEEN 4 AND 20", name="ck_posts_password_length"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posts_created_at", "posts", ["created_at"], unique=False)
    op.create_index("ix_posts_tag", "posts", ["tag"], unique=False)
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("password", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(content) BETWEEN 1 AND 1000", name="ck_comments_content_length"),
        sa.CheckConstraint("length(password) BETWEEN 4 AND 20", name="ck_comments_password_length"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_comments_post_created_at",
        "comments",
        ["post_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_comments_post_created_at", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_posts_tag", table_name="posts")
    op.drop_index("ix_posts_created_at", table_name="posts")
    op.drop_table("posts")
    op.drop_index("ix_locations_category_district_order", table_name="locations")
    op.drop_table("locations")
