"""
敏感词模型定义
"""
from datetime import datetime, timezone
from . import db

class SensitiveWord(db.Model):
    """敏感词模型"""
    __tablename__ = 'sensitive_words'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 关系
    creator = db.relationship('User', backref='created_sensitive_words', lazy=True)

    def to_dict(self):
        """将敏感词对象转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }


    def __repr__(self):
        return f'<SensitiveWord {self.content}>'
