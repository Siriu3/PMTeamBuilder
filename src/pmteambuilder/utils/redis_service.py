"""
Redis集成模块
"""
import redis
from flask import current_app

class RedisService:
    """Redis服务类，提供Redis操作的封装"""
    
    def __init__(self, app=None):
        self.redis_client = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Redis客户端"""
        self.redis_client = redis.from_url(app.config['REDIS_URL'])
    
    def set(self, key, value, expire=None):
        """设置键值对"""
        self.redis_client.set(key, value)
        if expire:
            self.redis_client.expire(key, expire)
    
    def get(self, key):
        """获取键值"""
        return self.redis_client.get(key)
    
    def delete(self, key):
        """删除键值对"""
        self.redis_client.delete(key)
    
    def exists(self, key):
        """检查键是否存在"""
        return self.redis_client.exists(key)
    
    def set_list(self, key, values, expire=None):
        """设置列表"""
        pipeline = self.redis_client.pipeline()
        pipeline.delete(key)
        if values:
            pipeline.rpush(key, *values)
            if expire:
                pipeline.expire(key, expire)
        pipeline.execute()
    
    def get_list(self, key):
        """获取列表所有元素"""
        return self.redis_client.lrange(key, 0, -1)
    
    def set_hash(self, key, mapping, expire=None):
        """设置哈希表"""
        self.redis_client.hmset(key, mapping)
        if expire:
            self.redis_client.expire(key, expire)
    
    def get_hash(self, key):
        """获取哈希表所有字段和值"""
        return self.redis_client.hgetall(key)
    
    def get_hash_field(self, key, field):
        """获取哈希表指定字段的值"""
        return self.redis_client.hget(key, field)
    
    def increment(self, key, amount=1):
        """递增键值"""
        return self.redis_client.incr(key, amount)
    
    def set_add(self, key, *values):
        """向集合添加元素"""
        return self.redis_client.sadd(key, *values)
    
    def set_members(self, key):
        """获取集合所有成员"""
        return self.redis_client.smembers(key)
    
    def set_is_member(self, key, value):
        """判断元素是否是集合的成员"""
        return self.redis_client.sismember(key, value)
    
    def flush_db(self):
        """清空当前数据库"""
        self.redis_client.flushdb()

# 创建Redis服务实例
redis_service = RedisService()
