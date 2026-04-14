"""Add location fields to market_orders

Revision ID: 009
Revises: 008
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('market_orders', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('market_orders', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('market_orders', sa.Column('address', sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column('market_orders', 'address')
    op.drop_column('market_orders', 'longitude')
    op.drop_column('market_orders', 'latitude')
