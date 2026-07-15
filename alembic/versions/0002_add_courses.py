"""Add courses and course stops tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_add_courses"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(title) BETWEEN 1 AND 100", name="ck_courses_title_length"),
        sa.CheckConstraint("length(password) BETWEEN 4 AND 20", name="ck_courses_password_length"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_table(
        "course_stops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position BETWEEN 1 AND 5", name="ck_course_stops_position"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "location_id", name="uq_course_stops_course_location"),
        sa.UniqueConstraint("course_id", "position", name="uq_course_stops_course_position"),
    )


def downgrade() -> None:
    op.drop_table("course_stops")
    op.drop_table("courses")
