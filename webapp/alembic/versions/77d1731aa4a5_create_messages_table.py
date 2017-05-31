"""Create messages table

Revision ID: 77d1731aa4a5
Revises: 347cb289508e
Create Date: 2017-05-30 20:19:04.713841

"""

# revision identifiers, used by Alembic.
revision = '77d1731aa4a5'
down_revision = '347cb289508e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('guild_id', sa.String(255), nullable=False),
        sa.Column('channel_id', sa.String(255), nullable=False),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP, nullable=False),
        sa.Column('edited_timestamp', sa.TIMESTAMP),
        sa.Column('mentions', sa.Text()),
        sa.Column('attachments', sa.Text()),
    )


def downgrade():
    op.drop_table('messages')
