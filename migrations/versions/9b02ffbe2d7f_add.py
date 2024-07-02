"""add

Revision ID: 9b02ffbe2d7f
Revises: 
Create Date: 2024-07-01 16:54:37.970258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b02ffbe2d7f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_photos_id'), 'photos', ['id'], unique=False)
    op.create_index(op.f('ix_photos_url'), 'photos', ['url'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_photos_url'), table_name='photos')
    op.drop_index(op.f('ix_photos_id'), table_name='photos')
    # ### end Alembic commands ###
