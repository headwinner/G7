import hashlib
import time
from datetime import datetime
from functools import wraps

# ====================================================
# 开放 API 鉴权框架核心逻辑演示
# ====================================================

class OpenAPIFramework:
    
    @staticmethod
    def get_user_by_appkey(app_key):
        """
        模拟从数据库 `open_api_users` 表中查询第三方用户信息
        实际应用中应使用 pymysql 或 ORM 查询数据库
        """
        # 模拟数据库记录
        mock_db = {
            "DEMO_APP_KEY_2024": {
                "company_name": "测试合作公司A",
                "contact_name": "张三",
                "app_secret": "DEMO_SECRET_ABC123XYZ890",
                "status": 1
            }
        }
        return mock_db.get(app_key)

    @staticmethod
    def verify_signature(params, app_secret):
        """
        签名验证算法 (与主流开放平台保持一致)：
        1. 提取客户端传来的 sign
        2. 将除了 sign 以外的参数按首字母排序
        3. 拼接参数键值对
        4. 首尾加上 app_secret
        5. 进行 MD5 加密，转大写，并与客户端 sign 对比
        """
        if 'sign' not in params:
            return False, "缺少签名参数 sign"
            
        client_sign = params.get('sign')
        
        # 1. 剔除 sign 和文件类参数
        sorted_keys = sorted([k for k in params.keys() if k != 'sign'])
        
        # 2. 拼接参数 (例如: appkeyXXXtimestamp2024...)
        param_str = "".join([f"{k}{params[k]}" for k in sorted_keys])
        
        # 3. 首尾拼接 secret
        sign_str = f"{app_secret}{param_str}{app_secret}"
        
        # 4. MD5 计算
        m = hashlib.md5()
        m.update(sign_str.encode('utf-8'))
        server_sign = m.hexdigest().upper()
        
        if client_sign != server_sign:
            return False, f"签名错误"
            
        return True, "验证通过"

    @staticmethod
    def check_timestamp(client_timestamp_str, max_expire_seconds=300):
        """
        防重放攻击验证 (验证时间戳误差)
        :param client_timestamp_str: 客户端传来的时间戳字符串 (如: 2024-01-01 12:00:00)
        :param max_expire_seconds: 允许的最大时间误差(秒)
        """
        try:
            client_time = datetime.strptime(client_timestamp_str, "%Y-%m-%d %H:%M:%S")
            now_time = datetime.now()
            diff_seconds = abs((now_time - client_time).total_seconds())
            if diff_seconds > max_expire_seconds:
                return False
            return True
        except Exception:
            return False

# ====================================================
# 鉴权装饰器 (可用于 Flask/FastAPI/Django 等 Web 框架)
# ====================================================
def require_open_api_auth(func):
    """
    通用 API 鉴权装饰器
    """
    @wraps(func)
    def wrapper(request_params, *args, **kwargs):
        # 1. 基础参数检查
        app_key = request_params.get('appkey')
        timestamp = request_params.get('timestamp')
        
        if not app_key or not timestamp:
            return {"code": 400, "msg": "缺少必要参数: appkey 或 timestamp"}
            
        # 2. 防重放攻击：时间戳校验 (限制5分钟内的请求有效)
        if not OpenAPIFramework.check_timestamp(timestamp):
            return {"code": 401, "msg": "请求已过期或时间戳格式错误"}

        # 3. 查询第三方用户信息
        user_info = OpenAPIFramework.get_user_by_appkey(app_key)
        if not user_info:
            return {"code": 401, "msg": "无效的 appkey"}
            
        if user_info.get('status') != 1:
            return {"code": 403, "msg": "该 AppKey 已被禁用，请联系管理员"}

        # 4. 签名校验
        is_valid, msg = OpenAPIFramework.verify_signature(request_params, user_info['app_secret'])
        if not is_valid:
            return {"code": 401, "msg": msg}

        # 5. 鉴权通过，将调用方信息注入到 kwargs，方便业务层获取(例如打日志、做数据隔离)
        kwargs['api_caller'] = user_info
        
        # 执行具体业务逻辑
        return func(request_params, *args, **kwargs)
        
    return wrapper

# ====================================================
# 模拟测试使用场景
# ====================================================
if __name__ == "__main__":
    # 定义一个被保护的接口
    @require_open_api_auth
    def get_device_data(params, api_caller=None):
        return {
            "code": 200, 
            "msg": "success", 
            "data": "这里是您的温湿度数据",
            "caller_company": api_caller['company_name']
        }

    # 模拟客户端构造合法请求
    print("--- 测试合法请求 ---")
    mock_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_params = {
        "appkey": "DEMO_APP_KEY_2024",
        "timestamp": mock_timestamp,
        "method": "get_device_data"
    }
    
    # 客户端使用 Secret 自己生成签名
    secret = "DEMO_SECRET_ABC123XYZ890"
    sorted_keys = sorted([k for k in client_params.keys()])
    param_str = "".join([f"{k}{client_params[k]}" for k in sorted_keys])
    sign_str = f"{secret}{param_str}{secret}"
    client_params["sign"] = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    # 服务端接收请求并处理
    response = get_device_data(client_params)
    print("服务端响应:", response)
    
    print("\n--- 测试非法请求 (篡改参数) ---")
    bad_params = client_params.copy()
    bad_params["method"] = "delete_all_data" # 篡改业务参数，导致签名不匹配
    response_bad = get_device_data(bad_params)
    print("服务端响应:", response_bad)
