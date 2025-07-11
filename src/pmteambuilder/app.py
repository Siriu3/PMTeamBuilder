"""
入口文件，用于启动应用
"""
import os
import sys

# 将 'src' 目录添加到 sys.path，以便能找到 'pmteambuilder' 包
# os.path.dirname(__file__) 是 app.py 所在的目录 (例如 /path/to/project/src/pmteambuilder)
# os.path.join(os.path.dirname(__file__), '..') 是 'src' 目录 (例如 /path/to/project/src)
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_APP_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from pmteambuilder import create_app

# 获取环境配置
config_name = os.environ.get('FLASK_ENV', 'development')

# 创建应用
app = create_app(config_name)

if __name__ == '__main__':
    # 创建数据库表和启动定时同步任务
    with app.app_context():
        from pmteambuilder.models import db
        db.create_all()
        # 启动宝可梦数据定时同步任务
        from pmteambuilder.services.pokemon_service import PokemonDataService
        # PokemonDataService.start_periodic_refresh(interval_hours=24)  # 暂时屏蔽全量learnset主动同步
        # PokemonDataService.patch_missing_pokemon_move_learnsets()  # 仅补全缺失learnset
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
