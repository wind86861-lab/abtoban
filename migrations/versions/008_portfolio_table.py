"""Add portfolio table

Revision ID: 008
Revises: 007
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title_uz', sa.String(500), nullable=False),
        sa.Column('title_ru', sa.String(500), nullable=False),
        sa.Column('title_en', sa.String(500), nullable=False),
        sa.Column('description_uz', sa.Text(), nullable=True),
        sa.Column('description_ru', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('client_name', sa.String(255), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('images', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('portfolios')
