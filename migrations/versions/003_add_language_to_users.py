"""Add language column to users

Revision ID: 003_language
Revises: 95be334201a4
Create Date: 2026-04-12 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003_language'
down_revision: Union[str, None] = '95be334201a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('language', sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'language')
