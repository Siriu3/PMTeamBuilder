"""
举报服务模块，提供举报管理功能
"""
from flask import current_app
from ..models import db, Report, Team
from datetime import datetime, timezone
from .notification_service import notification_service # Import notification service

class ReportService:
    """举报服务类"""
    
    @staticmethod
    def create_report(reporter_id, team_id, reason):
        """创建新举报"""
        # 检查团队是否存在
        team = Team.query.get(team_id)
        if not team:
            raise ValueError(f"团队ID {team_id} 不存在")
        
        # 检查是否已经举报过
        existing_report = Report.query.filter_by(
            reporter_id=reporter_id,
            team_id=team_id,
            status='pending'
        ).first()
        
        if existing_report:
            raise ValueError("您已经举报过该团队，请等待管理员处理")
        
        # 创建举报
        report = Report(
            reporter_id=reporter_id,
            team_id=team_id,
            reason=reason,
            status='pending'
        )
        
        db.session.add(report)
        db.session.commit()
        
        return report
    
    @staticmethod
    def get_reports(page=1, per_page=10, status=None):
        """获取举报列表，支持按状态筛选"""
        query = Report.query.order_by(Report.created_at.desc()) # 默认按创建时间降序
        
        if status == 'pending':
            query = query.filter_by(status='pending')
        elif status == 'handled':
            # Assuming 'resolved' and 'rejected' are handled states
            query = query.filter(Report.status.in_(['resolved', 'rejected'])) # 过滤已处理的状态
        elif status == 'resolved':
            query = query.filter_by(status='resolved')
        elif status == 'rejected':
            query = query.filter_by(status='rejected')
        # 如果 status 为 None 或空字符串，则不进行状态过滤，返回所有
        
        # 分页
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [report.to_dict() for report in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def resolve_report(report_id, admin_id, action, note=None):
        """处理举报"""
        report = Report.query.get(report_id)
        if not report:
            raise ValueError(f"举报ID {report_id} 不存在")
        
        if report.status != 'pending':
            raise ValueError("该举报已经被处理")
        
        # 更新举报状态
        report.status = 'resolved'
        report.handled_at = datetime.now(timezone.utc)
        report.handler_id = admin_id
        report.note = note
        report.action = action
        
        # 根据处理结果执行相应操作
        if action == 'delete_team':
            # 删除被举报的团队
            team = Team.query.get(report.team_id)
            if team:
                db.session.delete(team)
        elif action == 'reject_team':
            # 拒绝被举报的团队
            team = Team.query.get(report.team_id)
            if team:
                team.review_status = 'rejected'
                team.review_reason = note or "根据用户举报被拒绝"
        
        db.session.commit()

        # Create notification for the reporter
        reporter_notification_content = f"您的举报已处理：关于团队 '{team.name if team else '未知团队'}'"
        if action == 'delete_team':
            reporter_notification_content += "，团队已被删除。"
        elif action == 'reject_team':
            reporter_notification_content += "，团队已被拒绝。"
        else: # Should not happen based on admin.py logic, but for safety
             reporter_notification_content += "，处理结果未知。"

        notification_service.create_notification(
            user_id=report.reporter_id,
            type='report_handled',
            content=reporter_notification_content,
            related_id=report.id
        )

        # Create notification for the team creator if team was affected
        if action in ['delete_team', 'reject_team'] and team and team.user_id:
            team_notification_content = "您的团队 '{}' 因用户举报而被{}".format(
                team.name,
                '删除' if action == 'delete_team' else '拒绝'
            )
            notification_service.create_notification(
                user_id=team.user_id,
                type='team_affected_by_report',
                content=team_notification_content,
                related_id=team.id # Or report.id, depending on desired link
            )

        return report
    
    @staticmethod
    def reject_report(report_id, admin_id, note=None):
        """拒绝举报"""
        report = Report.query.get(report_id)
        if not report:
            raise ValueError(f"举报ID {report_id} 不存在")
        
        if report.status != 'pending':
            raise ValueError("该举报已经被处理")
        
        # 更新举报状态
        report.status = 'rejected'
        report.handled_at = datetime.now(timezone.utc)
        report.handler_id = admin_id
        report.note = note
        report.action = 'ignore'
        
        db.session.commit()

        # Create notification for the reporter for ignored report
        team = Team.query.get(report.team_id) # Get team again if needed for name after commit
        team_name = team.name if team else "未知团队"

        reporter_notification_content = f"您的举报已处理：关于团队 '{team_name}'，举报被忽略。"

        notification_service.create_notification(
            user_id=report.reporter_id,
            type='report_handled',
            content=reporter_notification_content,
            related_id=report.id
        )

        return report
    
    @staticmethod
    def get_report_history(page=1, per_page=10):
        """获取已处理举报历史"""
        # This method is now redundant as get_reports can filter by status
        # Keeping for now, but might be refactored later.
        # It currently filters for 'resolved' or 'rejected'
        query = Report.query.filter(Report.status.in_(['resolved', 'rejected'])).order_by(Report.handled_at.desc())
        
        # 分页
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [report.to_dict() for report in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'page': page,
            'per_page': per_page
        }

# 创建举报服务实例
report_service = ReportService()
