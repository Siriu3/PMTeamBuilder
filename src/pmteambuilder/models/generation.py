from . import db

class Generation(db.Model):
    __tablename__ = 'generations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # 可扩展更多字段

    def __repr__(self):
        return f'<Generation {self.name}>'
