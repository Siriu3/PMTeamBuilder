"""
配置模块，包含不同环境的配置类
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class Config:
    """基础配置类"""
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or '114514YAJU'
    DEBUG = False
    TESTING = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost/pmteambuilder'
    # sqlite:///dev.db
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    
    # 邮件配置
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'test@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@example.com')
    
    # Redis配置
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # 敏感词配置
    SENSITIVE_WORDS_CACHE_KEY = 'sensitive_words'
    SENSITIVE_WORDS_CACHE_TIMEOUT = 3600  # 1小时

    # 拉取数据时是否显示进度
    SHOW_FETCH_PROGRESS = True
    # 拉取数据时是否保存进度
    SAVE_FETCH_PROGRESS = True
    # 是否每次启动都强制重新拉取
    FORCE_FETCH_ON_STARTUP = True

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev.db'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'postgresql://postgres:lyc169405@localhost:5432/pmteambuilder'
    
    # 开发环境邮件配置
    MAIL_SUPPRESS_SEND = True  # 抑制实际发送
    MAIL_DEBUG = True  # 启用调试输出
    
    # 开发环境Redis配置
    REDIS_URL = os.environ.get('DEV_REDIS_URL', 'redis://localhost:6379/0')

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'postgresql://test_user:test_password@localhost:5432/test_db'
    
    # 测试环境邮件配置
    MAIL_SUPPRESS_SEND = True
    
    # 测试环境Redis配置
    REDIS_URL = os.environ.get('TEST_REDIS_URL', 'redis://localhost:6379/1')

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # 生产环境特定配置
    MAIL_SUPPRESS_SEND = False
    
    # 生产环境Redis配置
    REDIS_URL = os.environ.get('REDIS_URL')

# 配置字典，用于根据环境名称选择配置
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
