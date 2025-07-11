from . import db
from sqlalchemy import Index

class Ability(db.Model):
    __tablename__ = 'abilities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    name_zh_hans = db.Column(db.String(100), nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    description_zh_hans = db.Column(db.Text, nullable=True)
    # 可扩展 generation_id 等字段

    __table_args__ = (
        Index('ix_ability_name_zh_hans', 'name_zh_hans'),
    )

    def __repr__(self):
        return f'<Ability {self.name_zh_hans or self.name}>'
