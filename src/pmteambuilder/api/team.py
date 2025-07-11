"""
团队相关API路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..services.team_service import team_service
from ..services.sensitive_word_service import sensitive_word_filter
from ..services.report_service import report_service
from ..utils.decorators import admin_required
from ..models import Report

team_bp = Blueprint('team', __name__, url_prefix='/api/team')

@team_bp.route('/<int:team_id>', methods=['GET'])
@jwt_required(optional=True)
def get_team(team_id):
    """获取团队详情"""
    current_user_id = get_jwt_identity()
    try:
        team_data = team_service.get_team(team_id, current_user_id=current_user_id)
        return jsonify(team_data), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting team {team_id}: {e}")
        return jsonify({"message": "获取团队失败", "error": str(e)}), 500

@team_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_teams():
    """获取当前用户的团队列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    generation = request.args.get('generation', type=str) # Receive generation filter
    status = request.args.get('status', type=str)       # Receive status filter
    format = request.args.get('format', type=str)         # Receive format filter
    
    # Receive is_public filter as string and manually convert to boolean or None
    is_public_str = request.args.get('is_public', type=str)
    is_public = None
    if is_public_str is not None:
        if is_public_str.lower() == 'true':
            is_public = True
        elif is_public_str.lower() == 'false':
            is_public = False
        # If it's not 'true' or 'false', is_public remains None

    try:
        # Pass filters to the service method, including is_public
        teams_data = team_service.get_user_teams(current_user_id, page, per_page, generation=generation, status=status, format=format, is_public=is_public)
        return jsonify(teams_data), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user teams for user {current_user_id}: {e}")
        return jsonify({"message": "获取团队列表失败", "error": str(e)}), 500

@team_bp.route('/<int:team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    """删除团队"""
    current_user_id = get_jwt_identity()
    
    try:
        team_service.delete_team(team_id, current_user_id)
        return jsonify({"message": "团队删除成功"}), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting team {team_id} for user {current_user_id}: {e}")
        return jsonify({"message": "删除团队失败", "error": str(e)}), 500

@team_bp.route('/<int:team_id>/report', methods=['POST'])
@jwt_required()
def report_team(team_id):
    """举报团队"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    reason = data.get('reason')
    
    if not reason:
        return jsonify({"message": "举报理由不能为空"}), 400
    
    try:
        report = report_service.create_report(current_user_id, team_id, reason)
        return jsonify({
            "message": "举报提交成功",
            "report_id": report.id
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error submitting report for team {team_id} by user {current_user_id}: {e}")
        return jsonify({"message": "提交举报失败", "error": str(e)}), 500

@team_bp.route('', methods=['POST'])
@jwt_required()
def create_team_endpoint():
    """创建新团队"""
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    generation = data.get('generation') # 接收 generation
    format = data.get('format')       # 接收 format
    pokemons = data.get('pokemons', [])
    custom_tags = data.get('custom_tags', [])
    is_public = data.get('is_public', True) # 接收 is_public，默认 True

    if not name or not generation or not format:
        return jsonify({'message': 'Team name, generation, and format are required'}), 400

    try:
        new_team = team_service.create_team(user_id, name, generation, format, pokemons=pokemons, custom_tags=custom_tags, is_public=is_public)
        return jsonify(new_team.to_dict(include_token=True)), 201
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating team for user {user_id}: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@team_bp.route('/<int:team_id>', methods=['PUT'])
@jwt_required()
def update_team_endpoint(team_id):
    """更新团队信息"""
    user_id = get_jwt_identity()
    data = request.get_json()
    name = data.get('name')
    pokemons = data.get('pokemons') # Allow pokemons to be None to not update
    custom_tags = data.get('custom_tags') # Allow custom_tags to be None
    generation = data.get('generation') # Receive generation (allow None)
    format = data.get('format')       # Receive format (allow None)
    description = data.get('description') # Receive description parameter
    is_public = data.get('is_public', None) # Receive is_public (allow None), explicit None check in service

    try:
        updated_team = team_service.update_team(team_id, user_id, name=name, pokemons=pokemons, custom_tags=custom_tags, generation=generation, format=format, description=description, is_public=is_public)
        return jsonify(updated_team.to_dict()), 200
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating team {team_id} for user {user_id}: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@team_bp.route('/import', methods=['POST'])
def import_team_by_token_endpoint():
    """通过Token导入团队"""
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({"message": "Token is required"}), 400

    try:
        imported_data = team_service.get_team_by_token(token)
        return jsonify(imported_data), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error importing team with token {token}: {e}")
        return jsonify({"message": "导入团队失败", "error": str(e)}), 500

@team_bp.route('/<int:team_id>/copy', methods=['POST'])
@jwt_required()
def copy_team_endpoint(team_id):
    """复制团队"""
    current_user_id = get_jwt_identity()
    try:
        new_team = team_service.copy_team(team_id, current_user_id)
        return jsonify(new_team.to_dict(include_token=True)), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error copying team {team_id} for user {current_user_id}: {e}")
        return jsonify({"message": "复制团队失败", "error": str(e)}), 500

@team_bp.route('/public', methods=['GET'])
@jwt_required(optional=True)
def get_public_teams():
    """获取公开且审核通过的团队列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', type=str)
    generation = request.args.get('generation', type=str)
    format = request.args.get('format', type=str)

    try:
        teams_data = team_service.get_public_approved_teams(
            page=page,
            per_page=per_page,
            search_query=search_query,
            generation=generation,
            format=format,
            current_user_id=current_user_id
        )
        return jsonify(teams_data), 200
    except Exception as e:
        current_app.logger.error(f"Error getting public teams: {e}")
        return jsonify({"message": "获取团队列表失败", "error": str(e)}), 500

@team_bp.route('/<int:team_id>/like', methods=['POST', 'DELETE'])
@jwt_required()
def like_team(team_id):
    """用户点赞或取消点赞团队"""
    current_user_id = get_jwt_identity()
    if not current_user_id:
         return jsonify({"message": "需要登录才能点赞"}), 401

    try:
        if request.method == 'POST':
            likes_count = team_service.add_like(int(current_user_id), team_id)
            return jsonify({
                "message": "点赞成功",
                "likes_count": likes_count
            }), 200
        elif request.method == 'DELETE':
            likes_count = team_service.remove_like(int(current_user_id), team_id)
            return jsonify({
                "message": "取消点赞成功",
                "likes_count": likes_count
            }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error during like operation for team {team_id} by user {current_user_id}: {e}")
        return jsonify({"message": "点赞失败", "error": str(e)}), 500

@team_bp.route('/<int:team_id>/favorite', methods=['POST', 'DELETE'])
@jwt_required()
def favorite_team(team_id):
    """用户收藏或取消收藏团队"""
    current_user_id = get_jwt_identity()
    current_app.logger.info(f"User {current_user_id} attempting to favorite/unfavorite team {team_id}")

    try:
        user_id_int = int(current_user_id)
        if request.method == 'POST':
            # Add favorite
            new_favorites_count = team_service.add_favorite(user_id_int, team_id)
            return jsonify({'message': 'Team favorited successfully', 'favorites_count': new_favorites_count}), 200
        elif request.method == 'DELETE':
            # Remove favorite
            new_favorites_count = team_service.remove_favorite(user_id_int, team_id)
            return jsonify({'message': 'Team unfavorited successfully', 'favorites_count': new_favorites_count}), 200

    except ValueError as e:
         current_app.logger.error(f"Favorite/Unfavorite team {team_id} error: {e}")
         return jsonify({'message': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during favorite/unfavorite operation for team {team_id} by user {current_user_id}: {e}")
        return jsonify({'message': 'An error occurred during the favorite operation'}), 500

@team_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorite_teams_endpoint():
    """获取当前用户收藏的团队列表"""
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
        # 调用 team_service 中已实现的获取收藏团队列表的方法
        teams_data = team_service.get_favorite_teams(current_user_id, page, per_page)
        return jsonify(teams_data), 200
    except Exception as e:
        current_app.logger.error(f"Error getting favorite teams for user {current_user_id}: {e}")
        return jsonify({"message": "获取收藏团队列表失败", "error": str(e)}), 500