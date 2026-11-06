"""baseline: extensiones de PostgreSQL

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-05

Las tablas del modelo de datos se crean a partir del Módulo 2.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # gen_random_uuid() es nativo en PG13+, pgcrypto se usará para cifrado de columnas.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")  # búsqueda difusa de alimentos


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
