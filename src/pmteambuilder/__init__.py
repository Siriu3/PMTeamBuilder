"""
应用工厂模块，负责创建和配置Flask应用
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail

from .models import db
from .config import config_by_name
from .utils.redis_service import redis_service
from .services.email_service import mail, get_email_service
from .services.pokemon_service import PokemonDataService

def create_app(config_name='development'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_by_name[config_name])
    
    # 初始化扩展
    db.init_app(app)
    # 允许跨域，支持带凭证，允许所有源（开发环境可用）
    CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
    jwt = JWTManager(app)
    mail.init_app(app)
    
    # 初始化Redis服务
    redis_service.init_app(app)

    # 初始化迁移
    Migrate(app, db)
    
    # 注册蓝图
    from .api.auth import auth_bp
    from .api.team import team_bp
    from .api.admin import admin_bp
    from .api.pokemon import bp as pokemon_bp
    from .api.notification import notification_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(team_bp, url_prefix='/api/team')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(pokemon_bp)
    app.register_blueprint(notification_bp)

    # 新增：注册宝可梦相关开放API（批量特性/招式/道具等）
    @app.route('/api/abilities', methods=['GET'])
    def get_abilities():
        limit = int(request.args.get('limit', 10000))
        offset = int(request.args.get('offset', 0))
        generation_id = request.args.get('generation_id')
        abilities = PokemonDataService.get_ability_list(limit=limit, offset=offset, generation_id=generation_id)
        return jsonify(abilities)

    @app.route('/api/moves', methods=['GET'])
    def get_moves():
        limit = int(request.args.get('limit', 10000))
        offset = int(request.args.get('offset', 0))
        generation_id = request.args.get('generation_id')
        moves = PokemonDataService.get_move_list(limit=limit, offset=offset, generation_id=generation_id)
        return jsonify(moves)

    @app.route('/api/items', methods=['GET'])
    def get_items():
        limit = int(request.args.get('limit', 10000))
        offset = int(request.args.get('offset', 0))
        generation_id = request.args.get('generation_id')
        items = PokemonDataService.get_item_list(limit=limit, offset=offset, generation_id=generation_id)
        return jsonify(items)

    # 设置邮件服务
    with app.app_context():
        app.email_service = get_email_service()
    
    # JWT错误处理
    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return {"message": "缺少或无效的令牌"}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return {"message": "签名验证失败"}, 401
    
    @jwt.expired_token_loader
    def expired_token_response(callback, jwt_header):
        return {"message": "令牌已过期"}, 401
    
    # 允许OPTIONS请求直接返回200，避免CORS预检被JWT拦截
    @app.before_request
    def handle_options():
        from flask import request, make_response
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '*')
            response.headers['Access-Control-Allow-Methods'] = request.headers.get('Access-Control-Request-Method', '*')
            return response, 200

    return app
