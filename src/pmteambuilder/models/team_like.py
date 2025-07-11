"""
用户点赞团队模型定义
"""
from . import db
from datetime import datetime, timezone

class TeamLike(db.Model):
    """用户点赞团队模型"""
    __tablename__ = 'team_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # 确保一个用户只能点赞同一团队一次
    __table_args__ = (db.UniqueConstraint('user_id', 'team_id', name='_user_team_uc'),)

    def __repr__(self):
        return f'<TeamLike UserID: {self.user_id}, TeamID: {self.team_id}>'
