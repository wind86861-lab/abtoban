"""Add latitude/longitude to orders table

Revision ID: 011
Revises: 010
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('orders', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'longitude')
    op.drop_column('orders', 'latitude')
