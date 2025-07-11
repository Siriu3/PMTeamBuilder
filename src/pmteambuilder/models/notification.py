"""
通知模型定义
"""
from datetime import datetime, timezone
from . import db

class Notification(db.Model):
    """通知模型"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False) # Notification type (e.g., report_handled, team_rejected)
    related_id = db.Column(db.Integer, nullable=True) # ID of related entity (e.g., report_id, team_id)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_read = db.Column(db.Boolean, default=False)

    # Define relationship to User (optional, but good practice)
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id} (User: {self.user_id}, Type: {self.type}, Read: {self.is_read})>'

    def to_dict(self):
        """将 Notification 对象转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'related_id': self.related_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read,
        } 