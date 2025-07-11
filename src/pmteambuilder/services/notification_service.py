"""
通知服务模块
"""
from ..models import db, Notification, User
from datetime import datetime

class NotificationService:
    """通知服务类"""

    @staticmethod
    def create_notification(user_id, type, content, related_id=None):
        """创建一个新的通知"""
        user = User.query.get(user_id)
        if not user:
            # Or handle this differently, depending on desired behavior
            print(f"Warning: User with ID {user_id} not found when creating notification.")
            return None # Or raise an error

        notification = Notification(
            user_id=user_id,
            type=type,
            content=content,
            related_id=related_id
        )

        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_user_notifications(user_id, page=1, per_page=10, is_read=None):
        """获取用户的通知列表"""
        query = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc())

        if is_read is not None:
            query = query.filter_by(is_read=is_read)

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [notif.to_dict() for notif in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'page': page,
            'per_page': per_page
        }

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """标记通知为已读并验证用户归属"""
        # Query the notification by ID and user_id to ensure ownership
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            # Use a more specific message if notification doesn't exist for this user
            raise ValueError(f"通知ID {notification_id} 不存在或不属于当前用户")

        if not notification.is_read:
            notification.is_read = True
            db.session.commit()

        return notification

    @staticmethod
    def get_unread_count(user_id):
        """获取用户的未读通知数量"""
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
        return count

    @staticmethod
    def mark_all_as_read(user_id):
        """标记用户所有未读通知为已读"""
        # Find all unread notifications for the user
        unread_notifications = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).all()

        # Update is_read status and count the number of updated notifications
        updated_count = 0
        for notification in unread_notifications:
            notification.is_read = True
            updated_count += 1

        # Commit the changes to the database
        if updated_count > 0:
            db.session.commit()
        
        return updated_count

# 创建通知服务实例
notification_service = NotificationService() 