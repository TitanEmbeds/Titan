"""Create cosmetics table

Revision ID: de55c5fc3c49
Revises: 906a48cc55d0
Create Date: 2017-05-30 19:51:29.692001

"""

# revision identifiers, used by Alembic.
revision = 'de55c5fc3c49'
down_revision = '906a48cc55d0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'cosmetics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('css', sa.Boolean(), nullable=False),
    )


def downgrade():
    op.drop_table('cosmetics')
