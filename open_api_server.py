from flask import Flask, request, jsonify
from functools import wraps
import hashlib
from datetime import datetime
import pymysql
from config import config
import time

app = Flask(__name__)

# ====================================================
# 数据库连接与开放平台用户查询
# ====================================================
def get_db_connection():
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_user_by_appkey(app_key):
    """从数据库查询第三方用户信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM open_api_users WHERE app_key = %s", (app_key,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return None

def log_api_call(app_key, endpoint, ip, status_code, cost_time):
    """记录 API 调用日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO open_api_logs (app_key, api_endpoint, request_ip, response_code, cost_time_ms) VALUES (%s, %s, %s, %s, %s)",
            (app_key, endpoint, ip, status_code, cost_time)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"日志记录失败: {e}")

# ====================================================
# 鉴权装饰器逻辑
# ====================================================
def require_open_api_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # 1. 获取请求参数 (支持 JSON 和 Form)
        request_params = request.json if request.is_json else request.form.to_dict()
        if not request_params:
            request_params = request.args.to_dict()
            
        app_key = request_params.get('appkey')
        timestamp_str = request_params.get('timestamp')
        client_sign = request_params.get('sign')
        
        if not app_key or not timestamp_str or not client_sign:
            return jsonify({"code": 400, "msg": "缺少必要参数: appkey, timestamp 或 sign"}), 400
            
        # 2. 防重放攻击 (5分钟误差)
        try:
            client_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            diff_seconds = abs((datetime.now() - client_time).total_seconds())
            if diff_seconds > 300:
                return jsonify({"code": 401, "msg": "请求已过期或时间戳不准确"}), 401
        except Exception:
            return jsonify({"code": 400, "msg": "时间戳格式错误，应为 YYYY-MM-DD HH:mm:ss"}), 400

        # 3. 查询用户
        user_info = get_user_by_appkey(app_key)
        if not user_info:
            return jsonify({"code": 401, "msg": "无效的 appkey"}), 401
            
        if user_info.get('status') != 1:
            return jsonify({"code": 403, "msg": "该 AppKey 已被禁用"}), 403

        # 4. 签名校验
        sorted_keys = sorted([k for k in request_params.keys() if k != 'sign'])
        param_str = "".join([f"{k}{request_params[k]}" for k in sorted_keys])
        
        app_secret = user_info['app_secret']
        sign_str = f"{app_secret}{param_str}{app_secret}"
        
        m = hashlib.md5()
        m.update(sign_str.encode('utf-8'))
        server_sign = m.hexdigest().upper()
        
        if client_sign != server_sign:
            return jsonify({"code": 401, "msg": "签名错误"}), 401

        # 5. 鉴权通过，执行业务
        kwargs['api_caller'] = user_info
        kwargs['request_params'] = request_params
        
        response = func(*args, **kwargs)
        
        # 记录日志
        cost_ms = int((time.time() - start_time) * 1000)
        status_code = response[1] if isinstance(response, tuple) else 200
        log_api_call(app_key, request.path, request.remote_addr, status_code, cost_ms)
        
        return response
    return wrapper

# ====================================================
# 业务接口路由
# ====================================================

@app.route('/api/v1/device/getData', methods=['POST', 'GET'])
@require_open_api_auth
def get_device_data(request_params, api_caller=None):
    """
    提供给第三方的温湿度及电量数据查询接口 (查询 device_data 表)
    """
    storage_name = request_params.get('storage_name')
    limit = int(request_params.get('limit', 6))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        device_query = "SELECT collection_time, storage_name, location_name, monitor_point_name, device_number, temperature, humidity, battery FROM device_data"
        device_params = []
        
        if storage_name:
            device_query += " WHERE storage_name = %s"
            device_params.append(storage_name)
            
        device_query += " ORDER BY id DESC LIMIT %s"
        device_params.append(limit)
        
        cursor.execute(device_query, device_params)
        device_data_list = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "caller_company": api_caller['company_name'],
            "data": device_data_list
        })
        
    except Exception as e:
        return jsonify({"code": 500, "msg": f"服务端错误: {str(e)}"}), 500


@app.route('/api/v1/device/getAlarms', methods=['POST', 'GET'])
@require_open_api_auth
def get_alarm_records(request_params, api_caller=None):
    """
    提供给第三方的报警记录查询接口 (查询 alarm_records 表)
    """
    storage_name = request_params.get('storage_name')
    limit = int(request_params.get('limit', 10))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        alarm_query = "SELECT alarm_time, storage_name, location_name, monitor_point_name, device_number, alarm_type, current_value, threshold FROM alarm_records"
        alarm_params = []
        
        if storage_name:
            alarm_query += " WHERE storage_name = %s"
            alarm_params.append(storage_name)
            
        alarm_query += " ORDER BY id DESC LIMIT %s"
        alarm_params.append(limit)
        
        cursor.execute(alarm_query, alarm_params)
        alarm_data_list = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "code": 200,
            "msg": "success",
            "caller_company": api_caller['company_name'],
            "data": alarm_data_list
        })
        
    except Exception as e:
        return jsonify({"code": 500, "msg": f"服务端错误: {str(e)}"}), 500

if __name__ == '__main__':
    print("=====================================================")
    print(" 开放 API 服务正在启动...")
    print(" 请确保您已在数据库中执行了 open_api_design.sql 创建了相关表")
    print(" 监听地址: http://0.0.0.0:15898")
    print("=====================================================")
    # 绑定 0.0.0.0 允许外部网络访问
    app.run(host='0.0.0.0', port=15898, debug=False)
