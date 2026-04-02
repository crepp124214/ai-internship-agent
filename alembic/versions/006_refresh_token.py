"""add refresh_token_hash column to users"""

from alembic import op
import sqlalchemy as sa

revision = '006_refresh_token'
down_revision = '006_tracker_advice_mode'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('refresh_token_hash', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('users', 'refresh_token_hash')
