"""Add user_hududlar M2M table for multi-region users

Revision ID: 006
Revises: 005
Create Date: 2026-04-13 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_hududlar',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hudud_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hudud_id'], ['regions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'hudud_id'),
    )


def downgrade() -> None:
    op.drop_table('user_hududlar')
