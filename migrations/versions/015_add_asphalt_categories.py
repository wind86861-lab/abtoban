"""add asphalt categories and subcategories

Revision ID: 015_add_categories
Revises: 014_add_tuman
Create Date: 2026-04-18 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015_add_categories'
down_revision = '014_add_tuman'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create asphalt_categories table
    op.create_table(
        'asphalt_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create asphalt_subcategories table
    op.create_table(
        'asphalt_subcategories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['category_id'], ['asphalt_categories.id'], ondelete='CASCADE')
    )
    
    # Add subcategory_id to asphalt_types
    op.add_column('asphalt_types', sa.Column('subcategory_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_asphalt_types_subcategory',
        'asphalt_types', 'asphalt_subcategories',
        ['subcategory_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_asphalt_types_subcategory', 'asphalt_types', type_='foreignkey')
    op.drop_column('asphalt_types', 'subcategory_id')
    op.drop_table('asphalt_subcategories')
    op.drop_table('asphalt_categories')
