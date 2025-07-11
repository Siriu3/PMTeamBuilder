"""
敏感词服务模块，提供敏感词过滤功能
"""
from flask import current_app
import re
from ..models import db, SensitiveWord
from ..utils.redis_service import redis_service
import time


class SensitiveWordFilter:
    """敏感词过滤服务类"""
    
    @staticmethod
    def load_sensitive_words_to_cache():
        """从数据库加载敏感词到Redis缓存"""
        sensitive_words = SensitiveWord.query.all()
        words = [word.content for word in sensitive_words]
        
        # 使用Redis集合存储敏感词
        cache_key = current_app.config['SENSITIVE_WORDS_CACHE_KEY']
        cache_timeout = current_app.config['SENSITIVE_WORDS_CACHE_TIMEOUT']
        
        # 清空现有缓存并添加新词
        redis_service.delete(cache_key)
        if words:
            redis_service.set_add(cache_key, *words)
            redis_service.set(f"{cache_key}_timestamp", str(int(time.time())), cache_timeout)
        
        return words
    
    @staticmethod
    def get_sensitive_words():
        """获取所有敏感词"""
        cache_key = current_app.config['SENSITIVE_WORDS_CACHE_KEY']
        # 尝试从缓存获取
        cached_words = redis_service.set_members(cache_key)
        if cached_words:
            # 解码bytes为str
            return [w.decode('utf-8') if isinstance(w, bytes) else w for w in cached_words]
        
        # 缓存未命中，从数据库加载并更新缓存
        return SensitiveWordFilter.load_sensitive_words_to_cache()
    
    @staticmethod
    def contains_sensitive_word(text):
        """检查文本是否包含敏感词"""
        if not text:
            return False, None
        
        sensitive_words = SensitiveWordFilter.get_sensitive_words()
        if not sensitive_words:
            return False, None
        
        # 简单实现：直接检查文本是否包含任何敏感词
        for word in sensitive_words:
            if word in text:
                return True, word
        
        return False, None
    
    @staticmethod
    def filter_text(text, replacement='*'):
        """过滤文本中的敏感词，用replacement替换"""
        if not text:
            return text
        
        sensitive_words = SensitiveWordFilter.get_sensitive_words()
        if not sensitive_words:
            return text
        
        result = text
        for word in sensitive_words:
            if word in result:
                # 替换敏感词为等长的replacement字符
                result = result.replace(word, replacement * len(word))
        
        return result
    
    @staticmethod
    def add_sensitive_word(word, user_id=None):
        """添加新的敏感词"""
        if not word or len(word.strip()) == 0:
            raise ValueError("敏感词不能为空")
        
        word = word.strip()
        
        # 检查是否已存在
        existing = SensitiveWord.query.filter_by(content=word).first()
        if existing:
            raise ValueError(f"敏感词 '{word}' 已存在")
        
        # 创建新敏感词记录
        new_word = SensitiveWord(content=word, created_by=user_id)
        db.session.add(new_word)
        db.session.commit()
        
        # 更新缓存
        cache_key = current_app.config['SENSITIVE_WORDS_CACHE_KEY']
        redis_service.set_add(cache_key, word)
        
        return new_word
    
    @staticmethod
    def remove_sensitive_word(word_id):
        """删除敏感词"""
        word = SensitiveWord.query.get(word_id)
        if not word:
            raise ValueError(f"敏感词ID {word_id} 不存在")
        
        content = word.content
        db.session.delete(word)
        db.session.commit()
        
        # 更新缓存
        cache_key = current_app.config['SENSITIVE_WORDS_CACHE_KEY']
        redis_service.redis_client.srem(cache_key, content)
        
        return content
    
    @staticmethod
    def refresh_cache():
        """刷新敏感词缓存"""
        return SensitiveWordFilter.load_sensitive_words_to_cache()

# 创建敏感词过滤器实例
sensitive_word_filter = SensitiveWordFilter()
