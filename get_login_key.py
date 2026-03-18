import hashlib
import requests
from datetime import datetime

# 使用从截图提取的最新的 appkey 和 appsecret
APP_KEY = "0545F4D9-F0C3-48F2-A576-E1A846A6D33A" 
APP_SECRET = "6941524B-BD39-4016-9191-8DE3393D8437"

# 4.1 接口地址
API_URL = "https://api.e6yun.com/public/v4/BASIC/api/user/getLoginStr"

def generate_sign(secret_key, params):
    """
    签名算法：
    1. 根据传入参数名称（sign除外）将所有请求参数按照首字母先后顺序排序
    2. 拼接为 md5(密钥 + 排好序的参数串 + 密钥) 后转换为大写字母
    """
    sorted_keys = sorted([k for k in params.keys() if k != 'sign'])
    param_str = "".join([f"{k}{params[k]}" for k in sorted_keys])
    sign_str = f"{secret_key}{param_str}{secret_key}"
    
    m = hashlib.md5()
    m.update(sign_str.encode('utf-8'))
    return m.hexdigest().upper()

def get_login_key():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    params = {
        "method": "getLoginStr",
        "timestamp": timestamp,
        "format": "json",
        "appkey": APP_KEY
    }
    
    # 计算签名
    params["sign"] = generate_sign(APP_SECRET, params)
    
    print(f"正在调用 4.1 接口生成/获取免登密钥...")
    print(f"请求参数: {params}")
    
    try:
        response = requests.post(API_URL, data=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("code") == 1:
            data = result.get("data", {})
            login_key = data.get("loginKey", "")
            print("\n" + "="*50)
            print("✅ 成功获取免登易流云平台的密钥 (loginKey)!")
            print(f"🔑 密钥内容: {login_key}")
            print("="*50)
            return login_key
        else:
            print(f"❌ 请求失败: {result.get('message', '未知错误')} (Code: {result.get('code')})")
            
    except Exception as e:
        print(f"❌ 请求发生异常: {e}")

if __name__ == "__main__":
    get_login_key()
