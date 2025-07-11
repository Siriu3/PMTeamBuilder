"""add version_group_id to generation_pokemon_species

Revision ID: 20250527_add_version_group_to_generation_pokemon_species
Revises: 
Create Date: 2025-05-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250527_add_version_group_to_generation_pokemon_species'
down_revision = '20250526_add_first_generation_id_to_pokemon'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('generation_pokemon_species', sa.Column('version_group_id', sa.Integer(), nullable=True))
    # 可选: 如需外键约束可取消注释
    # op.create_foreign_key('fk_generation_pokemon_species_version_group', 'generation_pokemon_species', 'version_groups', ['version_group_id'], ['id'])

def downgrade():
    op.drop_column('generation_pokemon_species', 'version_group_id')
