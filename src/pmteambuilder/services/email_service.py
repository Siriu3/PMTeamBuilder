"""
邮件服务模块，提供邮件发送功能
"""
from flask import current_app, render_template
from flask_mail import Message, Mail
import logging
import os
from datetime import datetime
from pmteambuilder.config.config import Config

# 创建Mail实例
mail = Mail()

class EmailService:
    """邮件服务接口"""
    
    def send_verification_email(self, user_email, verification_token):
        """发送邮箱验证邮件"""
        pass
    
    def send_password_reset_email(self, user_email, reset_token):
        """发送密码重置邮件"""
        pass

class ProductionEmailService(EmailService):
    """生产环境邮件服务实现"""
    
    def send_verification_email(self, user_email, verification_token):
        """发送邮箱验证邮件"""
        subject = "请验证您的宝可梦团队构建系统账号"
        verification_link = f"{current_app.config['FRONTEND_URL'] or 'http://localhost:5173'}/verify-email?token={verification_token}"
        
        body = f"""
        您好，

        请点击以下链接验证您的邮箱地址：

        {verification_link}

        如果您没有注册宝可梦团队构建系统账号，请忽略此邮件。

        此致，
        宝可梦团队构建系统团队
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        return True
    
    def send_password_reset_email(self, user_email, reset_token):
        """发送密码重置邮件"""
        subject = "宝可梦团队构建系统密码重置"
        reset_link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={reset_token}"
        
        body = f"""
        您好，

        您请求重置宝可梦团队构建系统的密码。请点击以下链接设置新密码：

        {reset_link}

        如果您没有请求重置密码，请忽略此邮件。

        此致，
        宝可梦团队构建系统团队
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        return True

class MockEmailService(EmailService):
    """模拟邮件服务实现，用于开发环境"""
    
    def __init__(self):
        """初始化模拟邮件服务"""
        self.log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.log_file = os.path.join(self.log_dir, 'mock_emails.log')
        self.logger = logging.getLogger('mock_email_service')
        self.logger.setLevel(logging.INFO)
        
        # 添加文件处理器
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def send_verification_email(self, user_email, verification_token):
        """模拟发送邮箱验证邮件"""
        verification_link = f"{current_app.config['FRONTEND_URL']}/verify-email?token={verification_token}"
        
        email_content = f"""
        =============== 模拟邮件 ===============
        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        收件人: {user_email}
        主题: 请验证您的宝可梦团队构建系统账号
        
        内容:
        您好，
        
        请点击以下链接验证您的邮箱地址：
        
        {verification_link}
        
        如果您没有注册宝可梦团队构建系统账号，请忽略此邮件。
        
        此致，
        宝可梦团队构建系统团队
        ========================================
        """
        
        self.logger.info(email_content)
        return True
    
    def send_password_reset_email(self, user_email, reset_token):
        """模拟发送密码重置邮件"""
        reset_link = f"{current_app.config['FRONTEND_URL']}/reset-password?token={reset_token}"
        
        email_content = f"""
        =============== 模拟邮件 ===============
        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        收件人: {user_email}
        主题: 宝可梦团队构建系统密码重置
        
        内容:
        您好，
        
        您请求重置宝可梦团队构建系统的密码。请点击以下链接设置新密码：
        
        {reset_link}
        
        如果您没有请求重置密码，请忽略此邮件。
        
        此致，
        宝可梦团队构建系统团队
        ========================================
        """
        
        self.logger.info(email_content)
        return True

def get_email_service():
    """根据环境获取合适的邮件服务实现"""
    if current_app.config.get('MAIL_SUPPRESS_SEND', False):
        return MockEmailService()
    else:
        return ProductionEmailService()

# 创建邮件服务实例
email_service = None  # 将在应用初始化时设置
