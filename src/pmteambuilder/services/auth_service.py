"""
认证服务模块，提供用户注册、登录、验证等功能
"""
from datetime import datetime, timedelta, timezone
import uuid
import logging
from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from ..models import db, User, Token
from .sensitive_word_service import sensitive_word_filter # 导入敏感词服务

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AuthService:
    def __init__(self):
        pass

    def register_user(self, username, email, password):
        """
        注册新用户
        """
        # 检查邮箱是否已被注册
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError("邮箱已被注册")

        # 检查用户名是否已被使用
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            raise ValueError("用户名已被使用")

        # 创建新用户
        hashed_password = generate_password_hash(password)
        verification_token = str(uuid.uuid4())
        token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            email_verified=False,
            verification_token=verification_token,
            verification_token_expires_at=token_expires_at,
            is_admin=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()

        # 发送验证邮件
        self._send_verification_email(email, verification_token)

        return {"message": "用户注册成功，请验证您的邮箱。", "user_id": new_user.id}

    def authenticate_user(self, email, password):
        """
        用户登录认证
        """
        # 查询用户
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            raise ValueError("邮箱或密码错误")

        if not user.email_verified:
            raise ValueError("邮箱未验证，请检查您的收件箱")

        # 更新最后登录时间
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # 创建JWT令牌
        additional_claims = {
            'email': user.email,
            'username': user.username,
            'is_admin': user.is_admin,
            'email_verified': user.email_verified
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        # 存储刷新令牌到数据库（可选，用于令牌撤销）
        token = Token(
            user_id=str(user.id),
            token=refresh_token,
            token_type='refresh',
            expires_at=datetime.now(timezone.utc) + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(token)
        db.session.commit()

        expires_in_seconds = int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in_seconds,
            "message": "登录成功",
            "email_verified": user.email_verified,
            "is_admin": user.is_admin,
            "username": user.username
        }

    def verify_email(self, verification_token):
        # 验证用户邮箱
        # 查询具有此验证令牌的用户
        user = User.query.filter_by(verification_token=verification_token).first()
        if not user:
            raise ValueError("无效的验证令牌")

        if user.email_verified:
            raise ValueError("邮箱已验证")

        # 修复时区比较问题
        if user.verification_token_expires_at:
            # 确保verification_token_expires_at是时区感知的
            if user.verification_token_expires_at.tzinfo is None:
                # 如果是非时区感知的，假设它是UTC时间
                aware_expires_at = user.verification_token_expires_at.replace(tzinfo=timezone.utc)
            else:
                aware_expires_at = user.verification_token_expires_at
                
            # 现在可以安全比较
            if aware_expires_at < datetime.now(timezone.utc):
                raise ValueError("验证令牌已过期，请重新请求")

            # 更新用户验证状态
            user.email_verified = True
            user.verification_token = None
            user.verification_token_expires_at = None
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()

            return {"success": True, "message": "邮箱验证成功", "email": user.email}


    def resend_verification_email(self, email):
        """
        重新发送验证邮件
        """
        # 查询用户
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("用户不存在")

        if user.email_verified:
            raise ValueError("邮箱已验证")

        # 生成新的验证令牌
        new_verification_token = str(uuid.uuid4())
        new_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # 更新用户验证令牌
        user.verification_token = new_verification_token
        user.verification_token_expires_at = new_token_expires_at
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # 发送验证邮件
        self._send_verification_email(email, new_verification_token)
        return {"message": "验证邮件发送成功"}

    def refresh_tokens(self, refresh_token_str):
        """
        刷新访问令牌
        """
        try:
            # 验证刷新令牌
            from flask_jwt_extended import decode_token
            decoded_token = decode_token(refresh_token_str)
            user_id = decoded_token['sub']
            
            # 查询用户
            user = User.query.get(user_id)
            if not user:
                raise ValueError("用户不存在")
            
            # 检查令牌是否在数据库中
            token = Token.query.filter_by(user_id=user_id, token=refresh_token_str, token_type='refresh').first()
            if not token:
                raise ValueError("刷新令牌无效或已被撤销")
            
            # 创建新的令牌
            additional_claims = {
                'email': user.email,
                'username': user.username,
                'is_admin': user.is_admin,
                'email_verified': user.email_verified
            }
            
            # 确保user_id是字符串类型
            str_user_id = str(user_id)
            
            new_access_token = create_access_token(
                identity=str_user_id,  # 确保是字符串
                additional_claims=additional_claims
            )
            
            new_refresh_token = create_refresh_token(
                identity=str_user_id,  # 确保是字符串
                additional_claims=additional_claims
            )
            
            # 更新数据库中的令牌
            token.token = new_refresh_token
            token.expires_at = datetime.now(timezone.utc) + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
            db.session.commit()
            
            expires_in_seconds = int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "expires_in": expires_in_seconds,
                "message": "令牌刷新成功"
            }
        except Exception as e:
            logging.error(f"令牌刷新错误: {str(e)}")
            raise ValueError(f"令牌刷新失败: {str(e)}")


    def update_user_profile(self, user_id, new_username=None):
        """
        更新用户资料
        """
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 更新用户名
        if new_username:
            # 检查用户名是否包含敏感词
            contains_sensitive, sensitive_word = sensitive_word_filter.contains_sensitive_word(new_username)
            if contains_sensitive:
                raise ValueError(f"用户名包含敏感词：'{sensitive_word}'")

            # 检查用户名是否已被使用
            existing_username = User.query.filter(User.username == new_username, User.id != user_id).first()
            if existing_username:
                raise ValueError("用户名已被使用")
            
            user.username = new_username
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return {"message": "用户资料更新成功", "username": user.username}

    def get_user_profile(self, user_id):
        """
        获取用户资料
        """
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }

    def set_user_admin_status(self, user_id, is_admin):
        """
        设置用户管理员状态
        """
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"ID为{user_id}的用户不存在")

        # 更新管理员状态
        user.is_admin = is_admin
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logging.info(f"用户 {user_id} (邮箱: {user.email}) 管理员状态设置为 {is_admin}")
        return {"message": f"用户 {user_id} 管理员状态已更新"}

    def _send_verification_email(self, user_email, verification_token):
        """
        发送验证邮件
        """
        verification_link = url_for('auth.verify_email', token=verification_token, _external=True)
        subject = "请验证您的宝可梦团队构建系统邮箱"
        body = f"""您好，

请点击以下链接验证您的邮箱地址：

{verification_link}

如果您没有注册此服务，请忽略此邮件。

谢谢，
宝可梦团队构建系统团队"""

        # 在开发环境中，将邮件输出到日志
        if current_app.config['DEBUG']:
            logging.info(f"\n--- 模拟邮件 ---")
            logging.info(f"收件人: {user_email}")
            logging.info(f"主题: {subject}")
            logging.info(f"内容:\n{body}")
            logging.info(f"--- 模拟邮件结束 ---\n")
        else:
            # 在生产环境中，使用实际的邮件服务
            try:
                from flask_mail import Message
                from .. import mail
                
                msg = Message(subject, recipients=[user_email])
                msg.body = body
                mail.send(msg)
            except Exception as e:
                logging.error(f"发送邮件失败: {str(e)}")

# 实例化服务
auth_service = AuthService()
