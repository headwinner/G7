import time
import hashlib
import requests
from datetime import datetime
import json
import os
import csv

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

def get_daily_log_file():
    """
    获取当天的日志文件路径
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DATA_DIR, f"device_data_{date_str}.csv")

def save_to_csv(data_row):
    """
    将采集到的数据追加写入当天的 CSV 文件
    """
    log_file = get_daily_log_file()
    file_exists = os.path.isfile(log_file)
    with open(log_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 如果文件不存在，写入表头
        if not file_exists:
            writer.writerow(["采集时间", "仓库名称", "区位名称", "监测点名称", "设备编号", "温度(℃)", "湿度(%RH)", "电量(%)", "数据时间"])
        writer.writerow(data_row)

def fetch_equip_data():
    """
    调用 4.39 接口获取仓库温湿度数据
    """
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
                    
                    # 保存到 CSV
                    save_to_csv([timestamp, STORAGE_NAME, loc_name, point_name, equip_code, temp, hum, elec, gps_time])
                    count += 1
            
            if count == 0:
                 print("  (未找到有效温湿度数据)")

        else:
            print(f"[{timestamp}] 接口调用失败: {result.get('message', '未知错误')} (Code: {result.get('code')})")
            
    except Exception as e:
        print(f"[{timestamp}] 请求发生异常: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print(" 开始定时采集仓库温湿度数据 (接口 4.39)，每 180 秒(3分钟)采集一次...")
    print(f" 目标仓库: {STORAGE_NAME}")
    print(f" 数据将保存在: {DATA_DIR} 目录下，每天自动生成新文件")
    print(" (按 Ctrl+C 停止运行)")
    print("=" * 60)
    
    while True:
        fetch_equip_data()
        time.sleep(180)
