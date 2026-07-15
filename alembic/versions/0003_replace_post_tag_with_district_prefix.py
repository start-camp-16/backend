"""Replace post tag with district and prefix."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_replace_post_tag_with_district_prefix"
down_revision: str | None = "0002_add_courses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DISTRICT_CHECK = (
    "district IN ("
    "'강남구','강동구','강북구','강서구','관악구','광진구','구로구','금천구',"
    "'노원구','도봉구','동대문구','동작구','마포구','서대문구','서초구','성동구',"
    "'성북구','송파구','양천구','영등포구','용산구','은평구','종로구','중구','중랑구'"
    ")"
)
PREFIX_CHECK = "prefix IN ('관광','맛집','문화','행사','숙박','쇼핑','자유')"


def upgrade() -> None:
    op.execute(sa.text("DELETE FROM comments"))
    op.execute(sa.text("DELETE FROM posts"))
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_index("ix_posts_tag")
        batch_op.drop_constraint("ck_posts_tag", type_="check")
        batch_op.alter_column("tag", new_column_name="prefix", existing_type=sa.String(10))
        batch_op.add_column(sa.Column("district", sa.String(10), nullable=False))
        batch_op.create_check_constraint("ck_posts_district", DISTRICT_CHECK)
        batch_op.create_check_constraint("ck_posts_prefix", PREFIX_CHECK)
        batch_op.create_index("ix_posts_district", ["district"], unique=False)
        batch_op.create_index("ix_posts_prefix", ["tag"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_index("ix_posts_prefix")
        batch_op.drop_index("ix_posts_district")
        batch_op.drop_constraint("ck_posts_prefix", type_="check")
        batch_op.drop_constraint("ck_posts_district", type_="check")
        batch_op.drop_column("district")
        batch_op.alter_column("prefix", new_column_name="tag", existing_type=sa.String(10))
        batch_op.create_check_constraint("ck_posts_tag", PREFIX_CHECK.replace("prefix", "tag"))
        batch_op.create_index("ix_posts_tag", ["prefix"], unique=False)
