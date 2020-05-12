# coding:utf-8
import redis


class Config(object):
    """配置信息类"""
    DEBUG = True

    SECRET_KEY = "ASDLFsa11dlfjSF53lsdf"

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:mysql@192.168.3.9:3306/ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "192.168.3.9"
    REDIS_PORT = 6379

    # flask-session config: Maybe different with the first redis database
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 对cookies 中 session_id 进行隐藏处理
    SESSION_USE_SIGNER = True
    # session数据的有效期，单位秒
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    """开发模式的配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置信息"""
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}