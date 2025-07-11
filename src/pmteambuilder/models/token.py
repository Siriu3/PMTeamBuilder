"""
Token模型定义
"""
from datetime import datetime, timezone
from . import db

class Token(db.Model):
    """令牌模型，用于存储刷新令牌"""
    __tablename__ = 'tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(500), nullable=False, unique=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'refresh', 'access', 'verification'等
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    revoked = db.Column(db.Boolean, default=False)
    revoked_at = db.Column(db.DateTime, nullable=True)

    # 关系
    user = db.relationship('User', backref=db.backref('tokens', lazy=True))

    def __repr__(self):
        return f'<Token {self.id} (User: {self.user_id}, Type: {self.token_type})>'
