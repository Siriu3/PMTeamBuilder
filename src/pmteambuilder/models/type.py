from . import db

class Type(db.Model):
    __tablename__ = 'types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    name_zh_hans = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Type {self.name_zh_hans or self.name}>'
