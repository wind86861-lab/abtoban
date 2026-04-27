"""add payment_transfers table

Revision ID: 019_payment_transfers
Revises: 018_app_settings
Create Date: 2026-04-27 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "019_payment_transfers"
down_revision: Union[str, None] = "018_app_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "usta_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("usta_collected", sa.Numeric(15, 2), nullable=False),
        sa.Column("usta_wage_taken", sa.Numeric(15, 2), nullable=False),
        sa.Column("usta_sent", sa.Numeric(15, 2), nullable=False),
        sa.Column(
            "usta_submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("zavod_received", sa.Numeric(15, 2), nullable=True),
        sa.Column("zavod_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "zavod_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(30),
            server_default="usta_submitted",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("payment_transfers")
