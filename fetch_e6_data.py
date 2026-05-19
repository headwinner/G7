import time
import hashlib
import requests
from datetime import datetime
import json
import os
import sys
import pymysql
from db_config import DB_CONFIG

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    sys.stdout.flush()

# ==================== 配置区域 ====================
# 使用易流平台获取的 appkey 和 appsecret
APP_KEY = "0545F4D9-F0C3-48F2-A576-E1A846A6D33A" 
APP_SECRET = "6941524B-BD39-4016-9191-8DE3393D8437"

# 仓库名称（根据图片）
STORAGE_NAME = "福建汉吉斯冷链物流有限公司"

# API 请求地址 (4.39 获取仓库最新温湿度数据)
API_URL = "https://api.e6yun.com/public/v4/BL-MODULE-COLD-CHAIN-WEB/api/cold/storageTempHum/getStorageTempHum"

# 低电量报警阈值（百分比）
LOW_BATTERY_ALARM_THRESHOLD = 30

# ==================================================

def get_db_connection():
    """
    获取 MySQL 数据库连接
    """
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        log(f"数据库连接失败: {e}")
        raise

def init_db():
    """
    初始化 MySQL 数据库并创建数据表
    """
    log("正在初始化数据库...")
    # 先连接到 MySQL Server (不指定数据库) 来创建数据库
    temp_config = DB_CONFIG.copy()
    db_name = temp_config.pop('database')
    
    try:
        conn = pymysql.connect(**temp_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        conn.close()
        log(f"数据库 {db_name} 确认存在")
    except Exception as e:
        log(f"创建数据库失败 (可能已存在或权限不足): {e}")

    # 连接到指定数据库创建表
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                collection_time VARCHAR(50),
                storage_name VARCHAR(100),
                location_name VARCHAR(100),
                monitor_point_name VARCHAR(100),
                device_number VARCHAR(50),
                temperature FLOAT,
                humidity FLOAT,
                battery INT,
                data_time VARCHAR(50)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alarm_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                storage_name VARCHAR(100),
                location_name VARCHAR(100),
                monitor_point_name VARCHAR(100),
                device_number VARCHAR(50),
                alarm_type VARCHAR(50),
                current_value FLOAT,
                threshold FLOAT,
                alarm_time VARCHAR(50)
            )
        ''')
        conn.commit()
        conn.close()
        log("数据表检查完成")
    except Exception as e:
        log(f"初始化数据表失败: {e}")
        raise

# ==================== CRUD 操作 ====================
def insert_alarm(alarm_dict):
    """
    插入一条报警记录
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alarm_records (
                storage_name, location_name, monitor_point_name, device_number, 
                alarm_type, current_value, threshold, alarm_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            alarm_dict.get('storage_name'),
            alarm_dict.get('location_name'),
            alarm_dict.get('monitor_point_name'),
            alarm_dict.get('device_number'),
            alarm_dict.get('alarm_type'),
            alarm_dict.get('current_value'),
            alarm_dict.get('threshold'),
            alarm_dict.get('alarm_time')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"插入报警记录失败: {e}")

def query_alarms(limit=10, offset=0, alarm_type=None):
    """
    查询报警记录
    alarm_type: 报警类型筛选
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM alarm_records'
    params = []
    
    if alarm_type:
        query += ' WHERE alarm_type = %s'
        params.append(alarm_type)
        
    query += ' ORDER BY id DESC LIMIT %s OFFSET %s'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_alarm(record_id, update_dict):
    """
    更新报警记录
    update_dict: 需要更新的字段字典
    """
    if not update_dict:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{k} = %s" for k in update_dict.keys()])
    params = list(update_dict.values())
    params.append(record_id)
    
    cursor.execute(f'UPDATE alarm_records SET {set_clause} WHERE id = %s', params)
    conn.commit()
    conn.close()

def delete_alarm(record_id):
    """
    删除一条报警记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alarm_records WHERE id = %s', (record_id,))
    conn.commit()
    conn.close()

def insert_data(data_dict):
    """
    插入一条温湿度数据
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO device_data (
                collection_time, storage_name, location_name, monitor_point_name,
                device_number, temperature, humidity, battery, data_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data_dict.get('collection_time'),
            data_dict.get('storage_name'),
            data_dict.get('location_name'),
            data_dict.get('monitor_point_name'),
            data_dict.get('device_number'),
            data_dict.get('temperature'),
            data_dict.get('humidity'),
            data_dict.get('battery'),
            data_dict.get('data_time')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"插入温湿度数据失败: {e}")

def query_data(limit=10, offset=0):
    """
    查询温湿度数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM device_data ORDER BY id DESC LIMIT %s OFFSET %s', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_data(record_id, update_dict):
    """
    更新温湿度数据
    """
    if not update_dict:
        return
    
    set_clause = ", ".join([f"{k} = %s" for k in update_dict.keys()])
    values = list(update_dict.values())
    values.append(record_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'UPDATE device_data SET {set_clause} WHERE id = %s', values)
    conn.commit()
    conn.close()

def delete_data(record_id):
    """
    删除一条温湿度数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM device_data WHERE id = %s', (record_id,))
    conn.commit()
    conn.close()
# ==================================================

def generate_sign(secret_key, params):
    """
    签名算法：
    1. 根据传入参数名称（sign除外）将所有请求参数按照首字母先后顺序排序
    2. 对排序后的参数名称和参数值进行字符串拼接
    3. 在拼接后的字符串首尾加上 appsecret
    4. 对拼接后的字符串进行 MD5 加密，并转为大写
    """
    sorted_keys = sorted([k for k in params.keys() if k != 'sign'])
    param_str = "".join([f"{k}{params[k]}" for k in sorted_keys])
    sign_str = f"{secret_key}{param_str}{secret_key}"
    
    m = hashlib.md5()
    m.update(sign_str.encode('utf-8'))
    return m.hexdigest().upper()

def fetch_equip_data():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构造请求参数 (注意：4.39 接口参数与 4.44 不同)
    params = {
        "method": "getStorageTempHum",
        "timestamp": timestamp,
        "format": "json",
        "storageName": STORAGE_NAME,
        "appkey": APP_KEY
    }
    
    # 计算签名
    params["sign"] = generate_sign(APP_SECRET, params)
    
    # 打印请求参数供排查
    log(f"发起请求, 接口: {API_URL}")
    
    try:
        # 发送POST请求 (application/x-www-form-urlencoded)
        response = requests.post(API_URL, data=params, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 1:
            data = result.get("data", {})
            location_list = data.get("locationList", [])
            
            log(f"数据采集成功，获取到 {len(location_list)} 个区位的数据")
            
            count = 0
            for location in location_list:
                loc_name = location.get("locationName", "")
                point_list = location.get("pointList", [])
                
                for point in point_list:
                    point_name = point.get("pointName", "")
                    equip_code = point.get("equipCode", "")
                    temp = point.get("temp", "")
                    hum = point.get("hum", "")
                    elec = point.get("elecValue", "")
                    gps_time = point.get("gpstime", "")
                    
                    # 过滤无效数据 (根据之前的逻辑保留)
                    if temp == -999 or hum == -1:
                        continue
                        
                    # log(f"  - {loc_name} | {point_name} ({equip_code}): 温度={temp}℃, 湿度={hum}%RH, 电量={elec}%")
                    
                    # 报警判断逻辑
                    try:
                        temp_val = float(temp)
                        elec_str = str(elec)
                        elec_val = int(elec_str.replace('%', '')) if '%' in elec_str else int(float(elec_str))
                        
                        temp_alarm_type = None
                        temp_threshold = None
                        
                        if temp_val > -19:
                            temp_alarm_type = "库温过高报警"
                            temp_threshold = -19
                        elif temp_val < -21:
                            temp_alarm_type = "库温过低报警"
                            temp_threshold = -21
                            
                        if temp_alarm_type:
                            log(f"    [ALARM] 触发报警: {temp_alarm_type} (当前: {temp_val}degC, 阈值: {temp_threshold}degC)")
                            insert_alarm({
                                'storage_name': STORAGE_NAME,
                                'location_name': loc_name,
                                'monitor_point_name': point_name,
                                'device_number': equip_code,
                                'alarm_type': temp_alarm_type,
                                'current_value': temp_val,
                                'threshold': temp_threshold,
                                'alarm_time': timestamp
                            })
                            
                        if elec_val < LOW_BATTERY_ALARM_THRESHOLD:
                            log(f"    [ALARM] 触发报警: 电池低电量报警 (当前: {elec_val}%, 阈值: {LOW_BATTERY_ALARM_THRESHOLD}%)")
                            insert_alarm({
                                'storage_name': STORAGE_NAME,
                                'location_name': loc_name,
                                'monitor_point_name': point_name,
                                'device_number': equip_code,
                                'alarm_type': "电池低电量报警",
                                'current_value': elec_val,
                                'threshold': LOW_BATTERY_ALARM_THRESHOLD,
                                'alarm_time': timestamp
                            })
                            
                    except Exception as e:
                        log(f"    [ERROR] 报警判断出错: {e}")

                    # 保存到 MySQL 数据库
                    insert_data({
                        'collection_time': timestamp,
                        'storage_name': STORAGE_NAME,
                        'location_name': loc_name,
                        'monitor_point_name': point_name,
                        'device_number': equip_code,
                        'temperature': temp,
                        'humidity': hum,
                        'battery': elec,
                        'data_time': gps_time
                    })
                    log(f"  - 保存数据: {loc_name} | {point_name} | Temp={temp} | Time={gps_time}")
                    count += 1
            
            if count == 0:
                 log("  (未找到有效温湿度数据)")
            else:
                log(f"成功保存 {count} 条监测点数据")

        else:
            log(f"接口调用失败: {result.get('message', '未知错误')} (Code: {result.get('code')})")
            
    except Exception as e:
        log(f"请求发生异常: {e}")

if __name__ == "__main__":
    try:
        log("=" * 60)
        log(" G7 数据采集服务启动中...")
        log(f" 目标仓库: {STORAGE_NAME}")
        
        # 初始化数据库
        init_db()
        
        log(" 开始定时采集数据，每 300 秒(5分钟)采集一次...")
        log("=" * 60)
        
        while True:
            try:
                fetch_equip_data()
            except Exception as e:
                log(f"采集循环发生未捕获异常: {e}")
            
            time.sleep(300)
    except Exception as e:
        log(f"服务发生致命错误，即将退出: {e}")
        sys.exit(1)
