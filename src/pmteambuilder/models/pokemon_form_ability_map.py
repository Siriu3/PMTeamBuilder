from . import db
from sqlalchemy import Index

class PokemonFormAbilityMap(db.Model):
    __tablename__ = 'pokemon_form_ability_map'
    id = db.Column(db.Integer, primary_key=True)
    # Corresponds to the specific Pokemon form's ID in the 'pokemon' table
    pokemon_form_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    # Corresponds to the ability's ID in the 'abilities' table
    ability_id = db.Column(db.Integer, db.ForeignKey('abilities.id'), nullable=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    # slot = db.Column(db.Integer, nullable=True) # PokeAPI provides 'slot', could be useful

    pokemon_form = db.relationship('Pokemon', backref=db.backref('form_abilities_map', lazy='dynamic'))
    ability = db.relationship('Ability', backref=db.backref('in_pokemon_forms_map', lazy='dynamic'))

    __table_args__ = (
       db.UniqueConstraint('pokemon_form_id', 'ability_id', 'is_hidden', name='uq_pokemon_form_ability_map_entry'),
        Index('ix_pokemonformabilitymap_pokemon_form_id', 'pokemon_form_id'),
        Index('ix_pokemonformabilitymap_ability_id', 'ability_id'),
    )

    def __repr__(self):
        return f'<PokemonFormAbilityMap form_id={self.pokemon_form_id} ability_id={self.ability_id} hidden={self.is_hidden}>'
