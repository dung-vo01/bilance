"""add contacts table and contact-related notification types

Revision ID: b7c2e9a41f3d
Revises: a3f9c1d2e4b6
Create Date: 2026-07-17 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7c2e9a41f3d"
down_revision = "a3f9c1d2e4b6"
branch_labels = None
depends_on = None


def upgrade():
    # NotificationType is persisted by enum *name* (matching every existing
    # member, e.g. GROUP_INVITATION), not by .value - these must be uppercase.
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'CONTACT_REQUEST'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'CONTACT_ACCEPTED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'CONTACT_DECLINED'")

    op.create_table(
        "contacts",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "contact_id", name="uq_contact_pair"),
    )


def downgrade():
    op.drop_table("contacts")
    # Postgres doesn't support removing individual enum values; the three
    # contact_* values are left in place on downgrade.
