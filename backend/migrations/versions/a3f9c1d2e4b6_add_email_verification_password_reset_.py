"""add email verification, password reset, and guest columns to users

Revision ID: a3f9c1d2e4b6
Revises: df13e07c2e70
Create Date: 2026-07-16 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3f9c1d2e4b6"
down_revision = "df13e07c2e70"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "is_email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users", sa.Column("email_verification_token_hash", sa.String(), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_token_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "users", sa.Column("password_reset_token_hash", sa.String(), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_token_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_guest", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade():
    op.drop_column("users", "is_guest")
    op.drop_column("users", "password_reset_token_expires_at")
    op.drop_column("users", "password_reset_token_hash")
    op.drop_column("users", "email_verification_token_expires_at")
    op.drop_column("users", "email_verification_token_hash")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "is_email_verified")
