"""seed default admin and user

Revision ID: 082f2ed10449
Revises: b14fee0a3cb4
Create Date: 2026-04-05 17:43:09.418139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '082f2ed10449'
down_revision: Union[str, Sequence[str], None] = 'b14fee0a3cb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

users_table = table(
    "users",
    column("id", sa.Integer),
    column("email", sa.String(length=255)),
    column("full_name", sa.String(length=255)),
    column("hashed_password", sa.String(length=255)),
    column("is_admin", sa.Boolean),
)

accounts_table = table(
    "accounts",
    column("id", sa.Integer),
    column("user_id", sa.Integer),
    column("external_id", sa.Integer),
    column("balance", sa.Numeric(12, 2)),
)


def upgrade() -> None:
    admin_password_hash = "$2b$12$E8yWZJ3/1R4v91l/xgZObOm68Uk4KXVaPDLbxljSFKTYE6gND.96S"
    user_password_hash = "$2b$12$z1Dm78Di/1kOPfM6titrCupzEZRH7NQlZ.z747HxwYAxjlgRtijBq"

    op.bulk_insert(
        users_table,
        [
            {
                "id": 1,
                "email": "admin@example.com",
                "full_name": "Test Admin",
                "hashed_password": admin_password_hash,
                "is_admin": True,
            },
            {
                "id": 2,
                "email": "user@example.com",
                "full_name": "Test User",
                "hashed_password": user_password_hash,
                "is_admin": False,
            },
        ],
    )

    op.bulk_insert(
        accounts_table,
        [
            {
                "id": 1,
                "user_id": 2,
                "external_id": 1,
                "balance": 0.00,
            },
        ],
    )

    op.execute(
        "SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users), true)"
    )
    op.execute(
        "SELECT setval('accounts_id_seq', (SELECT COALESCE(MAX(id), 1) FROM accounts), true)"
    )
    op.execute(
        "SELECT setval('payments_id_seq', (SELECT COALESCE(MAX(id), 1) FROM payments), true)"
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM accounts
            WHERE user_id IN (
                SELECT id
                FROM users
                WHERE email IN ('admin@example.com', 'user@example.com')
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            DELETE FROM users
            WHERE email IN ('admin@example.com', 'user@example.com')
            """
        )
    )
