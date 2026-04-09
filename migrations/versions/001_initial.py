"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "asphalt_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price_per_m2", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column(
            "role",
            sa.Enum(
                "super_admin",
                "admin",
                "helper_admin",
                "master",
                "usta",
                "zavod",
                "shofer",
                "klient",
                name="userrole",
            ),
            nullable=False,
        ),
        sa.Column("region_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(length=20), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("master_id", sa.Integer(), nullable=True),
        sa.Column("usta_id", sa.Integer(), nullable=True),
        sa.Column("zavod_id", sa.Integer(), nullable=True),
        sa.Column("region_id", sa.Integer(), nullable=True),
        sa.Column("asphalt_type_id", sa.Integer(), nullable=True),
        sa.Column("client_name", sa.String(length=200), nullable=False),
        sa.Column("client_phone", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("area_m2", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("area_tonnes", sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column("total_price", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("advance_paid", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("discount", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("debt", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("usta_wage", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("usta_wage_note", sa.String(length=500), nullable=True),
        sa.Column("master_commission", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "new", "confirmed", "in_work", "done", "cancelled", name="orderstatus"
            ),
            nullable=False,
        ),
        sa.Column("work_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usta_assignment_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asphalt_type_id"], ["asphalt_types.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["master_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
        sa.ForeignKeyConstraint(["usta_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["zavod_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index("ix_orders_status", "orders", ["status"], unique=False)

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column(
            "expense_type",
            sa.Enum(
                "material", "delivery", "wage", "bardyor", "extra", name="expensetype"
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "material_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("usta_id", sa.Integer(), nullable=False),
        sa.Column("zavod_id", sa.Integer(), nullable=True),
        sa.Column("amount_tonnes", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("material_price", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("delivery_price", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("extra_cost", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "priced", "delivered", name="materialrequeststatus"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["usta_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["zavod_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("material_requests")
    op.drop_table("expenses")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
    op.drop_table("asphalt_types")
    op.drop_table("regions")
    op.execute("DROP TYPE IF EXISTS materialrequeststatus")
    op.execute("DROP TYPE IF EXISTS expensetype")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
