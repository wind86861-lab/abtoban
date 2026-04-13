"""Add zavod table, zavod_hududlar join table, viloyat/tuman/tafsif to regions, zavod_id to users

Revision ID: 005
Revises: 004
Create Date: 2026-04-13 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add viloyat / tuman / tafsif to regions
    op.add_column('regions', sa.Column('viloyat', sa.String(100), nullable=True))
    op.add_column('regions', sa.Column('tuman', sa.String(100), nullable=True))
    op.add_column('regions', sa.Column('tafsif', sa.Text(), nullable=True))

    # 2. Create zavods table
    op.create_table(
        'zavods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tafsif', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_zavods_name', 'zavods', ['name'], unique=True)

    # 3. Create zavod_hududlar join table
    op.create_table(
        'zavod_hududlar',
        sa.Column('zavod_id', sa.Integer(), nullable=False),
        sa.Column('hudud_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['zavod_id'], ['zavods.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hudud_id'], ['regions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('zavod_id', 'hudud_id'),
    )

    # 4. Add zavod_id to users
    op.add_column('users', sa.Column('zavod_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_zavod_id', 'users', 'zavods', ['zavod_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_users_zavod_id', 'users', type_='foreignkey')
    op.drop_column('users', 'zavod_id')
    op.drop_table('zavod_hududlar')
    op.drop_index('ix_zavods_name', table_name='zavods')
    op.drop_table('zavods')
    op.drop_column('regions', 'tafsif')
    op.drop_column('regions', 'tuman')
    op.drop_column('regions', 'viloyat')
