# -*- coding: utf-8 -*-

# API配置
API_VERSION = "1.0"
API_BASE_URL = 'http://localhost:5000'
API_ENDPOINTS = {
    'login': '/v1/login',
    'register': '/v1/register',
    'balance': '/v1/balance',
    'change_password': '/v1/change-password',
    'announcements': '/v1/announcements',
    'query_single': '/v1/query/account',
    'query_batch': '/v1/query/accounts/batch',
    'pool_status': '/v1/query/pool/status'
}

# API请求头
API_HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Version': API_VERSION
}

# 公告配置
ANNOUNCEMENT_TYPES = ['system', 'maintenance', 'update', 'other']
ANNOUNCEMENT_CONFIG = {
    'title_max_length': 100,
    'content_max_length': 1000,
    'default_type': 'system'
}

# UI配置
UI_CONFIG = {
    'main_window': {
        'title': '号码检测系统',
        'size': (1000, 700),
        'background_color': (240, 240, 245)
    },
    'login_window': {
        'title': '用户登录',
        'size': (350, 220),
        'background_color': (240, 240, 245)
    }
}

# UI文本配置
UI_TEXTS = {
    'labels': {
        'username': '用户名：',
        'password': '密码：',
        'phone_prefix': '号码前缀',
        'phone_number': '手机号码',
        'user_label': '用户：{username}',
        'balance_label': '余额：{balance:.2f}',
        'status_bar': '当前用户：{username} ({role})',
        'query_status': '查询状态：{status}',
        'query_progress': '进度：{current}/{total}'
    },
    'buttons': {
        'login': '登录',
        'register': '注册',
        'batch_query': '批量查询',
        'stop': '停止',
        'single_query': '单条查询',
        'export': '导出数据',
        'clear': '清空列表'
    },
    'dialogs': {
        'export_title': '导出数据',
        'export_type_prompt': '请选择要导出的检测结果类型',
        'save_file': '保存文件',
        'change_pwd_title': '修改密码',
        'old_pwd_prompt': '请输入旧密码：',
        'new_pwd_prompt': '请输入新密码：',
        'announcement_title': '系统公告'
    }
}

# 列表视图配置
LIST_VIEW_COLUMNS = ["序号", '前缀', "号码", "归属地", "运营商", "邮编", "区号", "检测结果", "注册年份", "查询时间"]

# 文件配置
FILE_CONFIG = {
    'phone_prefix_file': 'config/phone_head.txt',
    'export_file_type': 'CSV文件 (*.csv)|*.csv'
}

# 检测结果状态
CHECK_STATUS = ['未检测', '检测成功', '检测失败']

# 版本信息
VERSION = '1.0'

# 菜单配置
MENU_CONFIG = {
    'file_menu': {
        'title': '文件',
        'items': [
            {'id': 'export', 'label': '导出数据'},
            {'id': 'exit', 'label': '退出'}
        ]
    },
    'user_menu': {
        'title': '用户',
        'items': [
            {'id': 'change_pwd', 'label': '修改密码'},
            {'id': 'refresh_balance', 'label': '刷新余额'}
        ]
    },
    'help_menu': {
        'title': '帮助',
        'items': [
            {'id': 'about', 'label': '关于'},
            {'id': 'notice', 'label': '查看公告'},
            {'id': 'refresh_notice', 'label': '刷新公告'}
        ]
    }
}

# 提示信息
MESSAGES = {
    'login_success': '登录成功！\n',
    'login_failed': '登录失败！\n',
    'register_success': '注册成功！请登录。\n',
    'register_failed': '注册失败！\n',
    'password_change_success': '密码修改成功！\n',
    'password_change_failed': '密码修改失败！\n',
    'balance_update_failed': '获取余额失败！\n',
    'export_no_data': '没有可导出的数据\n',
    'export_success': '成功导出{count}条数据\n',
    'export_failed': '导出失败：{error}\n',
    'phone_format_error': '错误：号码 {phone} 包含非数字字符\n',
    'phone_empty_error': '错误：号码不能为空\n',
    'phone_duplicate': '跳过重复号码：{phone}\n',
    'file_import_success': '成功导入文件：{filepath}\n',
    'file_import_failed': '导入失败：{error}\n',
    'prefix_file_not_found': '号码前缀文件未找到\n',
    'prefix_load_failed': '加载前缀选项失败：{error}\n',
    'about_text': '号码检测系统\n版本：{version}\nAPI版本：{api_version}\n',
    'notice_text': '暂无公告',
    'notice_load_failed': '获取公告失败：{error}',
    'query_success': '查询成功\n',
    'query_failed': '查询失败：{error}\n',
    'query_in_progress': '正在查询中...\n',
    'query_stopped': '查询已停止\n',
    'query_completed': '查询完成，成功：{success}，失败：{failed}\n',
    'invalid_area_code': '无效的区号\n',
    'batch_size_exceeded': '批量查询数量超过限制（最大{limit}条）\n',
    'pool_status': '设备池状态：可用 {unused}，使用中 {using}，总计 {total}\n'
}

# 角色配置
ROLES = {
    'admin': '管理员',
    'user': '普通用户'
}

# 查询配置
QUERY_CONFIG = {
    'max_workers': 3,  # 默认最大并发数
    'retry_times': 3,  # 查询失败重试次数
    'retry_interval': 1,  # 重试间隔（秒）
    'batch_size': 100,  # 单次批量查询最大数量
    'status_types': ['正常老号', '封禁号', '锁定账号', '未注册号']
} 