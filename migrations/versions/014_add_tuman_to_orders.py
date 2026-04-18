"""add tuman to orders

Revision ID: 014_add_tuman
Revises: bec2613623ef
Create Date: 2026-04-18 12:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014_add_tuman'
down_revision = 'bec2613623ef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('tuman', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'tuman')
