"""
管理员相关API路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models import db, User, Team, SensitiveWord
from ..services.sensitive_word_service import sensitive_word_filter
from ..services.team_service import team_service
from ..services.report_service import report_service
from datetime import datetime, timezone

admin_bp = Blueprint('admin', __name__)

# 管理员权限检查装饰器
def admin_required(fn):
    """检查用户是否具有管理员权限的装饰器"""
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get('is_admin', False):
            return jsonify({"message": "需要管理员权限"}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """获取所有用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'page': page,
        'per_page': per_page
    }), 200

@admin_bp.route('/users/<int:user_id>/admin-status', methods=['PUT'])
@admin_required
def update_user_admin_status(user_id):
    """更新用户管理员状态"""
    current_user_id = get_jwt_identity()
    
    # 不允许修改自己的管理员状态
    if int(current_user_id) == user_id:
        return jsonify({"message": "不能修改自己的管理员状态"}), 400
    
    data = request.get_json()
    is_admin = data.get('is_admin', False)
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": f"用户ID {user_id} 不存在"}), 404
    
    user.is_admin = is_admin
    db.session.commit()
    
    return jsonify({
        "message": f"用户 {user.username} 的管理员状态已更新为 {is_admin}",
        "user": user.to_dict()
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    current_user_id = get_jwt_identity()
    
    # 不允许删除自己
    if int(current_user_id) == user_id:
        return jsonify({"message": "不能删除自己的账户"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": f"用户ID {user_id} 不存在"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({"message": f"用户 {user.username} 已删除"}), 200

@admin_bp.route('/sensitive-words', methods=['GET'])
@admin_required
def get_sensitive_words():
    """获取敏感词列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    words = SensitiveWord.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [word.to_dict() for word in words.items],
        'total': words.total,
        'pages': words.pages,
        'page': page,
        'per_page': per_page
    }), 200

@admin_bp.route('/sensitive-words', methods=['POST'])
@admin_required
def add_sensitive_word():
    """添加敏感词"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({"message": "敏感词内容不能为空"}), 400
    
    try:
        word = sensitive_word_filter.add_sensitive_word(content, current_user_id)
        return jsonify({
            "message": "敏感词添加成功",
            "word": word.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "添加敏感词失败", "error": str(e)}), 500

@admin_bp.route('/sensitive-words/<int:word_id>', methods=['DELETE'])
@admin_required
def remove_sensitive_word(word_id):
    """删除敏感词"""
    try:
        content = sensitive_word_filter.remove_sensitive_word(word_id)
        return jsonify({
            "message": f"敏感词 '{content}' 已删除"
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "删除敏感词失败", "error": str(e)}), 500

@admin_bp.route('/sensitive-words/refresh-cache', methods=['POST'])
@admin_required
def refresh_sensitive_words_cache():
    """刷新敏感词缓存"""
    try:
        words = sensitive_word_filter.refresh_cache()
        return jsonify({
            "message": "敏感词缓存已刷新",
            "count": len(words)
        }), 200
    except Exception as e:
        return jsonify({"message": "刷新敏感词缓存失败", "error": str(e)}), 500

@admin_bp.route('/teams/pending', methods=['GET'])
@admin_required
def get_pending_teams():
    """获取待审核团队列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        teams_data = team_service.get_pending_teams(page, per_page)
        return jsonify(teams_data), 200
    except Exception as e:
        return jsonify({"message": "获取待审核团队失败", "error": str(e)}), 500

@admin_bp.route('/teams/<int:team_id>/review', methods=['POST'])
@admin_required
def review_team(team_id):
    """审核团队"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    approved = data.get('approved', False)
    reason = data.get('reason')
    
    try:
        team = team_service.review_team(team_id, current_user_id, approved, reason)
        return jsonify({
            "message": f"团队 '{team.name}' 已{('通过' if approved else '拒绝')}审核",
            "team": team.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "审核团队失败", "error": str(e)}), 500

@admin_bp.route('/reports/pending', methods=['GET'])
@admin_required
def get_pending_reports():
    """获取待处理举报列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', type=str)
    
    try:
        reports_data = report_service.get_reports(page, per_page, status=status)
        return jsonify(reports_data), 200
    except Exception as e:
        return jsonify({"message": "获取待处理举报失败", "error": str(e)}), 500

@admin_bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    """处理举报"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    action = data.get('action')  # 'delete_team', 'reject_team', 'ignore'
    note = data.get('note')
    
    if action not in ['delete_team', 'reject_team', 'ignore']:
        return jsonify({"message": "无效的处理操作"}), 400
    
    try:
        if action == 'ignore':
            report = report_service.reject_report(report_id, current_user_id, note)
            message = "举报已忽略"
        else:
            report = report_service.resolve_report(report_id, current_user_id, action, note)
            message = "举报已处理"
        
        return jsonify({
            "message": message,
            "report": report.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        return jsonify({"message": "处理举报失败", "error": str(e)}), 500

@admin_bp.route('/reports/history', methods=['GET'])
@admin_required
def get_report_history():
    """获取举报处理历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        reports_data = report_service.get_report_history(page, per_page)
        return jsonify(reports_data), 200
    except Exception as e:
        return jsonify({"message": "获取举报历史失败", "error": str(e)}), 500
