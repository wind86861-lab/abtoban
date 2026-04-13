"""Add marketplace tables (categories, products, cart, market_orders)

Revision ID: 007
Revises: 006
Create Date: 2026-04-13 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_uz', sa.String(length=255), nullable=False),
        sa.Column('name_ru', sa.String(length=255), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('image', sa.String(length=500), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name_uz', sa.String(length=500), nullable=False),
        sa.Column('name_ru', sa.String(length=500), nullable=False),
        sa.Column('name_en', sa.String(length=500), nullable=False),
        sa.Column('description_uz', sa.Text(), nullable=True),
        sa.Column('description_ru', sa.Text(), nullable=True),
        sa.Column('description_en', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_value', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('discount_type', sa.String(length=20), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('images', sa.Text(), nullable=True),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create market_orders table
    op.create_table(
        'market_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=50), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.Enum('new', 'processing', 'completed', 'cancelled', name='marketorderstatus'), nullable=False, server_default='new'),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create market_order_items table
    op.create_table(
        'market_order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(length=500), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('image', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['market_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('market_order_items')
    op.drop_table('market_orders')
    op.drop_table('cart_items')
    op.drop_table('products')
    op.drop_table('categories')
    op.execute('DROP TYPE marketorderstatus')
