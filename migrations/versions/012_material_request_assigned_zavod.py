"""Add assigned_zavod_id to material_requests table

Revision ID: 012
Revises: 011
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('material_requests', sa.Column('assigned_zavod_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_material_requests_assigned_zavod',
        'material_requests', 'zavods',
        ['assigned_zavod_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_material_requests_assigned_zavod', 'material_requests', type_='foreignkey')
    op.drop_column('material_requests', 'assigned_zavod_id')
