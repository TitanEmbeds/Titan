"""Create user css table

Revision ID: 32a4d2d7b85f
Revises: 6af1048a519e
Create Date: 2017-05-30 20:30:26.148504

"""

# revision identifiers, used by Alembic.
revision = '32a4d2d7b85f'
down_revision = '6af1048a519e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'user_css',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('css', sa.Text()),
    )


def downgrade():
    op.drop_table('user_css')
