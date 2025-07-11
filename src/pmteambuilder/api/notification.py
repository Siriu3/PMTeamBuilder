"""
通知相关API路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.notification_service import notification_service

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')

@notification_bp.route('', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """获取当前用户的通知列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    is_read = request.args.get('is_read', type=str)
    
    # Convert is_read string to boolean or keep as None
    if is_read is not None:
        is_read = is_read.lower() == 'true'

    try:
        notifications_data = notification_service.get_user_notifications(
            current_user_id, page, per_page, is_read=is_read
        )
        return jsonify(notifications_data), 200
    except Exception as e:
        return jsonify({"message": "获取通知列表失败", "error": str(e)}), 500

@notification_bp.route('/unread_count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取当前用户未读通知数量"""
    current_user_id = get_jwt_identity()
    try:
        count = notification_service.get_unread_count(current_user_id)
        return jsonify({"unread_count": count}), 200
    except Exception as e:
        return jsonify({"message": "获取未读通知数量失败", "error": str(e)}), 500

@notification_bp.route('/<int:notification_id>/mark-read', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notification_id):
    """标记单个通知为已读"""
    current_user_id = get_jwt_identity()
    try:
        notification = notification_service.mark_as_read(notification_id, current_user_id)
        return jsonify({
            "message": "通知已标记为已读",
            "notification": notification.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "标记通知为已读失败", "error": str(e)}), 500

# New route to mark all notifications as read
@notification_bp.route('/mark_all_read', methods=['POST'])
@jwt_required()
def mark_all_notifications_as_read():
    """标记当前用户所有通知为已读"""
    current_user_id = get_jwt_identity()
    try:
        count = notification_service.mark_all_as_read(current_user_id)
        return jsonify({"message": f"{count} 条通知已标记为已读"}), 200
    except Exception as e:
        return jsonify({"message": "一键已读失败", "error": str(e)}), 500 