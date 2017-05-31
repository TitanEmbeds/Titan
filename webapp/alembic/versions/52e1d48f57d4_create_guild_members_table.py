"""Create guild_members table

Revision ID: 52e1d48f57d4
Revises: de55c5fc3c49
Create Date: 2017-05-30 20:01:55.380143

"""

# revision identifiers, used by Alembic.
revision = '52e1d48f57d4'
down_revision = 'de55c5fc3c49'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'guild_members',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('discriminator', sa.Integer, nullable=False),
        sa.Column('nickname', sa.String(255)),
        sa.Column('avatar', sa.String(255)),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('banned', sa.Boolean(), nullable=False),
        sa.Column('roles', sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table('guild_members')
