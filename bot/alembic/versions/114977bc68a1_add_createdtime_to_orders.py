"""add_createdtime_to_orders

Revision ID: 114977bc68a1
Revises: a3f9ee542135
Create Date: 2025-05-29 17:08:13.055387

"""

from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "114977bc68a1"
down_revision: Union[str, None] = "a3f9ee542135"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("orders", sa.Column("created_at", sa.DateTime(), nullable=True))
    # ### end Alembic commands ###
    now = datetime.now(timezone.utc)
    op.execute(sa.text("UPDATE orders SET created_at = :now").bindparams(now=now))

    # Изменяем столбец на NOT NULL после заполнения всех записей
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column("created_at", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("orders", "created_at")
    # ### end Alembic commands ###
