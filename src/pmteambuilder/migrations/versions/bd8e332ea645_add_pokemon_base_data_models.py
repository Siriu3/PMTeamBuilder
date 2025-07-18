"""add pokemon base data models

Revision ID: bd8e332ea645
Revises: 9381458f1928
Create Date: 2025-05-25 10:09:37.985396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd8e332ea645'
down_revision = '9381458f1928'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('abilities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('name_zh_hans', sa.String(length=100), nullable=True),
    sa.Column('description_en', sa.Text(), nullable=True),
    sa.Column('description_zh_hans', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('generations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('name_zh_hans', sa.String(length=100), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('description_en', sa.Text(), nullable=True),
    sa.Column('description_zh_hans', sa.Text(), nullable=True),
    sa.Column('sprite', sa.String(length=255), nullable=True),
    sa.Column('generation', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('moves',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('name_zh_hans', sa.String(length=100), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('power', sa.Integer(), nullable=True),
    sa.Column('accuracy', sa.Integer(), nullable=True),
    sa.Column('pp', sa.Integer(), nullable=True),
    sa.Column('description_en', sa.Text(), nullable=True),
    sa.Column('description_zh_hans', sa.Text(), nullable=True),
    sa.Column('generation', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('pokemon_species',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('name_zh_hans', sa.String(length=100), nullable=True),
    sa.Column('gender_rate', sa.Integer(), nullable=True),
    sa.Column('generation', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('name_zh_hans', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('version_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('generation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['generation_id'], ['generations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('version_groups')
    op.drop_table('types')
    op.drop_table('pokemon_species')
    op.drop_table('moves')
    op.drop_table('items')
    op.drop_table('generations')
    op.drop_table('abilities')
    # ### end Alembic commands ###
