# -*- coding: utf-8 -*-
"""
数据迁移脚本：将 SQLite 数据库中的数据迁移到 PostgreSQL
"""
import os
import pandas as pd
from sqlalchemy import create_engine, inspect

# SQLite 数据库连接字符串
# 请根据您的实际 .db 文件路径进行修改
# 例如：sqlite:///path/to/your/dev.db
SQLITE_DATABASE_URI = 'sqlite:///src/instance/dev.db' 

# PostgreSQL 数据库连接字符串
# 请根据您的实际 PostgreSQL 连接信息进行修改
# 例如：postgresql://user:password@host:port/dbname
POSTGRES_DATABASE_URI = 'postgresql://postgres:lyc169405@localhost:5432/pmteambuilder'


import_order = [
    'types',
    'generations',
    'version_groups',
    'abilities',
    'moves',
    'items',
    'sensitive_words',
    'users',
    'pokemon_species',
    'pokemon',
    'tokens',
    'teams',
    'generation_pokemon_species', # 关联表
    'pokemon_move_learnset',
    'pokemon_form_ability_map',   # 假设依赖 pokemon, abilities
    'team_pokemon',
    'pokemon_moves',
    'team_custom_tags',
    'user_favorites',       # 关联表
    'team_likes',
    'reports',
    'notifications',
]

import_order2 = [
    'sensitive_words'
]

def migrate_data():
    """执行数据迁移"""
    print(f"正在从 {SQLITE_DATABASE_URI} 连接 SQLite 数据库...")
    try:
        sqlite_engine = create_engine(SQLITE_DATABASE_URI)
        sqlite_conn = sqlite_engine.connect()
        print("SQLite 数据库连接成功。")
    except Exception as e:
        print(f"连接 SQLite 数据库失败: {e}")
        return

    print(f"正在连接 PostgreSQL 数据库 {POSTGRES_DATABASE_URI}...")
    try:
        postgres_engine = create_engine(POSTGRES_DATABASE_URI)
        postgres_conn = postgres_engine.connect()
        print("PostgreSQL 数据库连接成功。")
    except Exception as e:
        print(f"连接 PostgreSQL 数据库失败: {e}")
        sqlite_conn.close()
        return

    # 获取 SQLite 数据库中的所有表名
    inspector = inspect(sqlite_engine)
    sqlite_tables = inspector.get_table_names()
    
    print(f"在 SQLite 数据库中找到以下表格：{sqlite_tables}")
    
    # 遍历所有表并迁移数据
    for table_name in import_order2:
        print(f"正在迁移表格: {table_name}...")
        try:
            # 从 SQLite 读取数据
            df = pd.read_sql_table(table_name, sqlite_conn)
            
            # 将数据写入 PostgreSQL
            # if_exists='append' 表示如果表已存在，则追加数据
            # index=False 表示不将 DataFrame 的索引作为一列写入数据库
            df.to_sql(table_name, postgres_conn, if_exists='append', index=False)
            print(f"表格 {table_name} 数据迁移成功。")
        except Exception as e:
            print(f"迁移表格 {table_name} 失败: {e}")
            # 在实际应用中，您可能需要更精细的错误处理，例如跳过或记录错误

    # 关闭数据库连接
    sqlite_conn.close()
    postgres_conn.close()
    print("数据迁移完成。")

if __name__ == "__main__":
    # 为了能够运行此脚本，需要确保项目根目录在sys.path中，或者直接在项目根目录运行此脚本。
    # 假设当前工作目录是项目根目录（D:\VSCDocument\pmteambuilder）。
    # 如果不是，需要调整 SQLITE_DATABASE_URI 路径。
    
    # 示例：如果您运行脚本时的工作目录不是项目根目录，需要调整 SQLite 路径
    # 例如，如果脚本在 src/pmteambuilder/utils，而 .db 在 instance：
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.join(script_dir, '..', '..', '..')
    # SQLITE_DATABASE_URI = f'sqlite:///{os.path.join(project_root, "instance", "dev.db")}'

    migrate_data() 