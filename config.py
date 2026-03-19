import os
from dotenv import load_dotenv

class BaseConfig:
    """基础配置类"""
    DEBUG = False
    TESTING = False
    
    def __init__(self):
        # 实例化时动态读取环境变量，确保 load_dotenv 后能获取最新值
        self.APP_ENV = os.getenv("APP_ENV", "development")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", 3306))
        self.DB_USER = os.getenv("DB_USER", "root")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        self.DB_NAME = os.getenv("DB_NAME", "default_db")
        self.API_URL = os.getenv("API_URL", "http://localhost")

class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True

class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True

class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False

# 环境映射
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

def load_config():
    """
    根据环境变量 APP_ENV 加载对应的 .env 文件，并返回对应的配置实例。
    默认加载 .env.dev 作为开发环境。
    """
    # 1. 优先获取环境变量中的 APP_ENV (如果没设置，默认为 development)
    env = os.getenv("APP_ENV", "development").lower()
    
    # 2. 根据环境决定要加载的文件名
    if env == 'development':
        env_file = ".env.dev"
    elif env == 'production':
        env_file = ".env.production"
    else:
        env_file = f".env.{env}"
    
    # 如果对应的文件存在，则加载 (override=True 表示覆盖已有的环境变量)
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
    else:
        # 兜底：如果没有特定的 .env.* 文件，尝试加载默认的 .env 文件
        if os.path.exists(".env"):
            load_dotenv(".env", override=True)
            
    # 重新读取可能被 .env 文件更新的环境变量
    current_env = os.getenv("APP_ENV", env).lower()
    
    # 3. 获取对应的配置类并实例化
    config_class = config_map.get(current_env, DevelopmentConfig)
    
    return config_class()

# 全局单例配置对象，供其他模块直接导入
# 使用方法: from config import config
config = load_config()
