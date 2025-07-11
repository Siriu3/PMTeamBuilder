from . import db

class VersionGroup(db.Model):
    __tablename__ = 'version_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    generation_id = db.Column(db.Integer, db.ForeignKey('generations.id'))
    generation = db.relationship('Generation', backref=db.backref('version_groups', lazy=True))

    def __repr__(self):
        return f'<VersionGroup {self.name}>'
