# Flask用户认证系统API文档

## 系统配置
系统配置位于 `config/config.py`，支持多环境配置：

### 环境配置
- **开发环境** (`development`)
- **测试环境** (`testing`)
- **生产环境** (`production`)

可通过环境变量 `FLASK_ENV` 指定运行环境，默认为 `development`。

### 主要配置项
1. **API版本配置**:
   - 当前版本: `1.0`
   - 支持版本: `["1.0"]`

2. **用户配置**:
   - 用户名长度: 3-80字符
   - 密码长度: 6-120字符
   - 初始余额: 0.0

3. **安全配置**:
   - `SECRET_KEY`: 用于会话加密
   - 生产环境必须通过环境变量设置

4. **数据库配置**:
   - 开发环境: SQLite (`sqlite:///users.db`)
   - 生产环境: 通过环境变量 `DATABASE_URL` 设置

5. **公告配置**:
   - 标题最大长度: 100字符
   - 内容最大长度: 1000字符
   - 支持的公告类型: ['system', 'maintenance', 'update', 'other']

## 设备池配置
1. **Redis配置**:
   - Redis连接URL: `redis://localhost:6379/0`
   - 设备池键前缀: `device_pool:`
   - 未使用设备池: `device_pool:unused`
   - 使用中设备池: `device_pool:using`

2. **设备池参数**:
   - 默认池大小: 100个设备
   - 设备超时时间: 90秒
   - 设备创建重试次数: 3次
   - 设备创建超时: 30秒

3. **代理配置**:
   - 代理模式: '2'（隧道代理）或其他（提取式代理）
   - 代理URL: 通过环境变量或配置文件设置
   - 代理认证: 用户名和密码配置

## 基础信息
- 基础URL: `http://localhost:5000`
- 当前API版本: `1.0`
- 所有请求和响应均使用JSON格式
- 需要认证的接口使用`@login_required`标记
- 管理员专属接口使用`@admin_required`标记

## API版本控制
系统支持两种方式指定API版本：

1. URL前缀方式：
   - 所有接口都以 `/v1/` 开头，例如：`/v1/login`

2. 请求头方式：
   - 在请求头中添加 `X-API-Version` 字段
   - 例如：`X-API-Version: 1.0`

当前支持的版本：
- 1.0 (当前版本)

所有接口响应中都会包含 `api_version` 字段，表示当前使用的API版本。

## 错误处理机制

### 错误类型
系统定义了以下几种错误类型：

1. **验证错误** (400 Bad Request)
   - 请求参数缺失或格式错误
   - 数据验证失败
   - 用户名或密码不符合要求

2. **认证错误** (401 Unauthorized)
   - 未登录或会话过期
   - 访问需要认证的接口时未提供登录凭证
   - 响应示例：
   ```json
   {
       "error": "请先登录",
       "api_version": "1.0"
   }
   ```

3. **权限错误** (403 Forbidden)
   - 无管理员权限
   - 账户被封禁
   - 尝试操作未授权资源

4. **资源不存在** (404 Not Found)
   - 请求的资源不存在
   - 用户不存在
   - 公告不存在

5. **方法不允许** (405 Method Not Allowed)
   - 对资源使用了不支持的HTTP方法
   - 例如：对只支持POST的接口使用GET请求

6. **服务器错误** (500 Internal Server Error)
   - 数据库操作失败
   - 未预期的系统错误

### 错误响应格式
所有错误响应都遵循统一的格式：
```json
{
    "error": "错误描述信息",
    "api_version": "1.0"
}
```

对于405错误，响应中会包含允许的方法列表：
```json
{
    "error": "不支持的请求方法：GET",
    "allowed_methods": ["POST", "PUT"],
    "api_version": "1.0"
}
```

## 接口列表

### 1. 用户注册
- **URL**: `/v1/register`
- **方法**: `POST`
- **权限**: 无需认证
- **请求体**:
```json
{
    "username": "用户名",
    "password": "密码"
}
```
- **响应示例**:
```json
{
    "message": "注册成功",
    "role": "user",
    "api_version": "1.0"
}
```
- **错误情况**:
  - 用户名长度不符合要求（3-80字符）
  - 密码长度不符合要求（最少6字符）
  - 用户名已存在
  - 缺少必要参数

### 2. 用户登录
- **URL**: `/v1/login`
- **方法**: `POST`
- **权限**: 无需认证
- **请求体**:
```json
{
    "username": "用户名",
    "password": "密码"
}
```
- **响应示例**:
```json
{
    "message": "登录成功",
    "role": "user",
    "is_admin": false,
    "api_version": "1.0"
}
```

### 3. 查询余额
- **URL**: `/v1/balance`
- **方法**: `GET`
- **权限**: 需要登录
- **响应示例**:
```json
{
    "balance": 100.0,
    "api_version": "1.0"
}
```

### 4. 修改余额
- **URL**: `/v1/balance/<user_id>`
- **方法**: `POST`
- **权限**: 需要登录（修改他人余额需要管理员权限）
- **请求体**:
```json
{
    "amount": 100.0  // 可以为负数
}
```
- **响应示例**:
```json
{
    "message": "余额更新成功",
    "new_balance": 200.0,
    "api_version": "1.0"
}
```

### 5. 封禁用户
- **URL**: `/v1/ban/<user_id>`
- **方法**: `POST`
- **权限**: 仅管理员
- **请求体**:
```json
{
    "reason": "封禁原因"
}
```
- **响应示例**:
```json
{
    "message": "用户 username 已被封禁",
    "api_version": "1.0"
}
```

### 6. 解封用户
- **URL**: `/v1/unban/<user_id>`
- **方法**: `POST`
- **权限**: 仅管理员
- **响应示例**:
```json
{
    "message": "用户 username 已被解封",
    "api_version": "1.0"
}
```

### 7. 设置管理员
- **URL**: `/v1/set-admin/<user_id>`
- **方法**: `POST`
- **权限**: 仅管理员
- **响应示例**:
```json
{
    "message": "用户 username 已被设置为管理员",
    "api_version": "1.0"
}
```

### 8. 获取用户列表
- **URL**: `/v1/users`
- **方法**: `GET`
- **权限**: 仅管理员
- **响应示例**:
```json
{
    "users": [
        {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "is_banned": false,
            "balance": 100.0,
            "created_at": "2024-01-01T12:00:00"
        }
    ],
    "api_version": "1.0"
}
```

### 9. 修改密码
- **URL**: `/v1/change-password`
- **方法**: `POST`
- **权限**: 需要登录
- **请求体**:
```json
{
    "old_password": "旧密码",
    "new_password": "新密码"
}
```
- **响应示例**:
```json
{
    "message": "密码修改成功，请重新登录",
    "api_version": "1.0"
}
```
- **特别说明**:
  - 密码修改成功后会自动登出用户
  - 用户需要使用新密码重新登录
  - 新密码必须符合密码长度要求（最少6个字符）

### 10. 创建公告
- **URL**: `/v1/announcements`
- **方法**: `POST`
- **权限**: 仅管理员
- **请求体**:
```json
{
    "title": "公告标题",
    "content": "公告内容",
    "type": "公告类型"  // system, maintenance, update, other
}
```
- **响应示例**:
```json
{
    "message": "公告创建成功",
    "announcement_id": 1,
    "api_version": "1.0"
}
```

### 11. 获取公告列表
- **URL**: `/v1/announcements`
- **方法**: `GET`
- **权限**: 无需认证
- **Query参数**:
  - `type`: 公告类型（可选）
  - `active_only`: 是否只返回激活的公告（可选，默认true）
- **响应示例**:
```json
{
    "announcements": [
        {
            "id": 1,
            "title": "系统维护公告",
            "content": "系统将于今晚进行维护",
            "type": "maintenance",
            "created_by": 1,
            "created_at": "2024-01-01T12:00:00",
            "is_active": true
        }
    ],
    "api_version": "1.0"
}
```

### 12. 更新公告
- **URL**: `/v1/announcements/<announcement_id>`
- **方法**: `PUT`
- **权限**: 仅管理员
- **请求体**:
```json
{
    "title": "新公告标题",     // 可选
    "content": "新公告内容",   // 可选
    "type": "新公告类型",     // 可选
    "is_active": true        // 可选
}
```
- **响应示例**:
```json
{
    "message": "公告更新成功",
    "api_version": "1.0"
}
```

### 13. 删除公告
- **URL**: `/v1/announcements/<announcement_id>`
- **方法**: `DELETE`
- **权限**: 仅管理员
- **响应示例**:
```json
{
    "message": "公告删除成功",
    "api_version": "1.0"
}
```

### 14. 查询单个账号
- **URL**: `/v1/query/account`
- **方法**: `POST`
- **权限**: 需要登录
- **请求体**:
```json
{
    "area": "+1",
    "phone": "1234567890"
}
```
- **响应示例**:
```json
{
    "message": "查询成功",
    "data": {
        "area": "+1",
        "phone": "1234567890",
        "user_name": "用户昵称",
        "year": "注册时间",
        "status": "账号状态"  // 正常老号/封禁号/锁定账号/未注册号
    },
    "api_version": "1.0"
}
```
- **错误响应**:
```json
{
    "error": "查询失败，请稍后重试",
    "api_version": "1.0"
}
```

### 15. 批量查询账号
- **URL**: `/v1/query/accounts/batch`
- **方法**: `POST`
- **权限**: 需要登录
- **请求体**:
```json
{
    "phones": [
        {
            "area": "+1",
            "phone": "1234567890"
        },
        {
            "area": "+1",
            "phone": "0987654321"
        }
    ],
    "max_workers": 3  // 可选，默认3
}
```
- **响应示例**:
```json
{
    "message": "查询成功",
    "data": [
        {
            "area": "+1",
            "phone": "1234567890",
            "user_name": "用户1",
            "year": "2022",
            "status": "正常老号"
        },
        {
            "area": "+1",
            "phone": "0987654321",
            "user_name": "用户2",
            "year": "2023",
            "status": "封禁号"
        }
    ],
    "api_version": "1.0"
}
```

### 16. 获取设备池状态
- **URL**: `/v1/query/pool/status`
- **方法**: `GET`
- **权限**: 仅管理员
- **响应示例**:
```json
{
    "message": "获取成功",
    "data": {
        "unused_count": 80,
        "using_count": 20,
        "total_count": 100,
        "target_size": 100
    },
    "api_version": "1.0"
}
```

## 账号状态说明

1. **正常老号**:
   - 账号正常使用中
   - 可以查看注册时间和用户名

2. **封禁号**:
   - 账号已被平台封禁
   - account_status_code = 7

3. **锁定账号**:
   - 账号被临时锁定
   - 可能需要验证或解封

4. **未注册号**:
   - 手机号未注册抖音账号

5. **查询失败**:
   - 查询过程出现异常
   - 需要重试

## 设备池机制

1. **设备创建**:
   - 按需创建设备
   - 设备有效期为90秒
   - 支持设备创建重试

2. **设备使用**:
   - 从设备池获取设备
   - 使用后归还到设备池
   - 过期设备自动丢弃

3. **设备状态**:
   - 未使用：等待被使用的设备
   - 使用中：正在执行查询的设备
   - 已过期：超过有效期的设备会被丢弃

## 数据验证规则

### 用户名要求
- 最小长度：3个字符
- 最大长度：80个字符
- 必须唯一

### 密码要求
- 最小长度：6个字符
- 最大长度：120个字符

### 公告标题
- 最大长度：100个字符

### 公告内容
- 最大长度：1000个字符

### 公告类型
支持的类型：
- system（系统公告）
- maintenance（维护公告）
- update（更新公告）
- other（其他公告）

### 封禁原因
- 最大长度：200个字符

## 环境配置

### 开发环境
- 调试模式：开启
- 日志级别：DEBUG
- 数据库：SQLite (users.db)

### 测试环境
- 调试模式：关闭
- 日志级别：DEBUG
- 数据库：SQLite (test.db)

### 生产环境
- 调试模式：关闭
- 日志级别：WARNING
- 数据库：需要通过环境变量 DATABASE_URL 设置
- 必需的环境变量：
  - SECRET_KEY
  - DATABASE_URL
  - REDIS_URL
  - PROXY_URL

## 日志记录

系统会记录以下类型的日志：

### 操作日志
- 用户注册
- 用户登录
- 余额变动
- 用户封禁/解封
- 公告管理
- 账号查询

### 错误日志
- API错误
- 参数验证错误
- 权限错误
- 系统错误
- 设备创建错误
- 查询失败错误

### 日志格式
```
时间戳 [日志级别] 模块名:行号 - 日志内容
```

### 日志配置
- 日志文件位置：logs/app.log
- 单个日志文件大小限制：10MB
- 保留历史日志数量：5个文件

## 注意事项
1. 首个注册的用户自动成为管理员
2. 管理员账户不能被封禁
3. 余额可以为负数
4. 所有需要认证的接口都需要先登录
5. 修改他人余额需要管理员权限
6. 建议始终使用最新版本的API
7. 设备有效期为90秒，过期后会自动丢弃
8. 批量查询时建议控制并发数，避免过高并发导致查询失败

## 使用示例

### 注册新用户
```bash
curl -X POST http://localhost:5000/v1/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user", "password":"123456"}'
```

### 用户登录
```bash
curl -X POST http://localhost:5000/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user", "password":"123456"}'
```

### 查询余额
```bash
curl -X GET http://localhost:5000/v1/balance
```

### 修改余额
```bash
curl -X POST http://localhost:5000/v1/balance/1 \
  -H "Content-Type: application/json" \
  -d '{"amount":100}'
```

### 封禁用户
```bash
curl -X POST http://localhost:5000/v1/ban/1 \
  -H "Content-Type: application/json" \
  -d '{"reason":"违规行为"}'
```

### 修改密码
```bash
curl -X POST http://localhost:5000/v1/change-password \
  -H "Content-Type: application/json" \
  -d '{"old_password":"123456", "new_password":"new123456"}'
```

### 单个查询
```bash
curl -X POST http://localhost:5000/v1/query/account \
  -H "Content-Type: application/json" \
  -d '{
    "area": "+1",
    "phone": "1234567890"
  }'
```

### 批量查询
```bash
curl -X POST http://localhost:5000/v1/query/accounts/batch \
  -H "Content-Type: application/json" \
  -d '{
    "phones": [
      {"area": "+1", "phone": "1234567890"},
      {"area": "+1", "phone": "0987654321"}
    ],
    "max_workers": 3
  }'
```

### 查看设备池状态
```bash
curl -X GET http://localhost:5000/v1/query/pool/status
``` 