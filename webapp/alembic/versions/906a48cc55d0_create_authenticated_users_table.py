"""create authenticated_users table

Revision ID: 906a48cc55d0
Revises:
Create Date: 2017-05-30 19:47:38.457143

"""

# revision identifiers, used by Alembic.
revision = '906a48cc55d0'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'authenticated_users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('last_timestamp', sa.TIMESTAMP, nullable=False),
    )


def downgrade():
    op.drop_table('authenticated_users')
