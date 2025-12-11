from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


revision: str = 'add _reports_table_001'
down_revision: Union[str, Sequence[str], None] = '093acc532851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('reports',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('report_at', sa.DateTime(), nullable=False),
        sa.Column('order_id', sa.Uuid(), nullable=False),
        sa.Column('count_product', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('reports')

