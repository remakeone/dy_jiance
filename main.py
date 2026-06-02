# -*- coding: utf-8 -*-
"""
号码检测系统客户端
该模块实现了一个基于wxPython的GUI应用程序，用于手机号码的批量检测和管理。

主要功能：
1. 用户认证（登录/注册）
2. 号码检测（单条/批量）
3. 数据导出
4. 用户管理（余额查询、密码修改）
5. 公告系统
"""

from random import choice
import wx
import wx.xrc
import gettext
import requests
import logging
from config.config import *
import threading
import queue
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

_ = gettext.gettext

# 配置日志系统
logging.basicConfig(
    filename='log/app.log',
    format='%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s',
    level=logging.DEBUG,
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# HTTP代理配置，用于调试
proxies = {
    # "http":"http://127.0.0.1:8888",
    # "https":"http://127.0.0.1:8888",
}


class APIError(Exception):
    """API错误基类，用于处理所有API相关的异常"""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ValidationError(APIError):
    """数据验证错误，用于处理输入验证失败的情况"""
    pass


class AuthenticationError(APIError):
    """认证错误，用于处理登录失败、会话过期等情况"""
    pass


class PermissionError(APIError):
    """权限错误，用于处理权限不足的情况"""
    pass


class ResourceNotFoundError(APIError):
    """资源不存在错误，用于处理请求的资源不存在的情况"""
    pass


class APIClient:
    """
    API客户端类，处理与服务器的所有HTTP通信
    
    主要功能：
    - 维护会话状态
    - 处理API请求
    - 统一的错误处理
    - API版本控制
    """

    _session = None  # 类级别的会话对象，用于保持登录状态

    @classmethod
    def get_session(cls):
        """获取或创建会话对象，确保所有请求使用同一个会话"""
        if cls._session is None:
            cls._session = requests.Session()
            cls._session.headers.update(API_HEADERS)
        return cls._session

    @classmethod
    def clear_session(cls):
        """清除会话，用于登出或会话失效时"""
        if cls._session:
            cls._session.close()
            cls._session = None

    @classmethod
    def make_request(cls, method, endpoint, data=None, params=None):
        """
        发送API请求并处理响应
        
        Args:
            method (str): HTTP方法（GET, POST, PUT, DELETE）
            endpoint (str): API端点
            data (dict, optional): 请求体数据
            params (dict, optional): URL参数
            
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
            # 根据不同的HTTP方法发送请求
            if method.upper() == 'GET':
                response = session.get(url, params=params, proxies=proxies)
            elif method.upper() == 'POST':
                response = session.post(url, json=data, proxies=proxies)
            elif method.upper() == 'PUT':
                response = session.put(url, json=data, proxies=proxies)
            elif method.upper() == 'DELETE':
                response = session.delete(url, proxies=proxies)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            # 检查API版本
            if 'api_version' in response.json():
                if response.json()['api_version'] != API_VERSION:
                    logger.warning(f"API版本不匹配: 期望{API_VERSION}, 实际{response.json()['api_version']}")

            # 处理错误响应
            if response.status_code >= 400:
                error_data = response.json()
                error_msg = error_data.get('error', '未知错误')
                if response.status_code == 400:
                    raise ValidationError(error_msg, response.status_code)
                elif response.status_code == 401:
                    # 401错误时清除会话
                    cls.clear_session()
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


class DataValidator:
    """
    数据验证器类，提供各种数据验证方法
    
    主要验证：
    - 用户名
    - 密码
    - 手机号
    """

    @staticmethod
    def validate_username(username):
        """
        验证用户名是否符合要求
        
        Args:
            username (str): 待验证的用户名
            
        Returns:
            bool: 验证通过返回True
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        if not username:
            raise ValidationError("用户名不能为空")
        if len(username) < 3 or len(username) > 80:
            raise ValidationError("用户名长度必须在3-80个字符之间")
        return True

    @staticmethod
    def validate_password(password):
        """验证密码是否符合要求"""
        if not password:
            raise ValidationError("密码不能为空")
        if len(password) < 6 or len(password) > 120:
            raise ValidationError("密码长度必须在6-120个字符之间")
        return True

    @staticmethod
    def validate_phone(phone):
        """验证手机号是否符合要求"""
        if not phone:
            raise ValidationError("手机号不能为空")
        if not phone.isdigit():
            raise ValidationError("手机号必须是数字")
        # if len(phone) != 11:
        #     raise ValidationError("手机号必须是11位")
        return True


class AnnouncementDialog(wx.Dialog):
    """
    公告对话框类，用于显示系统公告
    
    显示内容：
    - 公告标题
    - 公告内容
    - 发布时间
    - 公告类型
    """

    def __init__(self, parent, announcements):
        super().__init__(parent, title=_(UI_TEXTS['dialogs']['announcement_title']),
                         size=(400, 300))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建富文本控件显示公告
        self.text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)

        # 格式化公告内容
        content = ""
        for ann in announcements:
            content += f"【{ann['type']}】{ann['title']}\n"
            content += f"{ann['content']}\n"
            content += f"发布时间：{ann['created_at']}\n"
            content += "-" * 40 + "\n"

        self.text.SetValue(content if content else _(MESSAGES['notice_text']))

        sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 5)

        # 添加关闭按钮
        btn = wx.Button(panel, wx.ID_OK, "关闭")
        sizer.Add(btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        panel.SetSizer(sizer)
        self.Centre()


# --------------------------------------------------------------------------
#  Class MyFileDropTarget
# ---------------------------------------------------------------------------

class MyFileDropTarget(wx.FileDropTarget):
    """
    文件拖放处理类，用于处理文件拖放到列表控件的操作
    
    功能：
    - 支持txt文件的拖放
    - 自动读取文件内容
    - 过滤重复号码
    - 添加到列表显示
    """

    def __init__(self, window):
        super().__init__()
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        """
        处理文件拖放事件
        
        Args:
            x, y: 鼠标放下文件时的坐标
            filenames: 拖放的文件列表
            
        Returns:
            bool: 处理成功返回True
        """
        prefix = self.window.m_choice1.GetStringSelection() if self.window.m_choice1.GetCount() > 0 else ""
        for filepath in filenames:
            if filepath.lower().endswith('.txt'):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # 读取文件内容，只保留数字行
                        batch_phones = [line.strip() for line in f if line.strip().isdigit()]
                        # 过滤重复号码
                        unique_phones = [p for p in batch_phones if not self.window.is_phone_exist(p)]
                        self.window.existing_phones.update(unique_phones)

                        # 添加到列表显示
                        for phone in unique_phones:
                            if phone.isdigit():
                                index = self.window.m_listCtrl1.GetItemCount()
                                self.window.m_listCtrl1.InsertItem(index, str(index + 1))
                                self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('前缀'), prefix)
                                self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('号码'), phone)
                                # self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('检测结果'),
                                #                                 choice(CHECK_STATUS))
                            else:
                                self.window.log_textctrl.AppendText(MESSAGES['phone_format_error'].format(phone=phone))

                        # 调整列宽
                        self.window.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('号码'),
                                                               wx.LIST_AUTOSIZE_USEHEADER)
                        self.window.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('前缀'),
                                                               wx.LIST_AUTOSIZE_USEHEADER)
                        self.window.log_textctrl.AppendText(MESSAGES['file_import_success'].format(filepath=filepath))
                except Exception as e:
                    self.window.log_textctrl.AppendText(MESSAGES['file_import_failed'].format(error=str(e)))
        return True


# --------------------------------------------------------------------------
#  Class QueryManager
# ---------------------------------------------------------------------------

class QueryManager:
    """
    查询管理器类，处理单条和批量查询操作
    
    功能：
    - 单条号码查询
    - 批量号码查询（使用线程池）
    - 查询状态管理
    """

    def __init__(self, window):
        self.window = window
        self.is_querying = False
        self.should_stop = False
        self.executor = ThreadPoolExecutor(max_workers=QUERY_CONFIG['max_workers'])

    def query_single(self, area: str, phone: str) -> Dict[str, Any]:
        """
        查询单个号码
        
        Args:
            area: 区号
            phone: 电话号码
            
        Returns:
            Dict: 查询结果
        """
        try:
            response = APIClient.make_request('POST', API_ENDPOINTS['query_single'],
                                              data={'area': area, 'phone': phone})
            return response.json().get('data', {})
        except Exception as e:
            logger.error(f"查询失败 {area}{phone}: {str(e)}")
            raise

    def start_batch_query(self, phones: List[Dict[str, str]], max_workers: int = None):
        """开始批量查询"""
        if self.is_querying:
            return

        if len(phones) > QUERY_CONFIG['batch_size']:
            self.window.log_textctrl.AppendText(
                MESSAGES['batch_size_exceeded'].format(limit=QUERY_CONFIG['batch_size']))
            return

        self.is_querying = True
        self.should_stop = False

        # 启动查询线程
        threading.Thread(
            target=self._batch_query_worker,
            args=(phones,),
            daemon=True
        ).start()

    def _batch_query_worker(self, phones: List[Dict[str, str]]):
        """批量查询工作线程"""
        try:
            # 创建电话号码到行索引的映射
            phone_to_row = {}
            for row in range(self.window.m_listCtrl1.GetItemCount()):
                phone = self.window.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('号码')).GetText()
                phone_to_row[phone] = row

            success_count = 0
            failed_count = 0

            # 使用线程池并发查询，但每个查询完成后立即更新UI
            with ThreadPoolExecutor(max_workers=QUERY_CONFIG['max_workers']) as executor:
                # 为每个电话号码创建一个查询任务
                future_to_phone = {
                    executor.submit(self.query_single, phone_data['area'], phone_data['phone']): phone_data
                    for phone_data in phones if not self.should_stop
                }

                # 处理完成的任务
                for future in as_completed(future_to_phone):
                    if self.should_stop:
                        break

                    phone_data = future_to_phone[future]
                    row_index = phone_to_row.get(phone_data['phone'])

                    if row_index is None:
                        continue  # 跳过找不到行的情况

                    try:
                        # 获取查询结果
                        result = future.result(timeout=30)

                        # 更新结果到UI
                        wx.CallAfter(self._update_existing_result, row_index, result)
                        success_count += 1

                    except Exception as e:
                        # 处理查询失败
                        logger.error(f"查询失败 {phone_data['area']}{phone_data['phone']}: {str(e)}")
                        wx.CallAfter(self.window.m_listCtrl1.SetItem, row_index,
                                     LIST_VIEW_COLUMNS.index('检测结果'), "查询失败")
                        wx.CallAfter(self.window.log_textctrl.AppendText,
                                     MESSAGES['query_failed'].format(error=str(e)))
                        failed_count += 1

                    # 更新状态显示
                    wx.CallAfter(self.window.update_query_status, success_count, failed_count)

        except Exception as e:
            logger.error(f"批量查询失败: {str(e)}")
            wx.CallAfter(self.window.log_textctrl.AppendText,
                         MESSAGES['query_failed'].format(error=str(e)))
        finally:
            self.is_querying = False
            wx.CallAfter(self.window.log_textctrl.AppendText,
                         MESSAGES['query_completed'].format(success=success_count, failed=failed_count))

    def _update_existing_result(self, row_index: int, result: Dict[str, Any]):
        """更新已有行的查询结果"""
        try:
            # 更新注册年份
            if 'year' in result:
                self.window.m_listCtrl1.SetItem(row_index, LIST_VIEW_COLUMNS.index('注册年份'),
                                                result.get('year', '未知'))

            # 更新检测结果
            if 'status' in result:
                self.window.m_listCtrl1.SetItem(row_index, LIST_VIEW_COLUMNS.index('检测结果'),
                                                result.get('status', '未知'))

            # 可以更新其他字段...

            # 调整列宽
            self.window.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('号码'),
                                                   wx.LIST_AUTOSIZE_USEHEADER)
            self.window.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('注册年份'),
                                                   wx.LIST_AUTOSIZE_USEHEADER)
            self.window.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('检测结果'),
                                                   wx.LIST_AUTOSIZE_USEHEADER)
        except Exception as e:
            logger.error(f"更新UI失败: {str(e)}")
            # 这里不抛出异常，避免影响其他查询

    def _add_new_result(self, result: Dict[str, Any]):
        """添加新行显示查询结果（备用方法，正常情况不应使用）"""
        index = self.window.m_listCtrl1.GetItemCount()
        self.window.m_listCtrl1.InsertItem(index, str(index + 1))
        self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('前缀'),
                                        result.get('area', ''))
        self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('号码'),
                                        result.get('phone', ''))
        self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('注册年份'),
                                        result.get('year', ''))
        self.window.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('检测结果'),
                                        result.get('status', '未知'))

        # 调整列宽
        self.window.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('号码'),
                                               wx.LIST_AUTOSIZE_USEHEADER)

    def stop_query(self):
        """停止查询"""
        self.should_stop = True
        self.is_querying = False

    def __del__(self):
        """清理资源"""
        self.executor.shutdown(wait=False)


# --------------------------------------------------------------------------
#  Class MyFrame1
# ---------------------------------------------------------------------------

class MyFrame1(wx.Frame):
    """
    主窗口类，实现系统的主要界面和功能
    
    主要功能：
    - 号码检测（单条/批量）
    - 数据导出
    - 用户信息显示
    - 余额查询
    - 公告查看
    """

    def __init__(self, parent):
        """初始化主窗口"""
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=_(UI_CONFIG['main_window']['title']), 
                          pos=wx.DefaultPosition,
                          size=wx.Size(*UI_CONFIG['main_window']['size']), 
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(*UI_CONFIG['main_window']['background_color']))

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏（两个字段）
        self.statusbar = self.CreateStatusBar(2)
        self.statusbar.SetStatusWidths([-2, -1])  # 2:1的比例
        self.update_status_bar()

        # 主布局
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # ===== 顶部用户信息面板 =====
        user_panel = wx.Panel(self, wx.ID_ANY)
        user_panel.SetBackgroundColour(wx.Colour(230, 230, 240))  # 浅蓝灰色背景
        user_sizer = wx.BoxSizer(wx.HORIZONTAL)

        app = wx.GetApp()
        username = app.user_info.get('username', '')
        
        # 用户信息显示
        self.user_label = wx.StaticText(user_panel, 
            label=UI_TEXTS['labels']['user_label'].format(username=username),
            style=wx.ALIGN_CENTER_VERTICAL)
        self.user_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.balance_label = wx.StaticText(user_panel, 
            label=UI_TEXTS['labels']['balance_label'].format(balance=0.00),
            style=wx.ALIGN_CENTER_VERTICAL)
        self.balance_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        # 添加到用户面板
        user_sizer.Add(self.user_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        user_sizer.Add(wx.StaticLine(user_panel, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 5)
        user_sizer.Add(self.balance_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        user_sizer.AddStretchSpacer(1)
        
        # 添加刷新余额按钮
        refresh_btn = wx.Button(user_panel, wx.ID_ANY, "刷新余额", size=wx.Size(90, -1))
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh_balance)
        user_sizer.Add(refresh_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        user_panel.SetSizer(user_sizer)
        main_sizer.Add(user_panel, 0, wx.EXPAND | wx.ALL, 5)

        # ===== 查询控制面板 =====
        query_panel = wx.Panel(self, wx.ID_ANY)
        query_box = wx.StaticBox(query_panel, wx.ID_ANY, "查询控制")
        query_box_sizer = wx.StaticBoxSizer(query_box, wx.VERTICAL)
        
        # 查询控制上部分 - 批量查询
        batch_query_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        prefix_label = wx.StaticText(query_panel, wx.ID_ANY, 
                                    _(UI_TEXTS['labels']['phone_prefix']),
                                    style=wx.ALIGN_CENTER_VERTICAL)
        
        m_choice1Choices = []
        self.m_choice1 = wx.Choice(query_panel, wx.ID_ANY, wx.DefaultPosition, wx.Size(100, -1), m_choice1Choices, 0)
        self.m_choice1.SetSelection(0)
        
        self.query_batch = wx.Button(query_panel, wx.ID_ANY,
                                   _(UI_TEXTS['buttons']['batch_query']), size=wx.Size(100, -1))
        
        self.stop = wx.Button(query_panel, wx.ID_ANY,
                            _(UI_TEXTS['buttons']['stop']), size=wx.Size(80, -1))
        
        # 状态显示
        self.status_label = wx.StaticText(query_panel, wx.ID_ANY, "", style=wx.ALIGN_CENTER_VERTICAL)
        
        batch_query_sizer.Add(prefix_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        batch_query_sizer.Add(self.m_choice1, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        batch_query_sizer.Add(self.query_batch, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        batch_query_sizer.Add(self.stop, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        batch_query_sizer.AddStretchSpacer(1)
        batch_query_sizer.Add(self.status_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        # 查询控制下部分 - 单条查询
        single_query_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        phone_label = wx.StaticText(query_panel, wx.ID_ANY,
                                  _(UI_TEXTS['labels']['phone_number']),
                                  style=wx.ALIGN_CENTER_VERTICAL)
        
        self.text_ctrl_phone = wx.TextCtrl(query_panel, wx.ID_ANY, wx.EmptyString, 
                                         wx.DefaultPosition, wx.Size(150, -1), 0)
        
        self.query_one = wx.Button(query_panel, wx.ID_ANY,
                                 _(UI_TEXTS['buttons']['single_query']), size=wx.Size(100, -1))
        
        # 导出按钮
        self.export_btn = wx.Button(query_panel, wx.ID_ANY,
                                  _(UI_TEXTS['buttons']['export']), size=wx.Size(100, -1))
        
        # 清空按钮
        clear_btn = wx.Button(query_panel, wx.ID_ANY, "清空列表", size=wx.Size(100, -1))
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_all)
        
        single_query_sizer.Add(phone_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        single_query_sizer.Add(self.text_ctrl_phone, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        single_query_sizer.Add(self.query_one, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        single_query_sizer.AddStretchSpacer(1)
        single_query_sizer.Add(self.export_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        single_query_sizer.Add(clear_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        # 添加到查询控制面板
        query_box_sizer.Add(batch_query_sizer, 0, wx.EXPAND | wx.ALL, 5)
        query_box_sizer.Add(wx.StaticLine(query_panel), 0, wx.EXPAND | wx.ALL, 2)
        query_box_sizer.Add(single_query_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        query_panel.SetSizer(query_box_sizer)
        main_sizer.Add(query_panel, 0, wx.EXPAND | wx.ALL, 5)

        # ===== 列表控件 =====
        list_panel = wx.Panel(self, wx.ID_ANY)
        list_box = wx.StaticBox(list_panel, wx.ID_ANY, "查询结果")
        list_box_sizer = wx.StaticBoxSizer(list_box, wx.VERTICAL)
        
        self.m_listCtrl1 = wx.ListCtrl(list_panel, wx.ID_ANY, wx.DefaultPosition, 
                                     wx.DefaultSize, wx.LC_REPORT)
        # 添加拖放支持
        dt = MyFileDropTarget(self)
        self.m_listCtrl1.SetDropTarget(dt)
        # 添加上下文菜单绑定
        self.m_listCtrl1.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        
        list_box_sizer.Add(self.m_listCtrl1, 1, wx.EXPAND | wx.ALL, 5)
        list_panel.SetSizer(list_box_sizer)
        main_sizer.Add(list_panel, 1, wx.EXPAND | wx.ALL, 5)

        # ===== 日志面板 =====
        log_panel = wx.Panel(self, wx.ID_ANY)
        log_box = wx.StaticBox(log_panel, wx.ID_ANY, "操作日志")
        log_box_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        self.log_textctrl = wx.TextCtrl(log_panel, wx.ID_ANY, wx.EmptyString, 
                                      wx.DefaultPosition, wx.DefaultSize,
                                      wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.log_textctrl.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        log_box_sizer.Add(self.log_textctrl, 1, wx.EXPAND | wx.ALL, 5)
        log_panel.SetSizer(log_box_sizer)
        main_sizer.Add(log_panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.SetItemMinSize(log_panel, (-1, 120))  # 设置日志面板最小高度

        self.SetSizer(main_sizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # 初始化数据
        self.col_list = LIST_VIEW_COLUMNS
        self.existing_phones = set()  # 号码缓存，用于去重
        self.__init_listctrl__()  # 初始化列表控件
        self.load_prefix_options()  # 加载号码前缀选项

        # 初始化查询管理器
        self.query_manager = QueryManager(self)

        # 绑定查询相关事件
        self.query_one.Bind(wx.EVT_BUTTON, self.on_query_one)
        self.query_batch.Bind(wx.EVT_BUTTON, self.on_query_batch)
        self.stop.Bind(wx.EVT_BUTTON, self.on_stop_query)
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)

    def __init_listctrl__(self):
        """初始化列表控件，设置列名和列宽"""
        for i in range(len(self.col_list)):
            self.m_listCtrl1.InsertColumn(i, self.col_list[i])
            self.m_listCtrl1.SetColumnWidth(i, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_listCtrl1.SetColumnWidth(0, 40)
        # 加载已有号码到缓存
        for row in range(self.m_listCtrl1.GetItemCount()):
            phone = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('号码')).GetText()
            self.existing_phones.add(phone)

    def is_phone_exist(self, phone):
        """检查号码是否已存在"""
        if phone in self.existing_phones:
            self.log_textctrl.AppendText(MESSAGES['phone_duplicate'].format(phone=phone))
            return True
        return False

    def load_prefix_options(self):
        """从配置文件加载号码前缀选项"""
        try:
            with open(FILE_CONFIG['phone_prefix_file'], 'r', encoding='utf-8') as f:
                options = [line.strip() for line in f if line.strip()]
                self.m_choice1.SetItems(options)
                if options:
                    self.m_choice1.SetSelection(0)
        except FileNotFoundError:
            self.log_textctrl.AppendText(MESSAGES['prefix_file_not_found'])
        except Exception as e:
            self.log_textctrl.AppendText(MESSAGES['prefix_load_failed'].format(error=str(e)))

    def on_query_one(self, event):
        """处理单条查询（异步版本）"""
        phone = self.text_ctrl_phone.GetValue().strip()
        prefix = self.m_choice1.GetStringSelection()

        try:
            DataValidator.validate_phone(phone)
            if self.is_phone_exist(phone):
                return

            # 先添加临时条目
            index = self.m_listCtrl1.GetItemCount()
            self.m_listCtrl1.InsertItem(index, str(index + 1))
            self.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('前缀'), prefix)
            self.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('号码'), phone)
            self.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('检测结果'), "查询中...")
            self.existing_phones.add(phone)

            # 启动查询线程
            threading.Thread(
                target=self._async_query_single,
                args=(prefix, phone, index),
                daemon=True
            ).start()

        except ValidationError as e:
            logger.warning(f"号码验证失败: {str(e)}")
            wx.MessageBox(str(e), _("验证错误"))

    def _async_query_single(self, prefix, phone, index):
        """异步查询线程"""
        try:
            result = self.query_manager.query_single(prefix, phone)

            # 主线程更新UI
            wx.CallAfter(self._update_query_result, index, {
                'year': result.get('year', '未知'),
                'status': result.get('status', '未知')
            })

        except Exception as e:
            logger.error(f"查询失败 {prefix}{phone}: {str(e)}")
            wx.CallAfter(self.m_listCtrl1.SetItem, index,
                         LIST_VIEW_COLUMNS.index('检测结果'),
                         f"查询失败: {str(e)}")
            wx.CallAfter(self.log_textctrl.AppendText,
                         MESSAGES['query_failed'].format(error=str(e)))

    def _update_query_result(self, index, result):
        """更新查询结果到指定行"""
        self.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('注册年份'), result['year'])
        self.m_listCtrl1.SetItem(index, LIST_VIEW_COLUMNS.index('检测结果'), result['status'])
        self.m_listCtrl1.SetColumnWidth(LIST_VIEW_COLUMNS.index('号码'), wx.LIST_AUTOSIZE_USEHEADER)

    def on_query_batch(self, event):
        """处理批量查询"""
        if self.query_manager.is_querying:
            return

        # 收集所有检测结果为空的号码
        phones = []
        status_col = LIST_VIEW_COLUMNS.index('检测结果')  # 新增列索引

        for row in range(self.m_listCtrl1.GetItemCount()):
            # 获取检测结果列的值
            status = self.m_listCtrl1.GetItem(row, status_col).GetText().strip()
            # 只收集未检测或需要重新检测的条目
            if not status or status == "查询失败":
                phone = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('号码')).GetText()
                prefix = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('前缀')).GetText()
                phones.append({'area': prefix, 'phone': phone})

                # 标记为"查询中..."
                self.m_listCtrl1.SetItem(row, status_col, "查询中...")

        if not phones:
            wx.MessageBox(_("没有可查询的号码"), _("提示"))
            return

        # 开始批量查询
        self.query_manager.start_batch_query(phones)
        self.log_textctrl.AppendText(MESSAGES['query_in_progress'])

    def on_stop_query(self, event):
        """停止查询"""
        if self.query_manager.is_querying:
            self.query_manager.stop_query()
            self.log_textctrl.AppendText(MESSAGES['query_stopped'])

    def update_query_status(self, success_count: int, failed_count: int):
        """更新查询状态显示"""
        status_text = UI_TEXTS['labels']['query_status'].format(
            status="查询中" if self.query_manager.is_querying else "空闲")
        if success_count > 0 or failed_count > 0:
            status_text += f" ({success_count}成功/{failed_count}失败)"
        self.status_label.SetLabel(status_text)

    def on_export(self, event):
        """
        处理数据导出功能
        
        流程：
        1. 获取所有检测结果类型
        2. 让用户选择要导出的类型
        3. 导出选中类型的数据到CSV文件
        """
        types = set()
        for row in range(self.m_listCtrl1.GetItemCount()):
            item_type = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('检测结果')).GetText()
            types.add(item_type)

        if not types:
            wx.MessageBox(MESSAGES['export_no_data'], "提示", wx.OK | wx.ICON_INFORMATION)
            return

        # 显示类型选择对话框
        dlg = wx.SingleChoiceDialog(self, "请选择要导出的检测结果类型",
                                    "导出数据", list(types))
        if dlg.ShowModal() == wx.ID_OK:
            selected_type = dlg.GetStringSelection()

            # 收集符合条件的数据
            data = []
            for row in range(self.m_listCtrl1.GetItemCount()):
                if self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('检测结果')).GetText() == selected_type:
                    row_data = [self.m_listCtrl1.GetItem(row, col).GetText()
                                for col in range(len(self.col_list))]
            data.append(row_data)

            # 保存到文件
            with wx.FileDialog(self, "保存文件", wildcard=FILE_CONFIG['export_file_type'],
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fd:
                if fd.ShowModal() == wx.ID_CANCEL:
                    return

                import csv
                try:
                    with open(fd.GetPath(), 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(self.col_list)
                        writer.writerows(data)
                    self.log_textctrl.AppendText(MESSAGES['export_success'].format(count=len(data)))
                except Exception as e:
                    self.log_textctrl.AppendText(MESSAGES['export_failed'].format(error=str(e)))

    def create_menu_bar(self):
        """创建菜单栏"""
        try:
            menubar = wx.MenuBar()

            # 根据配置创建菜单项
            for menu_key, menu_config in MENU_CONFIG.items():
                menu = wx.Menu()
                for item in menu_config['items']:
                    if item['id'] == 'exit':
                        menu_item = menu.Append(wx.ID_EXIT, _(item['label']))
                    elif item['id'] == 'about':
                        menu_item = menu.Append(wx.ID_ABOUT, _(item['label']))
                    else:
                        menu_item = menu.Append(wx.ID_ANY, _(item['label']))
                    # 保存菜单项引用
                    setattr(self, f"{item['id']}_item", menu_item)

                if menu_key == 'file_menu' and len(menu_config['items']) > 1:
                    menu.AppendSeparator()

                menubar.Append(menu, _(menu_config['title']))

            self.SetMenuBar(menubar)

            # 绑定菜单事件
            menu_bindings = {
                'export_item': self.on_export,
                'exit_item': self.on_exit,
                'change_pwd_item': self.on_change_password,
                'refresh_balance_item': self.on_refresh_balance,
                'about_item': self.on_about,
                'notice_item': self.on_notice,
                'refresh_notice_item': self.on_refresh_notice  # 添加刷新公告事件绑定
            }

            # 安全地绑定事件
            for item_name, handler in menu_bindings.items():
                if hasattr(self, item_name):
                    self.Bind(wx.EVT_MENU, handler, getattr(self, item_name))
                else:
                    logger.warning(f"菜单项 {item_name} 不存在")

        except Exception as e:
            logger.error(f"创建菜单栏失败: {str(e)}")
            wx.MessageBox(f"创建菜单栏失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def on_refresh_notice(self, event):
        """处理刷新公告事件"""
        try:
            response = APIClient.make_request('GET', API_ENDPOINTS['announcements'],
                                              params={'active_only': True})
            data = response.json()
            # 更新状态栏显示最新公告数量
            announcement_count = len(data.get('announcements', []))
            self.statusbar.SetStatusText(f"最新公告数量: {announcement_count}", 1)

            # 显示成功消息
            self.log_textctrl.AppendText("公告已刷新\n")

        except ResourceNotFoundError as e:
            logger.warning(f"获取公告失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))
        except APIError as e:
            logger.error(f"获取公告失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))

    def update_status_bar(self):
        app = wx.GetApp()
        username = app.user_info.get('username', '')
        role = ROLES['admin'] if app.user_info.get('is_admin') else ROLES['user']
        self.statusbar.SetStatusText(UI_TEXTS['labels']['status_bar'].format(
            username=username, role=role))

    def update_balance(self):
        try:
            response = APIClient.make_request('GET', API_ENDPOINTS['balance'])
            data = response.json()
            self.balance_label.SetLabel(UI_TEXTS['labels']['balance_label'].format(
                balance=data['balance']))
            logger.debug(f"余额更新成功: {data['balance']}")

        except AuthenticationError as e:
            logger.warning(f"获取余额失败: {str(e)}")
            wx.MessageBox(str(e), _("认证错误"))
        except APIError as e:
            logger.error(f"获取余额失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))

    def on_change_password(self, event):
        dlg = wx.PasswordEntryDialog(self,
                                     _(UI_TEXTS['dialogs']['old_pwd_prompt']),
                                     _(UI_TEXTS['dialogs']['change_pwd_title']))
        if dlg.ShowModal() == wx.ID_OK:
            old_password = dlg.GetValue()
            dlg.Destroy()

            dlg = wx.PasswordEntryDialog(self,
                                         _(UI_TEXTS['dialogs']['new_pwd_prompt']),
                                         _(UI_TEXTS['dialogs']['change_pwd_title']))
            if dlg.ShowModal() == wx.ID_OK:
                new_password = dlg.GetValue()
                try:
                    response = APIClient.make_request('POST', API_ENDPOINTS['change_password'],
                                                      data={'old_password': old_password, 'new_password': new_password})
                    data = response.json()
                    if response.status_code == 200:
                        wx.MessageBox(_(MESSAGES['password_change_success']), _("提示"))
                    else:
                        wx.MessageBox(data.get('error', _(MESSAGES['password_change_failed'])), _("错误"))
                except Exception as e:
                    wx.MessageBox(str(e), _("错误"))
            dlg.Destroy()

    def on_refresh_balance(self, event):
        self.update_balance()

    def on_about(self, event):
        wx.MessageBox(_(MESSAGES['about_text'].format(
            version=VERSION, api_version=API_VERSION)), _("关于"))

    def on_notice(self, event):
        try:
            response = APIClient.make_request('GET', API_ENDPOINTS['announcements'],
                                              params={'active_only': True})
            data = response.json()
            dlg = AnnouncementDialog(self, data.get('announcements', []))
            dlg.ShowModal()
            dlg.Destroy()

        except ResourceNotFoundError as e:
            logger.warning(f"获取公告失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))
        except APIError as e:
            logger.error(f"获取公告失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))

    def on_context_menu(self, event):
        """右键菜单处理"""
        menu = wx.Menu()
        self.context_menu_pos = event.GetPosition()  # 保存点击位置

        # 添加菜单项
        # retry_item = menu.Append(wx.ID_ANY, "重试选中项")
        clear_item = menu.Append(wx.ID_ANY, "清除选中行")
        menu.AppendSeparator()
        copy_phone_item = menu.Append(wx.ID_ANY, "复制号码")  # 新增
        copy_row_item = menu.Append(wx.ID_ANY, "复制整行")  # 新增
        menu.AppendSeparator()
        clear_all_item = menu.Append(wx.ID_ANY, "清空全部数据")

        # 绑定事件处理
        # self.Bind(wx.EVT_MENU, self.on_retry_selected, retry_item)
        self.Bind(wx.EVT_MENU, self.on_clear_selected, clear_item)
        self.Bind(wx.EVT_MENU, self.on_copy_phone, copy_phone_item)  # 新增
        self.Bind(wx.EVT_MENU, self.on_copy_row, copy_row_item)  # 新增
        self.Bind(wx.EVT_MENU, self.on_clear_all, clear_all_item)

        # 显示菜单
        self.m_listCtrl1.PopupMenu(menu)
        menu.Destroy()

    # def on_retry_selected(self, event):
    #     """重试选中项"""
    #     selected_phones = []
    #     prefix = self.m_choice1.GetStringSelection()
    #
    #     for row in range(self.m_listCtrl1.GetItemCount()):
    #         if self.m_listCtrl1.IsSelected(row):
    #             phone = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('号码')).GetText()
    #             selected_phones.append({'area': prefix, 'phone': phone})
    #
    #     if selected_phones:
    #         self.query_manager.start_batch_query(selected_phones)
    #         self.log_textctrl.AppendText(f"正在重试 {len(selected_phones)} 条记录...\n")

    def on_copy_phone(self, event):
        """复制选中号码"""
        # 使用保存的位置坐标
        pos = self.m_listCtrl1.ScreenToClient(self.context_menu_pos)
        row, _ = self.m_listCtrl1.HitTest(pos)
        if row != wx.NOT_FOUND:
            phone = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('号码')).GetText()
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(phone))
                wx.TheClipboard.Close()

    def on_copy_row(self, event):
        """复制整行数据"""
        pos = self.m_listCtrl1.ScreenToClient(self.context_menu_pos)
        row, _ = self.m_listCtrl1.HitTest(pos)
        if row != wx.NOT_FOUND:
            row_data = []
            for col in range(len(LIST_VIEW_COLUMNS)):
                row_data.append(self.m_listCtrl1.GetItem(row, col).GetText())
            text = '\t'.join(row_data)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(text))
                wx.TheClipboard.Close()

    def on_clear_selected(self, event):
        """清除选中行"""
        # 从后往前删除避免索引错乱
        for row in reversed(range(self.m_listCtrl1.GetItemCount())):
            if self.m_listCtrl1.IsSelected(row):
                phone = self.m_listCtrl1.GetItem(row, LIST_VIEW_COLUMNS.index('号码')).GetText()
                self.existing_phones.discard(phone)
                self.m_listCtrl1.DeleteItem(row)

    def on_clear_all(self, event):
        """清空全部数据"""
        dlg = wx.MessageDialog(self, "确定要清空所有数据吗？", "确认",
                              wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.m_listCtrl1.DeleteAllItems()
            self.existing_phones.clear()
            self.log_textctrl.AppendText("已清空所有检测数据\n")
        dlg.Destroy()

    def on_exit(self, event):
        # 退出时清除会话
        APIClient.clear_session()
        self.Close()


class LoginFrame(wx.Frame):
    """
    登录窗口类，处理用户登录和注册
    
    功能：
    - 用户登录
    - 用户注册
    - 输入验证
    """

    def __init__(self):
        """初始化登录窗口"""
        wx.Frame.__init__(self, None, id=wx.ID_ANY, title=_(UI_CONFIG['login_window']['title']),
                          pos=wx.DefaultPosition,
                          size=wx.Size(*UI_CONFIG['login_window']['size']),
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(*UI_CONFIG['login_window']['background_color']))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 创建面板
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # 用户名输入
        username_sizer = wx.BoxSizer(wx.HORIZONTAL)
        username_label = wx.StaticText(panel, label=_(UI_TEXTS['labels']['username']))
        self.username_input = wx.TextCtrl(panel)
        username_sizer.Add(username_label, 0, wx.ALL | wx.CENTER, 5)
        username_sizer.Add(self.username_input, 1, wx.ALL | wx.EXPAND, 5)

        # 密码输入
        password_sizer = wx.BoxSizer(wx.HORIZONTAL)
        password_label = wx.StaticText(panel, label=_(UI_TEXTS['labels']['password']))
        self.password_input = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        password_sizer.Add(password_label, 0, wx.ALL | wx.CENTER, 5)
        password_sizer.Add(self.password_input, 1, wx.ALL | wx.EXPAND, 5)

        # 按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.login_button = wx.Button(panel, label=_(UI_TEXTS['buttons']['login']))
        self.register_button = wx.Button(panel, label=_(UI_TEXTS['buttons']['register']))
        button_sizer.Add(self.login_button, 1, wx.ALL | wx.EXPAND, 5)
        button_sizer.Add(self.register_button, 1, wx.ALL | wx.EXPAND, 5)

        # 添加到主sizer
        sizer.Add(username_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(password_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(sizer)
        main_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        # 绑定事件
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login)
        self.register_button.Bind(wx.EVT_BUTTON, self.on_register)

        self.Centre()

    def on_login(self, event):
        """
        处理登录事件
        
        流程：
        1. 获取用户输入
        2. 验证输入格式
        3. 发送登录请求
        4. 处理响应结果
        """
        username = self.username_input.GetValue()
        password = self.password_input.GetValue()

        try:
            # 验证输入
            DataValidator.validate_username(username)
            DataValidator.validate_password(password)

            # 清除旧的会话
            APIClient.clear_session()

            # 发送登录请求
            response = APIClient.make_request('POST', API_ENDPOINTS['login'],
                                              {'username': username, 'password': password})
            data = response.json()

            logger.info(f"用户 {username} 登录成功")
            wx.MessageBox(_(MESSAGES['login_success']), _("提示"))

            # 保存用户信息并打开主窗口
            app = wx.GetApp()
            app.user_info = {
                'username': username,
                'role': data.get('role', 'user'),
                'is_admin': data.get('is_admin', False)
            }
            frame = MyFrame1(None)
            frame.Show()
            self.Close()

        except ValidationError as e:
            logger.warning(f"登录验证失败: {str(e)}")
            wx.MessageBox(str(e), _("验证错误"))
        except AuthenticationError as e:
            logger.warning(f"登录认证失败: {str(e)}")
            wx.MessageBox(str(e), _("认证错误"))
        except APIError as e:
            logger.error(f"登录失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))

    def on_register(self, event):
        username = self.username_input.GetValue()
        password = self.password_input.GetValue()

        try:
            # 验证输入
            DataValidator.validate_username(username)
            DataValidator.validate_password(password)

            # 发送注册请求
            response = APIClient.make_request('POST', API_ENDPOINTS['register'],
                                              {'username': username, 'password': password})

            logger.info(f"新用户注册成功: {username}")
            wx.MessageBox(_(MESSAGES['register_success']), _("提示"))

        except ValidationError as e:
            logger.warning(f"注册验证失败: {str(e)}")
            wx.MessageBox(str(e), _("验证错误"))
        except APIError as e:
            logger.error(f"注册失败: {str(e)}")
            wx.MessageBox(str(e), _("错误"))


class myApp(wx.App):
    """
    应用程序类，管理整个应用的生命周期
    
    功能：
    - 初始化应用
    - 管理用户信息
    - 清理资源
    """

    def OnInit(self):
        """应用程序初始化"""
        self.user_info = None  # 用于存储用户信息
        self.frame = LoginFrame()  # 显示登录界面
        self.frame.Show(True)
        return True

    def OnExit(self):
        """应用程序退出时的清理工作"""
        APIClient.clear_session()  # 清除会话
        return super().OnExit()


if __name__ == '__main__':
    app = myApp()
    app.MainLoop()
