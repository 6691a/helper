"""enable pgvector extension

Revision ID: 5b8594d0d4bb
Revises: 79063dcd634a
Create Date: 2026-01-17 13:29:48.909953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5b8594d0d4bb'
down_revision: Union[str, Sequence[str], None] = '79063dcd634a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")
