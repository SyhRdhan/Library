"""Add role column to user table

Revision ID: 9ed19cde51b2
Revises: 
Create Date: 2025-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '9ed19cde51b2'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Cek jika kolom sudah ada
    bind = op.get_bind()
    inspector = inspect(bind.engine)
    columns = inspector.get_columns('user')
    if 'role' not in [c['name'] for c in columns]:
        op.add_column('user', sa.Column('role', sa.String(length=20), nullable=True))
        op.execute("UPDATE user SET role = 'user'")
        op.alter_column('user', 'role', nullable=False)
    else:
        # Jika sudah ada, pastikan default
        op.execute("UPDATE user SET role = COALESCE(role, 'user')")

def downgrade():
    # Hapus kolom untuk rollback
    op.drop_column('user', 'role')