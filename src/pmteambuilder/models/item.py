from . import db
from sqlalchemy import Index

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    name_zh_hans = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    description_en = db.Column(db.Text, nullable=True)
    description_zh_hans = db.Column(db.Text, nullable=True)
    sprite = db.Column(db.String(255), nullable=True)
    generation = db.Column(db.String(20), nullable=True)

    __table_args__ = (
        Index('ix_item_name_zh_hans', 'name_zh_hans'),
        Index('ix_item_category', 'category'),
        Index('ix_item_generation', 'generation'),
    )

    def __repr__(self):
        return f'<Item {self.name_zh_hans or self.name}>'
