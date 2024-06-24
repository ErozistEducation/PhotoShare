"""Init

Revision ID: 4b1e280e7895
Revises: 9fc0fc6a1ce7
Create Date: 2024-06-25 01:47:49.127837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b1e280e7895'
down_revision: Union[str, None] = '9fc0fc6a1ce7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
