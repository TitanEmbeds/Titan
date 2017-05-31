"""Create keyvalue table

Revision ID: 347cb289508e
Revises: a785afdbfa91
Create Date: 2017-05-30 20:16:22.543157

"""

# revision identifiers, used by Alembic.
revision = '347cb289508e'
down_revision = 'a785afdbfa91'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'keyvalue_properties',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text()),
        sa.Column('expiration', sa.TIMESTAMP),
    )


def downgrade():
    op.drop_table('keyvalue_properties')
