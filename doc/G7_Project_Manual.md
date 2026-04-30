# G7 冷链温湿度采集与开放平台 API 项目文档

## 1. 项目简介

本项目旨在定期从易流平台（E6）获取指定仓库的温湿度及电量数据，持久化到本地 MySQL 数据库中，并通过 Flask 提供的 OpenAPI 接口对外提供数据查询服务。系统以双服务模式运行于 Windows 服务器上。

### 核心功能
*   **定时数据采集**：每 5 分钟调用 E6 平台 4.39 接口获取最新温湿度及设备电量。
*   **智能报警判断**：
    *   **温度报警**：高于 -17℃ 触发“库温过高报警”，低于 -21℃ 触发“库温过低报警”（基准 -19℃）。
    *   **电量报警**：电量低于 20% 时触发“电池低电量报警”。
*   **开放平台 API**：通过 `15898` 端口提供 RESTful 接口（支持签名鉴权、防重放攻击）供外部业务系统调用。
*   **后台静默运行**：使用 WinSW (Windows Service Wrapper) 封装为系统服务，实现开机自启、奔溃重启及日志自动切割。

---

## 2. 技术架构与依赖

*   **开发语言**：Python 3.x
*   **核心框架**：Flask (Web 框架)
*   **数据库**：MySQL (PyMySQL 驱动)
*   **网络请求**：Requests
*   **环境变量管理**：python-dotenv
*   **服务封装工具**：WinSW (Windows Service Wrapper)

### 依赖安装
```powershell
pip install pymysql requests python-dotenv flask
```

---

## 3. 目录结构说明

```text
c:\Trae\Github\G7\
├── config.py                 # 全局配置管理（环境映射）
├── db_config.py              # 数据库连接配置
├── fetch_e6_data.py          # 温湿度数据定时采集主程序
├── open_api_server.py        # 开放平台 API 服务主程序
├── .env.production           # 生产环境变量配置
├── logs/                     # 日志目录
│   ├── g7_api.err.log        # API 服务错误日志
│   ├── g7_api.out.log        # API 服务标准输出日志
│   ├── g7_fetcher.err.log    # 采集服务错误日志
│   ├── g7_fetcher.out.log    # 采集服务标准输出日志
│   └── python_debug.log      # Python 脚本自定义详细日志
├── g7_fetcher.exe            # 采集服务执行程序 (WinSW)
├── g7_fetcher.xml            # 采集服务配置
├── g7_api.exe                # API 服务执行程序 (WinSW)
└── g7_api.xml                # API 服务配置
```

---

## 4. 数据库设计 (`G7_device_data_fz`)

### 4.1. 核心表结构
系统在首次运行 `fetch_e6_data.py` 或 `open_api_server.py` 时，将自动检测并创建以下核心表（如需完整表结构，请参考 `open_api_design.sql`）：

*   **`device_data`**：存储每次采集到的温湿度、电量等原始数据。
*   **`alarm_records`**：存储触发阈值时的报警记录。
*   **`open_api_users`**：存储外部调用方信息（AppKey、AppSecret、状态）。
*   **`open_api_logs`**：记录外部 API 调用的访问日志（IP、耗时、状态码）。

### 4.2. 数据库连接配置
生产环境数据库连接参数位于 `.env.production` 文件中：
*   **Host**: `127.0.0.1`
*   **Port**: `3309` *(注：必须使用 3309，切勿混淆为 3306)*
*   **User**: `root`
*   **Password**: `root`

---

## 5. 运维管理指南 (Windows PowerShell)

本项目通过 WinSW 注册为 Windows 系统服务。所有运维操作**必须在管理员身份运行的 PowerShell 中执行**，且执行前必须进入项目目录。

### 5.1. 基础环境准备
```powershell
# 1. 以管理员身份打开 PowerShell
# 2. 进入项目根目录
cd c:\Trae\Github\G7
```

### 5.2. 数据采集服务 (`g7_fetcher`) 管理命令
该服务负责每 5 分钟拉取一次数据。

| 操作 | 命令 | 说明 |
| :--- | :--- | :--- |
| **查看状态** | `.\g7_fetcher.exe status` | 检查服务是否正在运行 (Started/Stopped) |
| **启动服务** | `.\g7_fetcher.exe start` | 启动后台采集脚本 |
| **停止服务** | `.\g7_fetcher.exe stop` | 停止后台采集 |
| **重启服务** | `.\g7_fetcher.exe restart` | **更新 Python 代码后，执行此命令生效** |
| **安装服务** | `.\g7_fetcher.exe install` | 首次部署或更新 XML 配置后执行 |
| **卸载服务** | `.\g7_fetcher.exe uninstall` | 从系统中彻底移除该服务 |

### 5.3. API 接口服务 (`g7_api`) 管理命令
该服务负责监听 `15898` 端口，提供对外接口。

| 操作 | 命令 | 说明 |
| :--- | :--- | :--- |
| **查看状态** | `.\g7_api.exe status` | 检查 API 服务是否在线 |
| **启动服务** | `.\g7_api.exe start` | 开启 15898 端口监听 |
| **停止服务** | `.\g7_api.exe stop` | 关闭 API 服务 |
| **重启服务** | `.\g7_api.exe restart` | **更新 Python 代码后，执行此命令生效** |
| **安装服务** | `.\g7_api.exe install` | 首次部署或更新 XML 配置后执行 |
| **卸载服务** | `.\g7_api.exe uninstall` | 移除服务 |

---

## 6. 常见问题排查 (Troubleshooting)

### 6.1. 修改了配置 (.xml) 如何生效？
如果修改了 `g7_fetcher.xml` 或 `g7_api.xml`（例如更改 Python 路径、环境变量或日志目录），必须执行完整的**卸载并重装**流程，单单 `restart` 是无效的：
```powershell
.\g7_fetcher.exe stop
.\g7_fetcher.exe uninstall
.\g7_fetcher.exe install
.\g7_fetcher.exe start
```

### 6.2. 如何查看运行日志？
日志统一存放在 `c:\Trae\Github\G7\logs` 目录下。

1.  **查看采集脚本的详细执行过程与报警信息（推荐）**：
    ```powershell
    Get-Content .\logs\python_debug.log -Wait
    ```
2.  **查看采集服务系统级报错**：
    ```powershell
    Get-Content .\logs\g7_fetcher.err.log -Tail 20
    ```
3.  **查看 API 服务报错**：
    ```powershell
    Get-Content .\logs\g7_api.err.log -Tail 20
    ```

### 6.3. 数据库明明有数据，但 Navicat 里看不到？
请检查 Navicat 的连接配置。本项目的生产环境数据库端口为 **`3309`**（定义在 `.env.production` 中），如果您连接了默认的 `3306` 端口，将看到一个空的数据库实例。

### 6.4. 服务启动失败或闪退？
*   检查 XML 配置文件中的 `<executable>` 路径是否正确指向了 `python.exe` 的绝对路径。
*   检查是否执行了 `pip install` 安装了必要的依赖库。
*   查看 `logs\g7_*.err.log` 文件中的 Python Traceback 信息。
