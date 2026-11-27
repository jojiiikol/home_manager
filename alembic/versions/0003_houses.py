"""Дома, информация о доме и участники."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "houses_table",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("login", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login", name="uq_houses_table_login"),
    )
    op.create_table(
        "houses_info_table",
        sa.Column("house_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("house_id"),
        sa.ForeignKeyConstraint(["house_id"], ["houses_table.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "houses_participants_table",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("house_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "member",
                native_enum=False,
                create_constraint=True,
                name="house_participant_role",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "blocked",
                "left",
                native_enum=False,
                create_constraint=True,
                name="house_participant_status",
            ),
            nullable=False,
        ),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["house_id"], ["houses_table.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users_table.id"]),
        sa.UniqueConstraint(
            "house_id", "user_id", name="uq_houses_participants_house_user"
        ),
    )
    op.create_index(
        "ix_houses_participants_table_user_id", "houses_participants_table", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_houses_participants_table_user_id", table_name="houses_participants_table"
    )
    op.drop_table("houses_participants_table")
    op.drop_table("houses_info_table")
    op.drop_table("houses_table")
