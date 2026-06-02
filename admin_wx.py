import wx
import wx.xrc
import wx.adv
import gettext
import requests
import logging
import os
from config.config import *
from typing import List, Dict, Any

_ = gettext.gettext

# API配置
API_VERSION = "1.0"
API_BASE_URL = "http://localhost:5000/v1"

# API端点
API_ENDPOINTS = {
    'login': '/login',
    'register': '/register',
    'users': '/users',
    'ban': '/ban',
    'unban': '/unban',
    'set_admin': '/set-admin',
    'balance': '/balance',
    'announcements': '/announcements',
    'change_password': '/change-password',
}

# 公告类型
ANNOUNCEMENT_TYPES = ['system', 'maintenance', 'update', 'other']

# 确保日志目录存在
if not os.path.exists('log'):
    os.makedirs('log')

# 配置日志系统
logging.basicConfig(
    filename='log/admin.log',
    format='%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s',
    level=logging.DEBUG,
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """API错误基类"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class ValidationError(APIError):
    """数据验证错误"""
    pass

class AuthenticationError(APIError):
    """认证错误"""
    pass

class PermissionError(APIError):
    """权限错误"""
    pass

class ResourceNotFoundError(APIError):
    """资源不存在错误"""
    pass

class APIClient:
    """API客户端类，处理与服务器的所有HTTP通信"""
    
    _instance = None
    _session = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_session(cls):
        """获取或创建会话对象"""
        if cls._session is None:
            cls._session = requests.Session()
            # 设置通用请求头
            cls._session.headers.update({
                'User-Agent': 'AdminClient/1.0',
                'Accept': 'application/json',
                'X-API-Version': API_VERSION
            })
        return cls._session
    
    @classmethod
    def clear_session(cls):
        """清除会话"""
        if cls._session:
            cls._session.close()
            cls._session = None
    
    @classmethod
    def make_request(cls, method: str, endpoint: str, data: dict = None, params: dict = None) -> requests.Response:
        """
        发送API请求并处理响应
        
        Args:
            method: HTTP方法（GET, POST, PUT, DELETE）
            endpoint: API端点
            data: 请求体数据
            params: URL参数
            
        Returns:
            requests.Response: API响应对象
            
        Raises:
            ValidationError: 数据验证失败
            AuthenticationError: 认证失败
            PermissionError: 权限不足
            ResourceNotFoundError: 资源不存在
            APIError: 其他API错误
        """
        url = f"{API_BASE_URL}{endpoint}"
        session = cls.get_session()
        
        try:
            # 发送请求
            if method.upper() == 'GET':
                response = session.get(url, params=params)
            elif method.upper() == 'POST':
                response = session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = session.delete(url)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查API版本
            if 'api_version' in response.headers:
                if response.headers['api_version'] != API_VERSION:
                    logger.warning(f"API版本不匹配: 期望{API_VERSION}, 实际{response.headers['api_version']}")
            
            # 处理错误响应
            if response.status_code >= 400:
                error_data = response.json()
                error_msg = error_data.get('error', '未知错误')
                
                if response.status_code == 400:
                    raise ValidationError(error_msg, response.status_code)
                elif response.status_code == 401:
                    cls.clear_session()  # 清除会话
                    raise AuthenticationError(error_msg, response.status_code)
                elif response.status_code == 403:
                    raise PermissionError(error_msg, response.status_code)
                elif response.status_code == 404:
                    raise ResourceNotFoundError(error_msg, response.status_code)
                else:
                    raise APIError(error_msg, response.status_code)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            raise APIError(f"API请求失败: {str(e)}")
        except ValueError as e:
            logger.error(f"数据解析失败: {str(e)}")
            raise APIError(f"数据解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise APIError(f"未知错误: {str(e)}")
    
    @classmethod
    def handle_error_response(cls, response: requests.Response) -> None:
        """处理错误响应"""
        try:
            error_data = response.json()
            error_msg = error_data.get('error', '未知错误')
            raise APIError(error_msg, response.status_code)
        except ValueError:
            raise APIError(f"无效的错误响应: {response.text}", response.status_code)

class UserManageDialog(wx.Dialog):
    """用户管理对话框，用于显示和管理用户列表"""
    
    def __init__(self, parent):
        super().__init__(parent, title="用户管理", size=(1000, 700))
        
        # 创建主面板和布局
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建用户列表控件
        self.user_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.user_list.InsertColumn(0, "ID", width=50)
        self.user_list.InsertColumn(1, "用户名", width=120)
        self.user_list.InsertColumn(2, "角色", width=80)
        self.user_list.InsertColumn(3, "状态", width=80)
        self.user_list.InsertColumn(4, "余额", width=100)
        self.user_list.InsertColumn(5, "注册时间", width=150)
        
        # 添加搜索面板
        search_panel = wx.Panel(panel)
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        search_label = wx.StaticText(search_panel, label="搜索用户：")
        self.search_input = wx.TextCtrl(search_panel)
        search_btn = wx.Button(search_panel, label="搜索")
        search_sizer.Add(search_label, 0, wx.ALL | wx.CENTER, 5)
        search_sizer.Add(self.search_input, 1, wx.ALL | wx.EXPAND, 5)
        search_sizer.Add(search_btn, 0, wx.ALL, 5)
        search_panel.SetSizer(search_sizer)
        
        # 添加按钮面板
        button_panel = wx.Panel(panel)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.ban_btn = wx.Button(button_panel, label="封禁用户")
        self.unban_btn = wx.Button(button_panel, label="解封用户")
        self.set_admin_btn = wx.Button(button_panel, label="设置管理员")
        self.adjust_balance_btn = wx.Button(button_panel, label="调整余额")
        self.refresh_btn = wx.Button(button_panel, label="刷新列表")
        
        button_sizer.Add(self.ban_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.unban_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.set_admin_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.adjust_balance_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        button_panel.SetSizer(button_sizer)
        
        # 添加到主布局
        main_sizer.Add(search_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.user_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(button_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.ban_btn.Bind(wx.EVT_BUTTON, self.on_ban_user)
        self.unban_btn.Bind(wx.EVT_BUTTON, self.on_unban_user)
        self.set_admin_btn.Bind(wx.EVT_BUTTON, self.on_set_admin)
        self.adjust_balance_btn.Bind(wx.EVT_BUTTON, self.on_adjust_balance)
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        search_btn.Bind(wx.EVT_BUTTON, self.on_search)
        
        # 加载用户列表
        self.load_users()
        
        # 设置自动刷新定时器
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(30000)  # 每30秒刷新一次
        
    def on_timer(self, event):
        """定时器事件处理"""
        self.load_users()
        
    def load_users(self, search_text=""):
        """加载用户列表"""
        try:
            params = {}
            if search_text:
                params['search'] = search_text
                
            response = APIClient.make_request('GET', API_ENDPOINTS['users'], params=params)
            users = response.json().get('users', [])
            
            self.user_list.DeleteAllItems()
            for user in users:
                index = self.user_list.GetItemCount()
                self.user_list.InsertItem(index, str(user['id']))
                self.user_list.SetItem(index, 1, user['username'])
                self.user_list.SetItem(index, 2, user['role'])
                self.user_list.SetItem(index, 3, "已封禁" if user['is_banned'] else "正常")
                self.user_list.SetItem(index, 4, f"{user['balance']:.2f}")
                self.user_list.SetItem(index, 5, user['created_at'])
                
        except Exception as e:
            wx.MessageBox(f"加载用户列表失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            logger.error(f"加载用户列表失败: {str(e)}")
    
    def on_search(self, event):
        """搜索用户"""
        search_text = self.search_input.GetValue().strip()
        self.load_users(search_text)
    
    def get_selected_user_id(self):
        """获取选中的用户ID"""
        index = self.user_list.GetFirstSelected()
        if index == -1:
            wx.MessageBox("请先选择一个用户", "提示", wx.OK | wx.ICON_INFORMATION)
            return None
        return self.user_list.GetItem(index, 0).GetText()
    
    def on_ban_user(self, event):
        """封禁用户"""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
            
        # 确认对话框
        if wx.MessageBox("确定要封禁该用户吗？", "确认",
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
            return
            
        dlg = wx.TextEntryDialog(self, "请输入封禁原因：", "封禁用户")
        if dlg.ShowModal() == wx.ID_OK:
            reason = dlg.GetValue()
            try:
                response = APIClient.make_request('POST', f"{API_ENDPOINTS['ban']}/{user_id}",
                                                data={'reason': reason})
                wx.MessageBox("用户已被封禁", "成功", wx.OK | wx.ICON_INFORMATION)
                self.load_users()
            except Exception as e:
                wx.MessageBox(f"封禁用户失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                logger.error(f"封禁用户失败: {str(e)}")
        dlg.Destroy()
    
    def on_unban_user(self, event):
        """解封用户"""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
            
        # 确认对话框
        if wx.MessageBox("确定要解封该用户吗？", "确认",
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
            return
            
        try:
            response = APIClient.make_request('POST', f"{API_ENDPOINTS['unban']}/{user_id}")
            wx.MessageBox("用户已被解封", "成功", wx.OK | wx.ICON_INFORMATION)
            self.load_users()
        except Exception as e:
            wx.MessageBox(f"解封用户失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            logger.error(f"解封用户失败: {str(e)}")
    
    def on_set_admin(self, event):
        """设置管理员"""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
            
        # 确认对话框
        if wx.MessageBox("确定要将该用户设置为管理员吗？", "确认",
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
            return
            
        try:
            response = APIClient.make_request('POST', f"{API_ENDPOINTS['set_admin']}/{user_id}")
            wx.MessageBox("已将用户设置为管理员", "成功", wx.OK | wx.ICON_INFORMATION)
            self.load_users()
        except Exception as e:
            wx.MessageBox(f"设置管理员失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            logger.error(f"设置管理员失败: {str(e)}")
    
    def on_adjust_balance(self, event):
        """调整余额"""
        user_id = self.get_selected_user_id()
        if not user_id:
            return
            
        dlg = wx.TextEntryDialog(self, "请输入调整金额（正数增加，负数减少）：", "调整余额")
        if dlg.ShowModal() == wx.ID_OK:
            try:
                amount = float(dlg.GetValue())
                
                # 确认对话框
                if wx.MessageBox(f"确定要{'增加' if amount > 0 else '减少'} {abs(amount)} 余额吗？", 
                               "确认", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
                    return
                    
                response = APIClient.make_request('POST', f"{API_ENDPOINTS['balance']}/{user_id}",
                                                data={'amount': amount})
                wx.MessageBox("余额已调整", "成功", wx.OK | wx.ICON_INFORMATION)
                self.load_users()
            except ValueError:
                wx.MessageBox("请输入有效的数字", "错误", wx.OK | wx.ICON_ERROR)
            except Exception as e:
                wx.MessageBox(f"调整余额失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                logger.error(f"调整余额失败: {str(e)}")
        dlg.Destroy()
    
    def on_refresh(self, event):
        """刷新用户列表"""
        self.load_users()
        
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'timer'):
            self.timer.Stop()

class AnnouncementManageDialog(wx.Dialog):
    """公告管理对话框"""
    
    def __init__(self, parent):
        super().__init__(parent, title="公告管理", size=(1000, 700))
        
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建公告列表
        self.announcement_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.announcement_list.InsertColumn(0, "ID", width=50)
        self.announcement_list.InsertColumn(1, "标题", width=200)
        self.announcement_list.InsertColumn(2, "类型", width=100)
        self.announcement_list.InsertColumn(3, "状态", width=80)
        self.announcement_list.InsertColumn(4, "创建时间", width=150)
        
        # 添加按钮面板
        button_panel = wx.Panel(panel)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.create_btn = wx.Button(button_panel, label="创建公告")
        self.edit_btn = wx.Button(button_panel, label="编辑公告")
        self.delete_btn = wx.Button(button_panel, label="删除公告")
        self.refresh_btn = wx.Button(button_panel, label="刷新列表")
        
        button_sizer.Add(self.create_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.edit_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.delete_btn, 0, wx.ALL, 5)
        button_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        button_panel.SetSizer(button_sizer)
        
        # 添加到主布局
        main_sizer.Add(self.announcement_list, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(button_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.create_btn.Bind(wx.EVT_BUTTON, self.on_create)
        self.edit_btn.Bind(wx.EVT_BUTTON, self.on_edit)
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        
        # 加载公告列表
        self.load_announcements()
        
        # 设置自动刷新定时器
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(30000)  # 每30秒刷新一次
        
    def on_timer(self, event):
        """定时器事件处理"""
        self.load_announcements()
    
    def load_announcements(self):
        """加载公告列表"""
        try:
            response = APIClient.make_request('GET', API_ENDPOINTS['announcements'])
            announcements = response.json().get('announcements', [])
            
            self.announcement_list.DeleteAllItems()
            for ann in announcements:
                index = self.announcement_list.GetItemCount()
                self.announcement_list.InsertItem(index, str(ann['id']))
                self.announcement_list.SetItem(index, 1, ann['title'])
                self.announcement_list.SetItem(index, 2, ann['type'])
                self.announcement_list.SetItem(index, 3, "激活" if ann['is_active'] else "未激活")
                self.announcement_list.SetItem(index, 4, ann['created_at'])
                
        except Exception as e:
            wx.MessageBox(f"加载公告列表失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            logger.error(f"加载公告列表失败: {str(e)}")
    
    def get_selected_announcement_id(self):
        """获取选中的公告ID"""
        index = self.announcement_list.GetFirstSelected()
        if index == -1:
            wx.MessageBox("请先选择一个公告", "提示", wx.OK | wx.ICON_INFORMATION)
            return None
        return self.announcement_list.GetItem(index, 0).GetText()
    
    def show_announcement_dialog(self, title="", content="", ann_type="system", is_edit=False):
        """显示公告编辑对话框"""
        dlg = wx.Dialog(self, title="编辑公告" if is_edit else "创建公告", size=(500, 400))
        
        panel = wx.Panel(dlg)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题输入
        title_label = wx.StaticText(panel, label="标题：")
        title_input = wx.TextCtrl(panel, value=title)
        
        # 内容输入
        content_label = wx.StaticText(panel, label="内容：")
        content_input = wx.TextCtrl(panel, value=content, style=wx.TE_MULTILINE)
        
        # 类型选择
        type_label = wx.StaticText(panel, label="类型：")
        type_choice = wx.Choice(panel, choices=['system', 'maintenance', 'update', 'other'])
        type_choice.SetStringSelection(ann_type)
        
        # 按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, "确定")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "取消")
        
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        
        # 添加到主布局
        sizer.Add(title_label, 0, wx.ALL, 5)
        sizer.Add(title_input, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(content_label, 0, wx.ALL, 5)
        sizer.Add(content_input, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(type_label, 0, wx.ALL, 5)
        sizer.Add(type_choice, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        if dlg.ShowModal() == wx.ID_OK:
            return {
                'title': title_input.GetValue(),
                'content': content_input.GetValue(),
                'type': type_choice.GetStringSelection()
            }
        return None
    
    def on_create(self, event):
        """创建新公告"""
        data = self.show_announcement_dialog()
        if data:
            try:
                response = APIClient.make_request('POST', API_ENDPOINTS['announcements'], data=data)
                wx.MessageBox("公告创建成功", "成功", wx.OK | wx.ICON_INFORMATION)
                self.load_announcements()
            except Exception as e:
                wx.MessageBox(f"创建公告失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                logger.error(f"创建公告失败: {str(e)}")
    
    def on_edit(self, event):
        """编辑公告"""
        ann_id = self.get_selected_announcement_id()
        if not ann_id:
            return
            
        # 获取当前公告信息
        index = self.announcement_list.GetFirstSelected()
        title = self.announcement_list.GetItem(index, 1).GetText()
        ann_type = self.announcement_list.GetItem(index, 2).GetText()
        
        data = self.show_announcement_dialog(title=title, ann_type=ann_type, is_edit=True)
        if data:
            try:
                response = APIClient.make_request('PUT', f"{API_ENDPOINTS['announcements']}/{ann_id}",
                                                data=data)
                wx.MessageBox("公告更新成功", "成功", wx.OK | wx.ICON_INFORMATION)
                self.load_announcements()
            except Exception as e:
                wx.MessageBox(f"更新公告失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                logger.error(f"更新公告失败: {str(e)}")
    
    def on_delete(self, event):
        """删除公告"""
        ann_id = self.get_selected_announcement_id()
        if not ann_id:
            return
            
        # 确认对话框
        if wx.MessageBox("确定要删除这条公告吗？", "确认",
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
            return
            
        try:
            response = APIClient.make_request('DELETE', f"{API_ENDPOINTS['announcements']}/{ann_id}")
            wx.MessageBox("公告已删除", "成功", wx.OK | wx.ICON_INFORMATION)
            self.load_announcements()
        except Exception as e:
            wx.MessageBox(f"删除公告失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
            logger.error(f"删除公告失败: {str(e)}")
    
    def on_refresh(self, event):
        """刷新公告列表"""
        self.load_announcements()
        
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'timer'):
            self.timer.Stop()

class LoginDialog(wx.Dialog):
    """管理员登录对话框"""
    
    def __init__(self, parent):
        super().__init__(parent, title="管理员登录", size=(400, 200))
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 用户名输入
        username_sizer = wx.BoxSizer(wx.HORIZONTAL)
        username_label = wx.StaticText(panel, label="用户名：")
        self.username_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        username_sizer.Add(username_label, 0, wx.ALL | wx.CENTER, 5)
        username_sizer.Add(self.username_input, 1, wx.ALL | wx.EXPAND, 5)
        
        # 密码输入
        password_sizer = wx.BoxSizer(wx.HORIZONTAL)
        password_label = wx.StaticText(panel, label="密码：")
        self.password_input = wx.TextCtrl(panel, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        password_sizer.Add(password_label, 0, wx.ALL | wx.CENTER, 5)
        password_sizer.Add(self.password_input, 1, wx.ALL | wx.EXPAND, 5)
        
        # 按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        login_button = wx.Button(panel, wx.ID_OK, "登录")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, "取消")
        button_sizer.Add(login_button, 1, wx.ALL | wx.EXPAND, 5)
        button_sizer.Add(cancel_button, 1, wx.ALL | wx.EXPAND, 5)
        
        # 添加到主布局
        sizer.Add(username_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(password_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)
        
        panel.SetSizer(sizer)
        self.Centre()
        
        # 绑定回车键事件
        self.username_input.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        self.password_input.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        
        # 设置默认按钮
        login_button.SetDefault()
        
    def on_enter(self, event):
        """处理回车键事件"""
        self.EndModal(wx.ID_OK)
    
    def get_credentials(self):
        """获取用户输入的凭据"""
        return {
            'username': self.username_input.GetValue().strip(),
            'password': self.password_input.GetValue().strip()
        }

class AdminApp(wx.App):
    """管理员应用程序类"""
    
    def OnInit(self):
        """应用程序初始化"""
        # 显示登录对话框
        login_dlg = LoginDialog(None)
        if login_dlg.ShowModal() == wx.ID_OK:
            credentials = login_dlg.get_credentials()
            try:
                # 尝试登录
                response = APIClient.make_request('POST', API_ENDPOINTS['login'], data=credentials)
                data = response.json()
                
                # 验证是否是管理员
                if not data.get('is_admin', False):
                    wx.MessageBox("您不是管理员，无法访问管理面板", "权限错误", wx.OK | wx.ICON_ERROR)
                    login_dlg.Destroy()
                    return False
                
                # 保存用户信息
                self.user_info = {
                    'username': credentials['username'],
                    'is_admin': True,
                    'role': 'admin'
                }
                
                # 显示主窗口
                frame = AdminFrame()
                frame.Show()
                login_dlg.Destroy()
                return True
                
            except AuthenticationError as e:
                wx.MessageBox("用户名或密码错误", "登录失败", wx.OK | wx.ICON_ERROR)
                login_dlg.Destroy()
                return False
            except Exception as e:
                wx.MessageBox(f"登录失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                login_dlg.Destroy()
                return False
        else:
            login_dlg.Destroy()
            return False

class AdminFrame(wx.Frame):
    """管理员主窗口"""
    
    def __init__(self):
        super().__init__(None, title="号码检测系统 - 管理员控制面板", size=(900, 700))
        
        # 设置图标和背景颜色
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusbar = self.CreateStatusBar(2)
        self.statusbar.SetStatusWidths([-2, -1])
        self.update_status_bar()
        
        # 创建主面板
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 添加标题
        title_text = wx.StaticText(panel, label="管理员控制面板")
        font = title_text.GetFont()
        font.SetPointSize(16)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title_text.SetFont(font)
        main_sizer.Add(title_text, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        # 添加分隔线
        line = wx.StaticLine(panel)
        main_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        # 创建功能区
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 左侧功能按钮面板
        left_panel = wx.Panel(panel)
        left_panel.SetBackgroundColour(wx.Colour(230, 230, 230))
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 添加功能按钮
        self.user_manage_btn = self.create_button(left_panel, "用户管理", "管理系统用户账号")
        self.announcement_btn = self.create_button(left_panel, "公告管理", "管理系统公告")
        self.change_pwd_btn = self.create_button(left_panel, "修改密码", "修改当前账号密码")
        self.logout_btn = self.create_button(left_panel, "退出登录", "退出当前账号")
        
        left_sizer.Add(self.user_manage_btn, 0, wx.EXPAND | wx.ALL, 10)
        left_sizer.Add(self.announcement_btn, 0, wx.EXPAND | wx.ALL, 10)
        left_sizer.Add(self.change_pwd_btn, 0, wx.EXPAND | wx.ALL, 10)
        left_sizer.Add(self.logout_btn, 0, wx.EXPAND | wx.ALL, 10)
        
        left_panel.SetSizer(left_sizer)
        
        # 右侧信息面板
        right_panel = wx.Panel(panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 系统信息
        info_box = wx.StaticBox(right_panel, label="系统信息")
        info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)
        
        # 添加系统信息内容
        self.system_info = wx.TextCtrl(right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.system_info.SetBackgroundColour(wx.Colour(250, 250, 250))
        self.update_system_info()
        
        info_sizer.Add(self.system_info, 1, wx.EXPAND | wx.ALL, 10)
        
        # 最近公告
        announcement_box = wx.StaticBox(right_panel, label="最近公告")
        announcement_sizer = wx.StaticBoxSizer(announcement_box, wx.VERTICAL)
        
        self.announcement_list = wx.ListCtrl(right_panel, style=wx.LC_REPORT)
        self.announcement_list.InsertColumn(0, "标题", width=200)
        self.announcement_list.InsertColumn(1, "类型", width=100)
        self.announcement_list.InsertColumn(2, "时间", width=150)
        
        announcement_sizer.Add(self.announcement_list, 1, wx.EXPAND | wx.ALL, 10)
        
        # 添加到右侧布局
        right_sizer.Add(info_sizer, 1, wx.EXPAND | wx.ALL, 10)
        right_sizer.Add(announcement_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        right_panel.SetSizer(right_sizer)
        
        # 添加到内容布局
        content_sizer.Add(left_panel, 0, wx.EXPAND | wx.ALL, 10)
        content_sizer.Add(right_panel, 1, wx.EXPAND | wx.ALL, 10)
        
        # 添加到主布局
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.user_manage_btn.Bind(wx.EVT_BUTTON, self.on_user_manage)
        self.announcement_btn.Bind(wx.EVT_BUTTON, self.on_announcement_manage)
        self.change_pwd_btn.Bind(wx.EVT_BUTTON, self.on_change_password)
        self.logout_btn.Bind(wx.EVT_BUTTON, self.on_logout)
        
        # 设置定时器更新状态
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(60000)  # 每分钟更新一次
        
        # 加载最近公告
        self.load_recent_announcements()
        
        self.Centre()
    
    def create_button(self, parent, label, tooltip=""):
        """创建统一风格的按钮"""
        btn = wx.Button(parent, label=label, size=(-1, 50))
        btn.SetToolTip(tooltip)
        font = btn.GetFont()
        font.SetPointSize(12)
        btn.SetFont(font)
        return btn
    
    def update_status_bar(self):
        """更新状态栏信息"""
        now = wx.DateTime.Now()
        date_str = now.FormatDate()
        time_str = now.FormatTime()
        self.statusbar.SetStatusText(f"当前时间: {date_str} {time_str}", 0)
        self.statusbar.SetStatusText("已连接到服务器", 1)
    
    def update_system_info(self):
        """更新系统信息"""
        try:
            # 获取系统信息
            info_text = f"""
系统版本: 号码检测系统 v1.0
API版本: {API_VERSION}
服务器: {API_BASE_URL}
登录状态: 已登录
登录时间: {wx.DateTime.Now().FormatDate()} {wx.DateTime.Now().FormatTime()}
            """
            self.system_info.SetValue(info_text.strip())
        except Exception as e:
            logger.error(f"更新系统信息失败: {str(e)}")
    
    def load_recent_announcements(self):
        """加载最近公告"""
        try:
            response = APIClient.make_request('GET', API_ENDPOINTS['announcements'], params={'active_only': True, 'limit': 5})
            announcements = response.json().get('announcements', [])
            
            self.announcement_list.DeleteAllItems()
            for ann in announcements:
                index = self.announcement_list.GetItemCount()
                self.announcement_list.InsertItem(index, ann['title'])
                self.announcement_list.SetItem(index, 1, ann['type'])
                self.announcement_list.SetItem(index, 2, ann['created_at'])
                
        except Exception as e:
            logger.error(f"加载最近公告失败: {str(e)}")
    
    def on_timer(self, event):
        """定时器事件处理"""
        self.update_status_bar()
        self.load_recent_announcements()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        change_pwd_item = file_menu.Append(wx.ID_ANY, "修改密码(&P)\tCtrl+P")
        file_menu.AppendSeparator()
        logout_item = file_menu.Append(wx.ID_ANY, "退出登录(&L)")
        exit_item = file_menu.Append(wx.ID_EXIT, "退出(&X)\tAlt+F4")
        menubar.Append(file_menu, "文件(&F)")
        
        # 管理菜单
        manage_menu = wx.Menu()
        user_item = manage_menu.Append(wx.ID_ANY, "用户管理(&U)\tCtrl+U")
        announcement_item = manage_menu.Append(wx.ID_ANY, "公告管理(&A)\tCtrl+A")
        menubar.Append(manage_menu, "管理(&M)")
        
        # 视图菜单
        view_menu = wx.Menu()
        refresh_item = view_menu.Append(wx.ID_ANY, "刷新(&R)\tF5")
        menubar.Append(view_menu, "视图(&V)")
        
        # 帮助菜单
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "关于(&A)")
        menubar.Append(help_menu, "帮助(&H)")
        
        self.SetMenuBar(menubar)
        
        # 绑定菜单事件
        self.Bind(wx.EVT_MENU, self.on_change_password, change_pwd_item)
        self.Bind(wx.EVT_MENU, self.on_logout, logout_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_user_manage, user_item)
        self.Bind(wx.EVT_MENU, self.on_announcement_manage, announcement_item)
        self.Bind(wx.EVT_MENU, self.on_refresh, refresh_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
    
    def on_user_manage(self, event):
        """打开用户管理对话框"""
        dlg = UserManageDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
    
    def on_announcement_manage(self, event):
        """打开公告管理对话框"""
        dlg = AnnouncementManageDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
    
    def on_change_password(self, event):
        """修改密码"""
        dlg = wx.PasswordEntryDialog(self, "请输入当前密码:", "修改密码")
        if dlg.ShowModal() == wx.ID_OK:
            old_password = dlg.GetValue()
            dlg.Destroy()
            
            # 输入新密码
            dlg = wx.PasswordEntryDialog(self, "请输入新密码:", "修改密码")
            if dlg.ShowModal() == wx.ID_OK:
                new_password = dlg.GetValue()
                dlg.Destroy()
                
                # 确认新密码
                dlg = wx.PasswordEntryDialog(self, "请再次输入新密码:", "修改密码")
                if dlg.ShowModal() == wx.ID_OK:
                    confirm_password = dlg.GetValue()
                    dlg.Destroy()
                    
                    if new_password != confirm_password:
                        wx.MessageBox("两次输入的密码不一致", "错误", wx.OK | wx.ICON_ERROR)
                        return
                    
                    try:
                        response = APIClient.make_request('POST', API_ENDPOINTS['change_password'], 
                                                        data={'old_password': old_password, 'new_password': new_password})
                        wx.MessageBox("密码修改成功，请重新登录", "成功", wx.OK | wx.ICON_INFORMATION)
                        self.on_logout(None)
                    except Exception as e:
                        wx.MessageBox(f"修改密码失败：{str(e)}", "错误", wx.OK | wx.ICON_ERROR)
                else:
                    dlg.Destroy()
            else:
                dlg.Destroy()
        else:
            dlg.Destroy()
    
    def on_logout(self, event):
        """退出登录"""
        if wx.MessageBox("确定要退出登录吗？", "确认", 
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
            APIClient.clear_session()
            self.Destroy()
            
            # 重新启动应用
            app = AdminApp()
            app.MainLoop()
    
    def on_refresh(self, event):
        """刷新界面"""
        self.update_status_bar()
        self.update_system_info()
        self.load_recent_announcements()
    
    def on_exit(self, event):
        """退出程序"""
        if wx.MessageBox("确定要退出程序吗？", "确认", 
                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
            APIClient.clear_session()
            self.Destroy()
    
    def on_about(self, event):
        """显示关于对话框"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("号码检测系统")
        info.SetVersion("1.0")
        info.SetDescription("号码检测系统管理员控制面板")
        info.SetCopyright("(C) 2024")
        info.SetWebSite("http://www.example.com")
        info.AddDeveloper("开发团队")
        wx.adv.AboutBox(info)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'timer'):
            self.timer.Stop()

if __name__ == '__main__':
    app = AdminApp()
    app.MainLoop()

