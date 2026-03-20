# 开放平台 API 接入规范文档 (V1.0)

本文档面向第三方开发者，详细介绍了如何通过平台分配的凭证（AppKey 和 AppSecret）安全地调用本系统的开放接口，以获取设备温湿度、电量及报警记录等数据。

---

## 1. 基础规范说明

### 1.1 凭证获取
在正式调用接口前，您需要向本平台管理员申请接入凭证。审核通过后，您将获得：
- **`appkey`**: 您的应用唯一标识，每次调用接口时必须作为公共参数传入明文。
- **`appsecret`**: 您的应用安全密钥，**仅用于在客户端本地计算生成签名，绝对禁止在网络请求中传输**。

### 1.2 接口环境与通讯协议
- **通讯协议**: HTTP / HTTPS
- **请求方式**: `POST` (推荐) 或 `GET`
- **数据格式**: 推荐使用 `application/json` 作为请求与响应的 Content-Type。
- **基础 URL**: 
  - 生产环境: `http://1.94.137.200:15898` （请替换为实际绑定的域名）

### 1.3 公共请求参数
**所有业务接口**在发起请求时，都必须包含以下公共鉴权参数：

| 参数名 | 类型 | 必填 | 描述 | 示例值 |
| :--- | :--- | :--- | :--- | :--- |
| `appkey` | String | 是 | 平台分配给您的应用唯一标识 | `DEMO_APP_KEY_2024` |
| `timestamp` | String | 是 | 请求发生的时间戳，格式必须为：`YYYY-MM-DD HH:mm:ss`。为防重放攻击，该时间与服务器时间相差超过 **5分钟** 将被拒绝访问 | `2026-03-19 12:00:00` |
| `sign` | String | 是 | 接口防篡改签名，由其他参数与 Secret 动态计算得出。算法详见[第2节](#2-签名机制-signature) | `A64185C16D7ED13337944CC5B399BF0B` |

---

## 2. 签名机制 (Signature)

为了防止请求参数在网络传输过程中被非法篡改，本平台强制要求对请求进行 MD5 签名校验。

### 2.1 签名算法详细步骤

1. **参数剔除**：将所有的请求参数（包括公共参数和业务参数），剔除掉 `sign` 字段本身以及可能存在的文件类型参数。
2. **参数排序**：将剩余的所有参数，按照参数名称（Key）的 **ASCII 码进行字典序升序** 排列。
3. **参数拼接**：将排序后的参数，以 `Key + Value` 的格式紧密拼接成一个长字符串（不加任何连接符）。若 Value 为 JSON 对象或数组，需先将其序列化为紧凑的 JSON 字符串再拼接。
4. **首尾加盐**：在拼接好的长字符串的**最前面和最后面**，都拼接上您的 `appsecret`。
5. **MD5 加密**：对最终的字符串进行标准 MD5 哈希计算，并将得到的 32 位十六进制字符串**全部转换为大写**，即为您最终的 `sign` 值。

### 2.2 签名计算示例

假设您拥有的凭证和本次请求参数如下：
- **AppSecret**: `SECRET123`
- **请求参数**: 
  - `appkey` = `DEMO_KEY`
  - `timestamp` = `2026-03-19 10:00:00`
  - `method` = `get_device_data`

**第一步：排序**
按字母顺序排列 Key：`appkey` -> `method` -> `timestamp`

**第二步：拼接**
`appkeyDEMO_KEYmethodget_device_datatimestamp2026-03-19 10:00:00`

**第三步：首尾加盐 (Secret)**
`SECRET123appkeyDEMO_KEYmethodget_device_datatimestamp2026-03-19 10:00:00SECRET123`

**第四步：MD5 加密并转大写**
计算结果即为：`5B3454796B079F459EDBD347F9611D36`

---

## 3. 业务接口列表

### 3.1 查询设备温湿度及电量数据

用于获取冷链仓库中各个监测点设备的最新或历史温湿度及电池电量信息。

- **接口路由**: `/api/v1/device/getData`  
- **请求方式**: `POST`

#### 业务请求参数：

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `method` | String | 是 | 固定值：`get_device_data` （必须传入以参与签名） |
| `storage_name` | String | 否 | 仓库名称筛选。不传则默认返回您名下有权限的所有仓库数据 |
| `limit` | Integer | 否 | 限制返回的最新数据条数，默认为 6 条 |

#### 请求示例 (JSON Body):
```json
{
    "appkey": "DEMO_APP_KEY_2024",
    "timestamp": "2026-03-19 14:30:00",
    "method": "get_device_data",
    "storage_name": "福建汉吉斯冷链物流有限公司",
    "limit": 5,
    "sign": "E5136B26A0..."
}
```

#### 响应参数说明：

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `code` | Integer | 状态码，`200` 表示成功 |
| `msg` | String | 提示信息 |
| `data` | Array | 数据列表，包含具体的设备信息对象 |
| `data[].collection_time` | String | 数据采集时间 |
| `data[].device_number` | String | 物理设备唯一编号 |
| `data[].temperature` | Float | 实时温度 (℃) |
| `data[].humidity` | Float | 实时湿度 (%RH) |
| `data[].battery` | Integer | 设备剩余电量百分比 (0-100) |
| `data[].location_name` | String | 所在库区名称 |
| `data[].monitor_point_name` | String | 具体监测点位名称 |
| `data[].storage_name` | String | 所属仓库名称 |

#### 响应示例:
```json
{
    "code": 200,
    "msg": "success",
    "caller_company": "测试合作公司A",
    "data": [
        {
            "collection_time": "2026-03-19 17:52:17",
            "device_number": "TW125700193",
            "temperature": -19.0,
            "humidity": 51.0,
            "battery": 96,
            "location_name": "冷冻区1-1-C",
            "monitor_point_name": "1-1-C-02",
            "storage_name": "福建汉吉斯冷链物流有限公司"
        }
    ]
}
```

---

### 3.2 查询设备报警记录

用于获取设备的超温、超湿、低电量等历史报警触发记录。

- **接口路由**: `/api/v1/device/getAlarms`  
- **请求方式**: `POST`

#### 业务请求参数：

| 参数名 | 类型 | 必填 | 描述 |
| :--- | :--- | :--- | :--- |
| `method` | String | 是 | 固定值：`get_alarm_records` （必须传入以参与签名） |
| `storage_name` | String | 否 | 仓库名称筛选 |
| `limit` | Integer | 否 | 限制返回的最新记录条数，默认为 10 条 |

#### 响应参数说明：

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `data[].alarm_time` | String | 报警触发时间 |
| `data[].alarm_type` | String | 报警类型 (如: 超温报警、探头离线等) |
| `data[].current_value` | Float | 触发报警时的实时数值 |
| `data[].threshold` | Float | 设定的报警阈值 |
| `data[].device_number` | String | 触发报警的设备编号 |

#### 响应示例:
```json
{
    "code": 200,
    "msg": "success",
    "caller_company": "测试合作公司A",
    "data": [
        {
            "alarm_time": "2026-03-19 10:00:00",
            "device_number": "TW125700193",
            "alarm_type": "超温报警",
            "current_value": -10.5,
            "threshold": -18.0,
            "location_name": "冷冻区1-1-C",
            "monitor_point_name": "1-1-C-02",
            "storage_name": "福建汉吉斯冷链物流有限公司"
        }
    ]
}
```

---

## 4. 全局状态码说明 (Error Codes)

在调用接口时，若 `code` 不为 `200`，请对照以下表格进行排查：

| 状态码 (`code`) | 错误信息 (`msg`) | 产生原因及解决方案 |
| :--- | :--- | :--- |
| `200` | success | 请求处理成功。 |
| `400` | 缺少必要参数 / 时间戳格式错误 | 请检查是否漏传了 `appkey`、`timestamp` 或 `sign`，且 `timestamp` 格式必须为标准的 `YYYY-MM-DD HH:mm:ss`。 |
| `401` | 无效的 appkey | 您传入的 `appkey` 在系统中不存在，请联系管理员核对。 |
| `401` | 请求已过期或时间戳不准确 | 您传入的 `timestamp` 与服务器当前时间误差超过 5 分钟，请求被拒绝。请校准客户端服务器的时间。 |
| `401` | 签名错误 | 您计算出的 `sign` 与服务器端计算的不一致。请严格按照 [签名机制](#2-签名机制-signature) 检查：是否遗漏了参数？排序是否正确？Secret 拼接是否正确？ |
| `403` | 该 AppKey 已被禁用 | 您的凭证已被系统管理员停用，请联系管理员恢复。 |
| `500` | 服务端错误: xxx | 平台内部逻辑异常或数据库连接失败，请保留错误信息并反馈给技术支持。 |

---

## 5. 客户端调用示例

### 5.1 Python 示例代码
以下提供一个标准的 Python `requests` 调用示例，演示了如何动态生成时间戳、计算签名并发起请求。

```python
import hashlib
import requests
from datetime import datetime

# 1. 配置凭证与接口地址
APP_KEY = "DEMO_APP_KEY_2024"
APP_SECRET = "DEMO_SECRET_ABC123XYZ890"
API_URL = "http://1.94.137.200:15898/api/v1/device/getData"

# 2. 构造基础参数
params = {
    "appkey": APP_KEY,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "method": "get_device_data",
    "storage_name": "福建汉吉斯冷链物流有限公司",
    "limit": 5
}

# 3. 核心签名算法
# 3.1 提取并按字典序排序所有的 key
sorted_keys = sorted([k for k in params.keys()])

# 3.2 拼接 KeyValue 字符串
param_str = "".join([f"{k}{params[k]}" for k in sorted_keys])

# 3.3 首尾加盐
sign_str = f"{APP_SECRET}{param_str}{APP_SECRET}"

# 3.4 MD5 计算并转大写
m = hashlib.md5()
m.update(sign_str.encode('utf-8'))
params['sign'] = m.hexdigest().upper()

# 4. 发送 POST 请求
try:
    print(f"请求参数: {params}")
    response = requests.post(API_URL, json=params)
    print("响应结果:", response.json())
except Exception as e:
    print("网络请求失败:", e)
```

### 5.2 Postman (Pre-request Script) 调试代码
在 Postman 中调试时，将以下代码粘贴到请求的 `Pre-request Script` 中，即可实现每次点击 Send 时自动计算并注入签名。

```javascript
const APP_SECRET = "您的AppSecret";

function getFormattedTime() {
    const now = new Date();
    const pad = (n) => (n < 10 ? '0' + n : n);
    return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

let rawBody = pm.request.body.raw;
let params = rawBody ? JSON.parse(rawBody) : {};
params['timestamp'] = getFormattedTime();

const sortedKeys = Object.keys(params).sort();
let paramStr = "";
for (let i = 0; i < sortedKeys.length; i++) {
    let key = sortedKeys[i];
    if (key !== 'sign') {
        let val = typeof params[key] === 'object' ? JSON.stringify(params[key]) : params[key];
        paramStr += key + val;
    }
}

const signStr = APP_SECRET + paramStr + APP_SECRET;
const sign = CryptoJS.MD5(signStr).toString().toUpperCase();

params['sign'] = sign;
pm.request.body.raw = JSON.stringify(params);
console.log("【自动签名生成】:", sign);
```