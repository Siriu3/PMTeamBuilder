"""
举报模型定义
"""
from datetime import datetime, timezone
from . import db

class Report(db.Model):
    """举报模型"""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'handled'
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    handled_at = db.Column(db.DateTime, nullable=True)
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(20), nullable=True)  # 'warn', 'delete', 'ignore'
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Report {self.id} (Team: {self.team_id}, Status: {self.status})>'

    def to_dict(self):
        """将 Report 对象转换为字典格式"""
        # 需要导入 User 和 Team 模型来获取相关信息
        from .user import User # 临时导入，或者确保在文件顶部导入
        from .team import Team # 临时导入，或者确保在文件顶部导入

        reporter_username = None
        if self.reporter_id:
            reporter = User.query.get(self.reporter_id)
            if reporter:
                reporter_username = reporter.username

        team_name = None
        if self.team_id:
            team = Team.query.get(self.team_id)
            if team:
                team_name = team.name

        handler_username = None
        if self.handler_id:
            handler = User.query.get(self.handler_id)
            if handler:
                handler_username = handler.username

        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'reporter_username': reporter_username, # 添加举报者用户名
            'team_id': self.team_id,
            'team_name': team_name, # 添加被举报团队名称
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'handled_at': self.handled_at.isoformat() if self.handled_at else None,
            'handler_id': self.handler_id,
            'handler_username': handler_username, # 添加处理者用户名
            'action': self.action, # 处理动作
            'note': self.note,   # 处理评论 (对应 report_service 中的 note)
            # 注意：report_service 中 resolve_report 和 reject_report 使用了 resolved_at 和 resolution_note
            # 模型中使用的是 handled_at 和 note，这里 to_dict 应该与模型字段对应。
            # 前端 AdminReportManagement.vue 期望的字段包括 handler_username, action, comment。
            # comment 字段在模型中是 note。
            'comment': self.note # 对应前端期望的 comment 字段
        }
