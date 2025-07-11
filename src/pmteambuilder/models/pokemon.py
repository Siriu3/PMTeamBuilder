from . import db
from sqlalchemy import Index

class Pokemon(db.Model):
    __tablename__ = 'pokemon'
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('pokemon_species.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    form_name = db.Column(db.String(100), nullable=True)  # 形态名，如mega、阿罗拉等
    form_name_zh_hans = db.Column(db.String(100), nullable=True)  # 形态中文译名
    is_default = db.Column(db.Boolean, default=True)
    sprite = db.Column(db.String(255), nullable=True)
    type_1 = db.Column(db.String(50), nullable=True)
    type_2 = db.Column(db.String(50), nullable=True)
    base_hp = db.Column(db.Integer, nullable=True)
    base_atk = db.Column(db.Integer, nullable=True)
    base_def = db.Column(db.Integer, nullable=True)
    base_spa = db.Column(db.Integer, nullable=True)
    base_spd = db.Column(db.Integer, nullable=True)
    base_spe = db.Column(db.Integer, nullable=True)
    first_generation_id = db.Column(db.Integer, nullable=True)  # 形态初登场世代
    # 可扩展 abilities、form_order、is_mega、is_regional、is_gmax 等

    __table_args__ = (
        Index('ix_pokemon_species_id', 'species_id'),
        Index('ix_pokemon_name', 'name'),
        Index('ix_pokemon_first_generation_id', 'first_generation_id'),
    )

    def __repr__(self):
        return f'<Pokemon {self.name} (form: {self.form_name or "default"})>'
