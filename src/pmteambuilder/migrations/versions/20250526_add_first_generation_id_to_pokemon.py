"""add first_generation_id to pokemon

Revision ID: 20250526_add_first_generation_id_to_pokemon
Revises: 7c2392d4889c
Create Date: 2025-05-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250526_add_first_generation_id_to_pokemon'
down_revision = '7c2392d4889c'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('pokemon', sa.Column('first_generation_id', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('pokemon', 'first_generation_id')
