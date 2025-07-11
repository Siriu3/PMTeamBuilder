"""
用户模型定义
"""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    # 关系
    teams = db.relationship('Team', back_populates='creator', lazy=True)
    favorites = db.relationship('Team', secondary='user_favorites', lazy='subquery',
                               backref=db.backref('favorited_by', lazy=True))
    reports = db.relationship('Report', backref='reporter', lazy=True, foreign_keys='Report.reporter_id')
    handled_reports = db.relationship('Report', backref='handler', lazy=True, foreign_keys='Report.handler_id')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

# 用户收藏关联表
user_favorites = db.Table('user_favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), primary_key=True),
    db.Column('created_at', db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
)
