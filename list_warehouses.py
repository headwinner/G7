import hashlib
import requests
import json
from datetime import datetime

# ==================== 配置区域 ====================
APP_KEY = "0545F4D9-F0C3-48F2-A576-E1A846A6D33A" 
APP_SECRET = "6941524B-BD39-4016-9191-8DE3393D8437"

# API 请求地址 (4.38 按仓库名称或编码获取区位&监测点信息)
API_URL = "https://api.e6yun.com/public/v4/BL-MODULE-COLD-CHAIN-WEB/api/cold/storageManage/getStorageInfoList"
# ==================================================

def generate_sign(secret_key, params):
    """
    签名算法
    """
    sorted_keys = sorted([k for k in params.keys() if k != 'sign'])
    param_str = "".join([f"{k}{params[k]}" for k in sorted_keys])
    sign_str = f"{secret_key}{param_str}{secret_key}"
    
    m = hashlib.md5()
    m.update(sign_str.encode('utf-8'))
    return m.hexdigest().upper()

def list_warehouses():
    """
    调用 4.38 接口获取仓库列表
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构造请求参数
    params = {
        "method": "getStorageInfoList",
        "timestamp": timestamp,
        "format": "json",
        "storageName": "-1", # -1 表示查询所有仓库
        "appkey": APP_KEY
    }
    
    # 计算签名
    params["sign"] = generate_sign(APP_SECRET, params)
    
    print(f"\n[{timestamp}] 发起请求, 接口: {API_URL}")
    print(f"请求参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(API_URL, data=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("code") == 1:
            data = result.get("data", [])
            print(f"\n✅ 获取成功，共找到 {len(data)} 个仓库:")
            for item in data:
                storage_name = item.get("storageName", "未知名称")
                storage_code = item.get("storageCode", "无编码")
                print(f"  - 仓库名称: {storage_name} (编码: {storage_code})")
        else:
            print(f"❌ 接口调用失败: {result.get('message', '未知错误')} (Code: {result.get('code')})")
            
    except Exception as e:
        print(f"❌ 请求发生异常: {e}")

if __name__ == "__main__":
    list_warehouses()
