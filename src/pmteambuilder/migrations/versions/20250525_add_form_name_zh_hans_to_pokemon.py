"""add form_name_zh_hans to pokemon

Revision ID: 20250525
Revises: 8a9e5001f68c
Create Date: 2025-05-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250525'
down_revision = '8a9e5001f68c'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('pokemon', sa.Column('form_name_zh_hans', sa.String(length=100), nullable=True))

def downgrade():
    op.drop_column('pokemon', 'form_name_zh_hans')
