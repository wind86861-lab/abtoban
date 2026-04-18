"""add viloyat and tuman tables

Revision ID: 016_viloyat_tuman
Revises: 015_add_categories
Create Date: 2026-04-18 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '016_viloyat_tuman'
down_revision = '015_add_categories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'viloyats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'tumans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('viloyat_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['viloyat_id'], ['viloyats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tumans_viloyat_id', 'tumans', ['viloyat_id'])

    # User FKs
    op.add_column('users', sa.Column('viloyat_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('tuman_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_viloyat', 'users', 'viloyats', ['viloyat_id'], ['id'])
    op.create_foreign_key('fk_users_tuman', 'users', 'tumans', ['tuman_id'], ['id'])
    op.create_index('ix_users_viloyat_id', 'users', ['viloyat_id'])
    op.create_index('ix_users_tuman_id', 'users', ['tuman_id'])

    # Order FKs
    op.add_column('orders', sa.Column('viloyat_id', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('tuman_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_orders_viloyat', 'orders', 'viloyats', ['viloyat_id'], ['id'])
    op.create_foreign_key('fk_orders_tuman', 'orders', 'tumans', ['tuman_id'], ['id'])
    op.create_index('ix_orders_viloyat_id', 'orders', ['viloyat_id'])
    op.create_index('ix_orders_tuman_id', 'orders', ['tuman_id'])


def downgrade() -> None:
    op.drop_index('ix_orders_tuman_id', table_name='orders')
    op.drop_index('ix_orders_viloyat_id', table_name='orders')
    op.drop_constraint('fk_orders_tuman', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_viloyat', 'orders', type_='foreignkey')
    op.drop_column('orders', 'tuman_id')
    op.drop_column('orders', 'viloyat_id')

    op.drop_index('ix_users_tuman_id', table_name='users')
    op.drop_index('ix_users_viloyat_id', table_name='users')
    op.drop_constraint('fk_users_tuman', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_viloyat', 'users', type_='foreignkey')
    op.drop_column('users', 'tuman_id')
    op.drop_column('users', 'viloyat_id')

    op.drop_index('ix_tumans_viloyat_id', table_name='tumans')
    op.drop_table('tumans')
    op.drop_table('viloyats')
