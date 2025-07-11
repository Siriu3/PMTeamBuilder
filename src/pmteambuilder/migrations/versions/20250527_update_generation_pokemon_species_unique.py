"""update unique constraint for generation_pokemon_species to triple

Revision ID: 20250527_update_generation_pokemon_species_unique
Revises: 20250527_add_version_group_to_generation_pokemon_species
Create Date: 2025-05-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250527_update_generation_pokemon_species_unique'
down_revision = '20250527_add_version_group_to_generation_pokemon_species'
branch_labels = None
depends_on = None

def upgrade():
    # 直接创建新主键，指定主键名
    with op.batch_alter_table('generation_pokemon_species') as batch_op:
        batch_op.create_primary_key('generation_pokemon_species_pk', ['generation_id', 'pokemon_species_id', 'version_group_id'])

def downgrade():
    with op.batch_alter_table('generation_pokemon_species') as batch_op:
        batch_op.create_primary_key('generation_pokemon_species_pk', ['generation_id', 'pokemon_species_id'])
