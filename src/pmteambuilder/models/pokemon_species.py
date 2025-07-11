from . import db
from sqlalchemy import Index

generation_pokemon_species = db.Table(
    'generation_pokemon_species',
    db.Column('generation_id', db.Integer, db.ForeignKey('generations.id'), primary_key=True),
    db.Column('pokemon_species_id', db.Integer, db.ForeignKey('pokemon_species.id'), primary_key=True),
    db.Column('version_group_id', db.Integer, nullable=True, primary_key=True),  # 新增，三元组唯一
    # __table_args__ 不能直接用于 db.Table，需用迁移脚本实现唯一约束
)

class PokemonSpecies(db.Model):
    __tablename__ = 'pokemon_species'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    name_zh_hans = db.Column(db.String(100), nullable=True)
    gender_rate = db.Column(db.Integer, nullable=True)
    # 多对多世代
    generations = db.relationship('Generation', secondary=generation_pokemon_species, backref=db.backref('pokemon_species', lazy='dynamic'))
    # 关联所有形态
    forms = db.relationship('Pokemon', backref='species', lazy=True, cascade='all, delete-orphan')

     # Add __table_args__ for indexes
    __table_args__ = (
        Index('ix_pokemonspecies_name_zh_hans', 'name_zh_hans'),
        Index('ix_pokemonspecies_name', 'name'),
        Index('ix_pokemonspecies_id', 'id'),
    )

    def __repr__(self):
        return f'<PokemonSpecies {self.name_zh_hans or self.name}>'
