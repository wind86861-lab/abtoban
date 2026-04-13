"""Seed Uzbekistan regions (viloyatlar)

Revision ID: 004_seed_regions
Revises: 003_language
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004_seed_regions'
down_revision: Union[str, None] = '003_language'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REGIONS = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Andijon viloyati",
    "Farg'ona viloyati",
    "Namangan viloyati",
    "Samarqand viloyati",
    "Buxoro viloyati",
    "Navoiy viloyati",
    "Qashqadaryo viloyati",
    "Surxondaryo viloyati",
    "Jizzax viloyati",
    "Sirdaryo viloyati",
    "Xorazm viloyati",
    "Qoraqalpog'iston Respublikasi",
]


def upgrade() -> None:
    conn = op.get_bind()
    for name in REGIONS:
        conn.execute(
            sa.text(
                "INSERT INTO regions (name, is_active) "
                "VALUES (:name, true) ON CONFLICT (name) DO NOTHING"
            ),
            {"name": name},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for name in REGIONS:
        conn.execute(
            sa.text("DELETE FROM regions WHERE name = :name"),
            {"name": name},
        )
