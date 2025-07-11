from . import db
from sqlalchemy import Index

class Move(db.Model):
    __tablename__ = 'moves'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    name_zh_hans = db.Column(db.String(100), nullable=True)
    type = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    power = db.Column(db.Integer, nullable=True)
    accuracy = db.Column(db.Integer, nullable=True)
    pp = db.Column(db.Integer, nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    description_zh_hans = db.Column(db.Text, nullable=True)
    generation = db.Column(db.String(20), nullable=True)

    __table_args__ = (
        Index('ix_move_name_zh_hans', 'name_zh_hans'),
        Index('ix_move_type', 'type'),
        Index('ix_move_category', 'category'),
        Index('ix_move_generation', 'generation'),
    )

    def __repr__(self):
        return f'<Move {self.name_zh_hans or self.name}>'
