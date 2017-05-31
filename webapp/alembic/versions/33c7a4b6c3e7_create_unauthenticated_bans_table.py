"""Create unauthenticated bans table

Revision ID: 33c7a4b6c3e7
Revises: 77d1731aa4a5
Create Date: 2017-05-30 20:23:44.618429

"""

# revision identifiers, used by Alembic.
revision = '33c7a4b6c3e7'
down_revision = '77d1731aa4a5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'unauthenticated_bans',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(255), nullable=False),
        sa.Column('last_username', sa.String(255), nullable=False),
        sa.Column('last_discriminator', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP, nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('lifter_id', sa.String(255)),
        sa.Column('placer_id', sa.String(255), nullable=False),
    )


def downgrade():
    op.drop_table('unauthenticated_bans')
