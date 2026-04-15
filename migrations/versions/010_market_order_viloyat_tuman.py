"""Add viloyat and tuman fields to market_orders

Revision ID: 010
Revises: 009
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('market_orders', sa.Column('viloyat', sa.String(200), nullable=True))
    op.add_column('market_orders', sa.Column('tuman', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('market_orders', 'tuman')
    op.drop_column('market_orders', 'viloyat')
