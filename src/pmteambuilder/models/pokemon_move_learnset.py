from . import db
from sqlalchemy import Index

class PokemonMoveLearnset(db.Model):
    __tablename__ = 'pokemon_move_learnset'
    id = db.Column(db.Integer, primary_key=True)
    pokemon_species_id = db.Column(db.Integer, db.ForeignKey('pokemon_species.id'), nullable=False)
    move_id = db.Column(db.Integer, db.ForeignKey('moves.id'), nullable=False)
    version_group_id = db.Column(db.Integer, db.ForeignKey('version_groups.id'), nullable=False)
    learn_method = db.Column(db.String(50), nullable=False)  # level-up, machine, egg, tutor, etc.
    level = db.Column(db.Integer, nullable=True)  # 学会等级

    __table_args__ = (
        db.UniqueConstraint('pokemon_species_id', 'move_id', 'version_group_id', 'learn_method', 'level', name='uq_pokemon_move_learnset'),
        Index('ix_learnset_pokemon_species_version_group', 'pokemon_species_id', 'version_group_id'),
        Index('ix_learnset_move_id', 'move_id'),
    )

    def __repr__(self):
        return f'<Learnset species={self.pokemon_species_id} move={self.move_id} vg={self.version_group_id} method={self.learn_method} lvl={self.level}>'
