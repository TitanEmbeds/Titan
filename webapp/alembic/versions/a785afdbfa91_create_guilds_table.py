"""Create guilds table

Revision ID: a785afdbfa91
Revises: 52e1d48f57d4
Create Date: 2017-05-30 20:08:17.451959

"""

# revision identifiers, used by Alembic.
revision = 'a785afdbfa91'
down_revision = '52e1d48f57d4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'guilds',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('unauth_users', sa.Boolean(), nullable=False, default=1),
        sa.Column('chat_links', sa.Boolean(), nullable=False, default=1),
        sa.Column('bracket_links', sa.Boolean(), nullable=False, default=1),
        sa.Column('mentions_limit', sa.Integer, nullable=False, default=11),
        sa.Column('roles', sa.Text(), nullable=False),
        sa.Column('channels', sa.Text(), nullable=False),
        sa.Column('emojis', sa.Text(), nullable=False),
        sa.Column('owner_id', sa.String(255), nullable=False),
        sa.Column('icon', sa.String(255)),
    )


def downgrade():
    op.drop_table('guilds')
