# backend/app/api/auth.py
from flask import Blueprint, request, jsonify, current_app
from pmteambuilder.services.auth_service import auth_service # Adjust import path as needed
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from datetime import timedelta # To define JWT expiry
# from pmteambuilder.utils.decorators import admin_required # 暂时不使用装饰器，直接在路由内部检查claims

auth_bp = Blueprint('auth', __name__)

# Configure JWT settings (usually in app.py or config.py)
# app.config["JWT_SECRET_KEY"] = "super-secret-key-for-jwt" # Change this!
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
# app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
# jwt = JWTManager(app)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"message": "缺失必填项"}), 400

    try:
        response = auth_service.register_user(username, email, password)
        return jsonify(response), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 409 # Conflict

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "缺少用户名或密码"}), 400

    try:
        response = auth_service.authenticate_user(email, password)
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 401 # Unauthorized

@auth_bp.route('/verify-email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({"message": "缺失验证令牌"}), 400

    try:
        response = auth_service.verify_email(token)
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/resend-verification-email', methods=['POST'])
def resend_verification_email():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"message": "需要Email"}), 400

    try:
        response = auth_service.resend_verification_email(email)
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({"message": "缺失刷新令牌"}), 400

    try:
        response = auth_service.refresh_tokens(refresh_token)
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 401 # Unauthorized


@auth_bp.route('/profile', methods=['GET'])
@jwt_required() # Protect this endpoint with JWT
def get_profile():
    current_user_id = get_jwt_identity()
    # fetch user details from DB using current_user_id
    claims = get_jwt() # Get all claims from JWT
    user_email = claims.get('email', 'N/A')
    username = claims.get('username', 'N/A')
    is_admin = claims.get('is_admin', False)
    email_verified = claims.get('email_verified', False)

    return jsonify({
        "user_id": current_user_id,
        "username": username,
        "email": user_email,
        "is_admin": is_admin,
        "email_verified": email_verified,
        "message": "User profile data (simulated)"
    }), 200

# 更新用户个人资料路由 (PUT) - 新增
@auth_bp.route('/profile', methods=['PUT']) # <--- 新增 PUT 方法
@jwt_required() # 需要 JWT 认证
def update_profile():
    claims = get_jwt()
    current_user_id = claims.get('sub') # 获取当前 JWT 的用户ID
    data = request.get_json()

    # 允许修改的字段
    new_username = data.get('username')
    # 如果允许修改其他字段，例如密码（需要旧密码），邮箱（需要验证），在这里添加
    # 比如：new_password = data.get('password')

    try:
        # 调用 auth_service 来处理更新逻辑
        # 这里需要 auth_service 提供一个 update_user_profile 方法
        response = auth_service.update_user_profile(current_user_id, new_username) # 传递 current_user_id 和要更新的数据

        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "更新档案时发生错误", "error": str(e)}), 500

# 新增：管理员专属测试路由
@auth_bp.route('/admin-data', methods=['GET'])
@jwt_required() # 需要JWT认证
def get_admin_data():
    claims = get_jwt() # 获取当前JWT的claims
    if not claims.get('is_admin', False): # 检查JWT中的is_admin字段
        return jsonify({"message": "Admin access required"}), 403 # 403 Forbidden
    return jsonify({"message": "管理员面板概览数据已成功加载，请谨慎处理相关数据。"}), 200
