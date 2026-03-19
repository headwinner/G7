import pymysql.cursors
from config import config

# MySQL 数据库配置
DB_CONFIG = {
    'host': config.DB_HOST,
    'port': config.DB_PORT,
    'user': config.DB_USER,
    'password': config.DB_PASSWORD,
    'database': config.DB_NAME,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
