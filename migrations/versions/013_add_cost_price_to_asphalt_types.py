"""Add cost_price_per_m2 to asphalt_types table

Revision ID: 013
Revises: 012
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('asphalt_types', sa.Column('cost_price_per_m2', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('asphalt_types', 'cost_price_per_m2')
