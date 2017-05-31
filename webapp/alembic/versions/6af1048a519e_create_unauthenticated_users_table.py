"""Create unauthenticated users table

Revision ID: 6af1048a519e
Revises: 33c7a4b6c3e7
Create Date: 2017-05-30 20:27:30.232927

"""

# revision identifiers, used by Alembic.
revision = '6af1048a519e'
down_revision = '33c7a4b6c3e7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'unauthenticated_users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('discriminator', sa.Integer, nullable=False),
        sa.Column('user_key', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(255), nullable=False),
        sa.Column('last_timestamp', sa.TIMESTAMP, nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
    )


def downgrade():
    op.drop_table('unauthenticated_users')
