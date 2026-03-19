import os
import sys
import importlib

def print_config(config_obj):
    print(f"当前运行环境: {config_obj.APP_ENV}")
    print(f"数据库主机: {config_obj.DB_HOST}")
    print(f"数据库端口: {config_obj.DB_PORT}")
    print(f"数据库用户: {config_obj.DB_USER}")
    print(f"数据库密码: {config_obj.DB_PASSWORD}")
    print(f"API 地址: {config_obj.API_URL}")
    print(f"是否为 DEBUG 模式: {config_obj.DEBUG}")
    print("-" * 30)

if __name__ == "__main__":
    print("【1】默认加载（未设置系统环境变量，默认使用 .env.dev）:")
    import config
    print_config(config.config)
    
    print("【2】模拟生产环境（在环境变量中设置 APP_ENV=production，使用 .env.production）:")
    os.environ["APP_ENV"] = "production"
    # 重载 config 模块以便它重新读取环境变量和配置文件
    importlib.reload(config)
    print_config(config.config)

    print("【3】模拟测试环境（在环境变量中设置 APP_ENV=testing，使用 .env.testing）:")
    os.environ["APP_ENV"] = "testing"
    importlib.reload(config)
    print_config(config.config)
