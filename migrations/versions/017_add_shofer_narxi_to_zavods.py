"""Add shofer_narxi column to zavods table

Revision ID: 017
Revises: 016
Create Date: 2026-04-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '017'
down_revision: Union[str, None] = '016_viloyat_tuman'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'zavods',
        sa.Column('shofer_narxi', sa.Numeric(14, 2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('zavods', 'shofer_narxi')
