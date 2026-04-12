"""Add ADMIN_PENDING status to MaterialRequestStatus

Revision ID: 95be334201a4
Revises: 001
Create Date: 2026-04-11 11:17:10.506205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '95be334201a4'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum value to MaterialRequestStatus
    op.execute("ALTER TYPE materialrequeststatus ADD VALUE IF NOT EXISTS 'admin_pending' BEFORE 'pending'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type
    pass
