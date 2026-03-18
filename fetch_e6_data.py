import time
import hashlib
import requests
from datetime import datetime
import json
import os
import sqlite3

# ==================== 配置区域 ====================
# 使用易流平台获取的 appkey 和 appsecret
APP_KEY = "0545F4D9-F0C3-48F2-A576-E1A846A6D33A" 
APP_SECRET = "6941524B-BD39-4016-9191-8DE3393D8437"

# 仓库名称（根据图片）
STORAGE_NAME = "福建汉吉斯冷链物流有限公司"

# API 请求地址 (4.39 获取仓库最新温湿度数据)
API_URL = "https://api.e6yun.com/public/v4/BL-MODULE-COLD-CHAIN-WEB/api/cold/storageTempHum/getStorageTempHum"

# 本地数据存储目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# 数据库文件路径
DB_PATH = os.path.join(DATA_DIR, "device_data.db")
# ==================================================

def init_db():
    """
    初始化 SQLite 数据库并创建数据表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_time TEXT,
            storage_name TEXT,
            location_name TEXT,
            monitor_point_name TEXT,
            device_number TEXT,
            temperature REAL,
            humidity REAL,
            battery INTEGER,
            data_time TEXT
        )
    ''')
    
    # 检查 alarm_records 表结构是否匹配，如果不匹配则删除重建
    # (为了简化逻辑，这里通过检查字段是否存在或顺序来判断，或者直接重建)
    # 鉴于用户要求严格按照截图结构，我们采用重建策略以确保字段顺序和名称一致
    try:
        cursor.execute("PRAGMA table_info(alarm_records)")
        columns = [info[1] for info in cursor.fetchall()]
        expected_columns = ['id', 'storage_name', 'location_name', 'monitor_point_name', 'device_number', 'alarm_type', 'current_value', 'threshold', 'alarm_time']
        
        # 如果列名或数量不一致，则重建表
        # 注意：这里会清空旧的报警数据，如果需要保留请先备份
        if columns != expected_columns:
            print("检测到 alarm_records 表结构变更，正在重建表...")
            cursor.execute("DROP TABLE IF EXISTS alarm_records")
    except Exception as e:
        print(f"检查表结构时出错: {e}")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarm_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            storage_name TEXT,
            location_name TEXT,
            monitor_point_name TEXT,
            device_number TEXT,
            alarm_type TEXT,
            current_value REAL,
            threshold REAL,
            alarm_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ==================== CRUD 操作 ====================
def insert_alarm(alarm_dict):
    """
    插入一条报警记录
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO alarm_records (
            storage_name, location_name, monitor_point_name, device_number, 
            alarm_type, current_value, threshold, alarm_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

def query_alarms(limit=10, offset=0, alarm_type=None):
    """
    查询报警记录
    alarm_type: 报警类型筛选
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM alarm_records'
    params = []
    
    if alarm_type:
        query += ' WHERE alarm_type = ?'
        params.append(alarm_type)
        
    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_alarm(record_id, update_dict):
    """
    更新报警记录
    update_dict: 需要更新的字段字典
    """
    if not update_dict:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{k} = ?" for k in update_dict.keys()])
    params = list(update_dict.values())
    params.append(record_id)
    
    cursor.execute(f'UPDATE alarm_records SET {set_clause} WHERE id = ?', params)
    conn.commit()
    conn.close()

def delete_alarm(record_id):
    """
    删除一条报警记录
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alarm_records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

def insert_data(data_dict):
    """
    插入一条温湿度数据
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO device_data (
            collection_time, storage_name, location_name, monitor_point_name,
            device_number, temperature, humidity, battery, data_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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

def query_data(limit=10, offset=0):
    """
    查询温湿度数据
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM device_data ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_data(record_id, update_dict):
    """
    更新温湿度数据
    """
    if not update_dict:
        return
    
    set_clause = ", ".join([f"{k} = ?" for k in update_dict.keys()])
    values = list(update_dict.values())
    values.append(record_id)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'UPDATE device_data SET {set_clause} WHERE id = ?', values)
    conn.commit()
    conn.close()

def delete_data(record_id):
    """
    删除一条温湿度数据
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM device_data WHERE id = ?', (record_id,))
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
    print(f"\n[{timestamp}] 发起请求, 接口: {API_URL}")
    print(f"请求参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求 (application/x-www-form-urlencoded)
        response = requests.post(API_URL, data=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        # 打印返回结果供调试
        # print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("code") == 1:
            data = result.get("data", {})
            location_list = data.get("locationList", [])
            
            print(f"[{timestamp}] 数据采集成功，获取到 {len(location_list)} 个区位的数据:")
            
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
                        
                    print(f"  - {loc_name} | {point_name} ({equip_code}): 温度={temp}℃, 湿度={hum}%RH, 电量={elec}%")
                    
                    # 报警判断逻辑
                    # 以-19℃为基准，高于-17℃报警过高，低于-21℃报警过低
                    # 电量低于15%报警
                    try:
                        temp_val = float(temp)
                        # 处理电量数据，可能是数字或带%的字符串
                        elec_str = str(elec)
                        elec_val = int(elec_str.replace('%', '')) if '%' in elec_str else int(float(elec_str))
                        
                        # 1. 温度报警判断
                        temp_alarm_type = None
                        temp_threshold = None
                        
                        if temp_val > -17:
                            temp_alarm_type = "库温过高报警"
                            temp_threshold = -17
                        elif temp_val < -21:
                            temp_alarm_type = "库温过低报警"
                            temp_threshold = -21
                            
                        if temp_alarm_type:
                            print(f"    ⚠️ 触发报警: {temp_alarm_type} (当前: {temp_val}℃, 阈值: {temp_threshold}℃)")
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
                            
                        # 2. 电量报警判断
                        if elec_val < 15:
                            print(f"    ⚠️ 触发报警: 电池低电量报警 (当前: {elec_val}%, 阈值: 15%)")
                            insert_alarm({
                                'storage_name': STORAGE_NAME,
                                'location_name': loc_name,
                                'monitor_point_name': point_name,
                                'device_number': equip_code,
                                'alarm_type': "电池低电量报警",
                                'current_value': elec_val,
                                'threshold': 15,
                                'alarm_time': timestamp
                            })
                            
                    except Exception as e:
                        print(f"    ❌ 报警判断出错: {e}")

                    # 保存到 SQLite 数据库
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
                    count += 1
            
            if count == 0:
                 print("  (未找到有效温湿度数据)")

        else:
            print(f"[{timestamp}] 接口调用失败: {result.get('message', '未知错误')} (Code: {result.get('code')})")
            
    except Exception as e:
        print(f"[{timestamp}] 请求发生异常: {e}")

if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    print("=" * 60)
    print(" 开始定时采集仓库温湿度数据 (接口 4.39)，每 300 秒(5分钟)采集一次...")
    print(f" 目标仓库: {STORAGE_NAME}")
    print(f" 数据将保存在: {DB_PATH} 数据库中")
    print(" (按 Ctrl+C 停止运行)")
    print("=" * 60)
    
    while True:
        fetch_equip_data()
        time.sleep(300)
