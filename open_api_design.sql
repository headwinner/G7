-- ==========================================================
-- 开放平台 (Open API) 数据库表设计
-- 用于管理第三方用户的 AppKey、AppSecret 以及调用日志
-- ==========================================================

-- 1. 第三方接入用户表
-- 存储第三方公司的基本信息以及分配的鉴权凭证
CREATE TABLE IF NOT EXISTS `open_api_users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `company_name` VARCHAR(100) NOT NULL COMMENT '所属公司名称',
    `contact_name` VARCHAR(50) NOT NULL COMMENT '联系人姓名',
    `contact_phone` VARCHAR(20) NOT NULL COMMENT '联系人手机号',
    `app_key` VARCHAR(64) NOT NULL UNIQUE COMMENT '分配给第三方应用的AppKey (唯一标识)',
    `app_secret` VARCHAR(128) NOT NULL COMMENT '分配给第三方应用的AppSecret (签名密钥)',
    `status` TINYINT(1) DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    `qps_limit` INT DEFAULT 10 COMMENT '限流: 每秒允许的最大请求数 (可选)',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='开放平台第三方用户表';

-- 2. 接口调用日志表
-- 用于审计、排错和统计第三方用户的调用行为
CREATE TABLE IF NOT EXISTS `open_api_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `app_key` VARCHAR(64) NOT NULL COMMENT '调用的AppKey',
    `company_name` VARCHAR(100) COMMENT '调用方公司名称',
    `contact_name` VARCHAR(50) COMMENT '调用方联系人',
    `api_endpoint` VARCHAR(100) NOT NULL COMMENT '请求的接口路由或方法名',
    `request_ip` VARCHAR(50) COMMENT '请求方IP',
    `response_code` INT COMMENT '业务响应状态码 (如 200, 401, 500)',
    `cost_time_ms` INT COMMENT '接口处理耗时(毫秒)',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '请求发生时间',
    INDEX `idx_app_key` (`app_key`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='开放平台接口调用日志表';

-- 3. 数据权限配置表 (可选扩展)
-- 如果某些第三方只能获取特定仓库的数据，可以通过此表进行权限控制
CREATE TABLE IF NOT EXISTS `open_api_data_permissions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `app_key` VARCHAR(64) NOT NULL COMMENT '对应的AppKey',
    `resource_type` VARCHAR(50) NOT NULL COMMENT '资源类型 (如: storage_name)',
    `resource_value` VARCHAR(100) NOT NULL COMMENT '允许访问的资源值 (如: 福建汉吉斯冷链物流有限公司)',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY `uk_appkey_resource` (`app_key`, `resource_type`, `resource_value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='开放平台数据权限控制表';

-- ==========================================================
-- 插入一条测试数据供开发调试
-- ==========================================================
INSERT IGNORE INTO `open_api_users` 
(`company_name`, `contact_name`, `contact_phone`, `app_key`, `app_secret`) 
VALUES 
('测试合作公司A', '张三', '13800138000', 'DEMO_APP_KEY_2024', 'DEMO_SECRET_ABC123XYZ890');
