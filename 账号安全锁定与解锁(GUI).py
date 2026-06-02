import time
import json
import requests
import re
import sys
import threading
import queue
from io import StringIO
from contextlib import redirect_stdout
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QRadioButton, QProgressBar, QFileDialog, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

from sixgods.Encrypt import Encrypt
from module.six_god1.devide_register import device_register
from module.six_god1.dyhk import VerifyAweme

# 全局常量
MAX_PROXY_RETRIES = 3  # 代理 IP 获取或请求失败的最大重试次数
MAX_DEVICE_RETRIES = 3  # 设备注册失败的最大重试次数
MAX_PROXY_USAGE = 5  # 每个代理 IP 最大使用次数


class ProxyPool:
    def __init__(self):
        self.proxies = {}  # 代理 IP 到使用次数的映射
        self.lock = threading.Lock()

    def get_proxy(self):
        """获取一个代理 IP，若池中无可用代理则从 API 获取"""
        with self.lock:
            # 优先返回未达到使用上限的代理
            for proxy, usage in list(self.proxies.items()):
                if usage < MAX_PROXY_USAGE:
                    self.proxies[proxy] = usage + 1
                    print(f"分配代理 IP: {proxy} (已使用 {self.proxies[proxy]} 次)")
                    return proxy
            # 池中无可用代理，获取新代理
            new_proxy = self._fetch_new_proxy()
            if new_proxy:
                self.proxies[new_proxy] = 1
                print(f"分配新代理 IP: {new_proxy} (已使用 1 次)")
            return new_proxy

    def add_proxy(self, proxy):
        """将代理 IP 放回池中，如果未达到使用上限"""
        if not proxy:
            return
        with self.lock:
            if proxy in self.proxies and self.proxies[proxy] < MAX_PROXY_USAGE:
                print(f"代理 IP {proxy} 放回池中 (已使用 {self.proxies[proxy]} 次)")
            else:
                # 达到使用上限或无效代理，移除
                if proxy in self.proxies:
                    print(f"代理 IP {proxy} 已使用 {self.proxies[proxy]} 次，释放")
                    del self.proxies[proxy]

    def _fetch_new_proxy(self):
        """从 API 获取新代理 IP"""
        proxy_url = "https://sch.shanchendaili.com/api.html?action=get_ip&key=HU27ca0c517041096372gnJQ&time=5&count=1&type=text&textSep=1&only=1"
        for attempt in range(MAX_PROXY_RETRIES):
            try:
                response = requests.get(proxy_url, timeout=10)
                if response.status_code == 200:
                    proxy_ip = response.text.strip()
                    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', proxy_ip):
                        print(f"成功获取代理 IP: {proxy_ip}")
                        return proxy_ip
                    else:
                        print(f"尝试 {attempt + 1}/{MAX_PROXY_RETRIES}: 获取的代理 IP 格式无效: {proxy_ip}")
                else:
                    print(f"尝试 {attempt + 1}/{MAX_PROXY_RETRIES}: 获取代理 IP 失败，状态码: {response.status_code}")
            except requests.RequestException as e:
                print(f"尝试 {attempt + 1}/{MAX_PROXY_RETRIES}: 获取代理 IP 时发生错误: {e}")
            time.sleep(1)
        print("达到最大重试次数，未能获取有效代理 IP")
        return None


proxy_pool = ProxyPool()


def make_request_with_proxy(method, url, headers, data=None, proxy_ip=None, retries=MAX_PROXY_RETRIES):
    """
    使用代理执行 HTTP 请求，若失败则重新获取代理 IP 并重试。
    method: 'post' 或 'get'
    proxy_ip: 当前线程使用的代理 IP
    返回响应对象或 None。
    """
    current_proxy = proxy_ip
    for attempt in range(retries):
        if not current_proxy:
            current_proxy = proxy_pool.get_proxy()
            if not current_proxy:
                print(f"尝试 {attempt + 1}/{retries}: 无法获取代理 IP")
                continue

        proxies = {"http": f"http://{current_proxy}", "https": f"http://{current_proxy}"}

        try:
            print(f"尝试 {attempt + 1}/{retries}: 使用代理 {current_proxy} 发起请求")
            if method.lower() == 'post':
                response = requests.post(url, data=data, headers=headers, proxies=proxies, timeout=10)
            else:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=10)

            if response.status_code == 200:
                print(f"请求成功，状态码: {response.status_code}")
                return response
            else:
                print(f"尝试 {attempt + 1}/{retries}: 请求失败，状态码: {response.status_code}")
                print(response.text)
                current_proxy = None  # 清除当前代理，触发重新获取
        except requests.RequestException as e:
            print(f"尝试 {attempt + 1}/{retries}: 请求失败: {e}")
            current_proxy = None  # 清除当前代理，触发重新获取

    print("达到最大重试次数，请求失败")
    return None


def query_account(area, mobile, device_id, install_id, device_token, proxy_ip, scene="lock"):
    headers = {
        "Host": "api5-normal-m-hj.amemv.com",
        "accept-encoding": "gzip",
        "x-tt-dt": device_token,
        "activity_now_client": str(round(time.time() * 1000)),
        "x-ss-req-ticket": str(round(time.time() * 1000)),
        "bd-ticket-guard-tee-status": "0",
        "sdk-version": "2",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "203331",
        "x-vc-bdturing-sdk-version": "3.7.5.cn",
        "user-agent": "com.ss.android.ugc.aweme/330801 (Linux; U; Android 13; zh_CN; 23127PN0CC; Build/TKQ1.220829.002;tt-ok/3.12.13.18)",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "content-length": "114"
    }
    url = "https://api.amemv.com/passport/safe/query_account/"
    params = {
        "passport-sdk-version": "203331",
        "request_from_account_sdk": "1",
        "iid": install_id,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "xiaomi_1128_64",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "330800",
        "version_name": "33.8.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "23127PN0CC",
        "device_brand": "Xiaomi",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "330801",
        "resolution": "1080*2255",
        "dpi": "420",
        "update_version_code": "33809900",
        "_rticket": str(round(time.time() * 1000)),
        "package": "com.ss.android.ugc.aweme",
        "mcc_mnc": "46001",
        "first_launch_timestamp": "1745941220",
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
        "ts": str(round(time.time())),
        "cdid": "2afa8569-3498-4cec-aa4d-b8a10x56bba3",
        "okhttp_version": "4.2.228.4-douyin",
        "use_store_region_cookie": "1"
    }
    data = {
        "is_vcd": "1",
        "enter_from": "recover",
        "account_sdk_source": "app",
        "hide_user_name_v3": "1",
        "mix_mode": "1",
        "area_code": area,
        "mobile": xor(f"+{area} {mobile}"),
        "query_type": "0",
        "multi_login": "1",
        "scene": scene
    }
    sign_headers, sign_urls = Encrypt().sign_android(url=url, params=params, data=data, header=headers, lanusk="",
                                                     cell=True, log=False)

    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
    if not response:
        return None

    print(response.text)
    if response.status_code == 200:
        try:
            response_data = response.json()
            if response_data.get('message') == 'success' or response_data.get('data', {}).get('error_code') in [4021,4022]:
                return response.text
            if 'data' in response_data and response_data['data'].get('error_code') == 1105:
                hk = VerifyAweme(params['device_id'], params['iid']).captcha(
                    response_data['data']['verify_center_decision_conf'])
                if hk['code'] == 200:
                    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
                    if not response:
                        return None
                    print(response.text)
                    return response.text
            if response_data.get('message') == 'error':
                error_desc = response_data.get('data', {}).get('description', '未知错误')
                print(f"查询账号失败: {error_desc}")
                return json.dumps({"message": "error", "data": {"description": error_desc}})
            return response.text
        except ValueError:
            print("响应不是有效的 JSON 格式")
            print(response.text)
            return response.text
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return response.text


def send_code(area, mobile, not_login_ticket, device_id, install_id, device_token, proxy_ip):
    headers = {
        "Host": "api5-normal-m-hj.amemv.com",
        "accept-encoding": "gzip",
        "x-tt-dt": device_token,
        "activity_now_client": str(round(time.time() * 1000)),
        "x-ss-req-ticket": str(round(time.time() * 1000)),
        "bd-ticket-guard-tee-status": "0",
        "sdk-version": "2",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "203331",
        "x-vc-bdturing-sdk-version": "3.7.5.cn",
        "user-agent": "com.ss.android.ugc.aweme/330801 (Linux; U; Android 13; zh_CN; 23127PN0CC; Build/TKQ1.220829.002;tt-ok/3.12.13.18)",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "content-length": "114"
    }
    url = "https://api.amemv.com/passport/mobile/send_code/"
    params = {
        "passport-sdk-version": "203331",
        "request_from_account_sdk": "1",
        "iid": install_id,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "xiaomi_1128_64",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "330800",
        "version_name": "33.8.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "23127PN0CC",
        "device_brand": "Xiaomi",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "330801",
        "resolution": "1080*2255",
        "dpi": "420",
        "update_version_code": "33809900",
        "_rticket": str(round(time.time() * 1000)),
        "package": "com.ss.android.ugc.aweme",
        "mcc_mnc": "46001",
        "first_launch_timestamp": "1745941220",
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
        "ts": str(round(time.time())),
        "cdid": "2afa8569-3498-4cec-aa4d-b8a10c56bba3",
        "okhttp_version": "4.2.228.4-douyin",
        "use_store_region_cookie": "1"
    }
    data = {
        "is_vcd": "1",
        "account_sdk_source": "app",
        "mix_mode": "1",
        "mobile": xor(f"+{area} {mobile}"),
        "multi_login": "1",
        "type": "3130",
        "not_login_ticket": not_login_ticket,
    }
    sign_headers, sign_urls = Encrypt().sign_android(url=url, params=params, data=data, header=headers, lanusk="",
                                                     cell=True)

    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
    if not response:
        return None

    print(response.text)
    if response.status_code == 200:
        try:
            response_data = response.json()
            if response_data.get('message') == 'error':
                error_desc = response_data.get('data', {}).get('description', '未知错误')
                print(f"发送验证码失败: {error_desc}")
                return json.dumps({"message": "error", "data": {"description": error_desc}})
            if response_data.get('message') == 'success' and response_data.get('data', {}).get('error_code') in [4021,4022]:
                print("验证码验证成功，账号已锁定")
                return json.dumps({"message": "success", "data": {"description": "Account already locked"}})
            if 'data' in response_data and response_data['data'].get('error_code') == 1105:
                hk = VerifyAweme(params['device_id'], params['iid']).captcha(
                    response_data['data']['verify_center_decision_conf'])
                if hk['code'] == 200:
                    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
                    if not response:
                        return None
                    print('过完滑块', response.text)
                    response_data = response.json()
                    if response_data.get('message') == 'error':
                        error_desc = response_data.get('data', {}).get('description', '未知错误')
                        print(f"滑块验证后发送验证码失败: {error_desc}")
                        return json.dumps({"message": "error", "data": {"description": error_desc}})
                    return response.text
            return response.text
        except ValueError:
            print("响应不是有效的 JSON 格式")
            print(response.text)
            return response.text
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(response.text)
        return response.text


def check_code(area, mobile, not_login_ticket, code, device_id, install_id, device_token, proxy_ip):
    headers = {
        "Host": "api5-normal-m-hj.amemv.com",
        "accept-encoding": "gzip",
        "x-tt-dt": device_token,
        "activity_now_client": str(round(time.time() * 1000)),
        "x-ss-req-ticket": str(round(time.time() * 1000)),
        "bd-ticket-guard-tee-status": "0",
        "sdk-version": "2",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "203331",
        "x-vc-bdturing-sdk-version": "3.7.5.cn",
        "user-agent": "com.ss.android.ugc.aweme/330801 (Linux; U; Android 13; zh_CN; 23127PN0CC; Build/TKQ1.220829.002;tt-ok/3.12.13.18)",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "content-length": "114"
    }
    url = "https://api.amemv.com/passport/safe/check_code/"
    params = {
        "passport-sdk-version": "203331",
        "request_from_account_sdk": "1",
        "iid": install_id,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "xiaomi_1128_64",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "330800",
        "version_name": "33.8.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "23127PN0CC",
        "device_brand": "Xiaomi",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "330801",
        "resolution": "1080*2255",
        "dpi": "420",
        "update_version_code": "33809900",
        "_rticket": str(round(time.time() * 1000)),
        "package": "com.ss.android.ugc.aweme",
        "mcc_mnc": "46001",
        "first_launch_timestamp": "1745941220",
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
        "ts": str(round(time.time())),
        "cdid": "2afa8569-3498-4cec-aa4d-b8a10c56bba3",
        "okhttp_version": "4.2.228.4-douyin",
        "use_store_region_cookie": "1"
    }
    data = {
        "is_vcd": "1",
        "code": xor(code),
        "account_sdk_source": "app",
        "mix_mode": "1",
        "mobile": xor(f"+{area} {mobile}"),
        "multi_login": "1",
        "not_login_ticket": not_login_ticket,
        "type": "3130"
    }
    sign_headers, sign_urls = Encrypt().sign_android(url=url, params=params, data=data, header=headers, lanusk="",
                                                     cell=True)

    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
    if not response:
        return None
    print(response.text)
    try:
        response_data = response.json()
        if response_data.get('message') == 'error':
            error_desc = response_data.get('data', {}).get('description', '未知错误')
            print(f"验证码验证失败: {error_desc}")
            return json.dumps({"message": "error", "data": {"description": error_desc}})
        return response.text
    except ValueError:
        print("响应不是有效的 JSON 格式")
        print(response.text)
        return response.text


def lock_account(not_login_ticket, verify_ticket, device_id, install_id, device_token, proxy_ip):
    headers = {
        "Host": "api5-normal-m-hj.amemv.com",
        "accept-encoding": "gzip",
        "x-tt-dt": device_token,
        "activity_now_client": str(round(time.time() * 1000)),
        "x-ss-req-ticket": str(round(time.time() * 1000)),
        "bd-ticket-guard-tee-status": "0",
        "sdk-version": "2",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "203331",
        "x-vc-bdturing-sdk-version": "3.7.5.cn",
        "user-agent": "com.ss.android.ugc.aweme/330801 (Linux; U; Android 13; zh_CN; 23127PN0CC; Build/TKQ1.220829.002;tt-ok/3.12.13.18)",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "content-length": "114"
    }
    url = "https://api.amemv.com/passport/safe/lock/"
    params = {
        "passport-sdk-version": "203331",
        "request_from_account_sdk": "1",
        "iid": install_id,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "xiaomi_1128_64",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "330800",
        "version_name": "33.8.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "23127PN0CC",
        "device_brand": "Xiaomi",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "330801",
        "resolution": "1080*2255",
        "dpi": "420",
        "update_version_code": "33809900",
        "_rticket": str(round(time.time() * 1000)),
        "package": "com.ss.android.ugc.aweme",
        "mcc_mnc": "46001",
        "first_launch_timestamp": "1745941220",
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
        "ts": str(round(time.time())),
        "cdid": "2afa8569-3498-4cec-aa4d-b8a10c56bba3",
        "okhttp_version": "4.2.228.4-douyin",
        "use_store_region_cookie": "1"
    }
    data = {
        "is_vcd": "1",
        "account_sdk_source": "app",
        "multi_login": "1",
        "not_login_ticket": not_login_ticket,
        "verify_ticket": verify_ticket,
    }
    sign_headers, sign_urls = Encrypt().sign_android(url=url, params=params, data=data, header=headers, lanusk="",
                                                     cell=True)

    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
    if not response:
        return None
    print(response.text)
    try:
        response_data = response.json()
        if response_data.get('message') == 'error':
            error_desc = response_data.get('data', {}).get('description', '未知错误')
            print(f"锁定账号失败: {error_desc}")
            return json.dumps({"message": "error", "data": {"description": error_desc}})
        return response.text
    except ValueError:
        print("响应不是有效的 JSON 格式")
        print(response.text)
        return response.text


def unlock_account(not_login_ticket, verify_ticket, device_id, install_id, device_token, proxy_ip):
    headers = {
        "Host": "api5-normal-m-hj.amemv.com",
        "accept-encoding": "gzip",
        "x-tt-dt": device_token,
        "activity_now_client": str(round(time.time() * 1000)),
        "x-ss-req-ticket": str(round(time.time() * 1000)),
        "bd-ticket-guard-tee-status": "0",
        "sdk-version": "2",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "203331",
        "x-vc-bdturing-sdk-version": "3.7.5.cn",
        "user-agent": "com.ss.android.ugc.aweme/330801 (Linux; U; Android 13; zh_CN; 23127PN0CC; Build/TKQ1.220829.002;tt-ok/3.12.13.18)",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "content-length": "114"
    }
    url = "https://api.amemv.com/passport/safe/unlock/"
    params = {
        "passport-sdk-version": "203331",
        "request_from_account_sdk": "1",
        "iid": install_id,
        "device_id": device_id,
        "ac": "wifi",
        "channel": "xiaomi_1128_64",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "330800",
        "version_name": "33.8.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "23127PN0CC",
        "device_brand": "Xiaomi",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "330801",
        "resolution": "1080*2255",
        "dpi": "420",
        "update_version_code": "33809900",
        "_rticket": str(round(time.time() * 1000)),
        "package": "com.ss.android.ugc.aweme",
        "mcc_mnc": "46001",
        "first_launch_timestamp": "1745941220",
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
        "ts": str(round(time.time())),
        "cdid": "2afa8569-3498-4cec-aa4d-b8a10c56bba3",
        "okhttp_version": "4.2.228.4-douyin",
        "use_store_region_cookie": "1"
    }
    data = {
        "is_vcd": "1",
        "account_sdk_source": "app",
        "multi_login": "1",
        "not_login_ticket": not_login_ticket,
        "verify_ticket": verify_ticket,
    }
    sign_headers, sign_urls = Encrypt().sign_android(url=url, params=params, data=data, header=headers, lanusk="",
                                                     cell=True)

    response = make_request_with_proxy('post', sign_urls, sign_headers, data=data, proxy_ip=proxy_ip)
    if not response:
        return None
    print(response.text)
    try:
        response_data = response.json()
        if response_data.get('message') == 'error':
            error_desc = response_data.get('data', {}).get('description', '未知错误')
            print(f"解锁账号失败: {error_desc}")
            return json.dumps({"message": "error", "data": {"description": error_desc}})
        return response.text
    except ValueError:
        print("响应不是有效的 JSON 格式")
        print(response.text)
        return response.text


def get_verification_code(sms_api_url, max_attempts=10, poll_interval=5, initial_delay=5):
    """
    轮询 SMS API 获取验证码。
    返回 4 位验证码，若未找到则返回 None。
    """
    print(f"等待 {initial_delay} 秒后开始轮询 SMS API...")
    time.sleep(initial_delay)
    for attempt in range(max_attempts):
        try:
            response = requests.get(sms_api_url, timeout=10)
            if response.status_code == 200:
                sms_text = response.text
                match = re.search(r'\b(\d{4})\b', sms_text)
                if match:
                    print(f"尝试 {attempt + 1}: 找到验证码: {match.group(1)}")
                    return match.group(1)
                print(f"尝试 {attempt + 1}: 未找到验证码: {sms_text}")
            else:
                print(f"尝试 {attempt + 1}: SMS API 请求失败，状态码: {response.status_code}")
        except requests.RequestException as e:
            print(f"尝试 {attempt + 1}: 轮询 SMS API 时发生错误: {e}")
        time.sleep(poll_interval)
    print("达到最大尝试次数，未能获取验证码")
    return None


def process_sms_verification(str_data, proxy_retries=3, device_retries=3, max_retries=1):
    """
    处理锁定账号的 SMS 验证，支持验证码失败重试。
    成功返回 'Verification successful'，否则返回 None。
    """
    try:
        mobile, area, sms_api_url = str_data.split('|')
    except ValueError:
        print("str_data 格式无效")
        return None

    # 为当前账号获取独立的代理 IP
    proxy_ip = None
    for attempt in range(proxy_retries):
        proxy_ip = proxy_pool.get_proxy()
        if proxy_ip:
            print(f"分配代理 IP: {proxy_ip}")
            break
        print(f"尝试 {attempt + 1}/{proxy_retries}: 无法获取代理 IP")
        time.sleep(1)
    if not proxy_ip:
        print("无法获取代理 IP，程序将退出")
        return None

    # 尝试注册设备
    device_info = None
    for attempt in range(device_retries):
        device_info = device_register()
        if device_info:
            device_id = device_info.get('device_id_str')
            install_id = device_info.get('install_id_str')
            device_token = device_info.get('device_token')
            if all([device_id, install_id, device_token]) and device_id != '0' and install_id != '0':
                print(f"注册设备成功: device_id={device_id}, install_id={install_id}, device_token={device_token}")
                break
            print(f"尝试 {attempt + 1}/{device_retries}: 设备注册信息无效: {device_info}")
        else:
            print(f"尝试 {attempt + 1}/{device_retries}: 设备注册失败")
        time.sleep(1)
    else:
        print("达到最大设备注册重试次数，未能获取有效设备信息")
        proxy_pool.add_proxy(proxy_ip)  # 放回代理
        return None

    device_id = device_info.get('device_id_str')
    install_id = device_info.get('install_id_str')
    device_token = device_info.get('device_token')

    for attempt in range(max_retries + 1):
        print(f"验证尝试 {attempt + 1}/{max_retries + 1}")
        json_str = query_account(area, mobile, device_id, install_id, device_token, proxy_ip, scene="lock")
        if not json_str:
            print("查询账号信息失败，可能是代理问题")
            proxy_pool.add_proxy(proxy_ip)  # 放回代理
            return None
        try:
            json_data = json.loads(json_str)
            if json_data.get("message") == "success":
                not_login_ticket = json_data.get("data", {}).get("account", [{}])[0].get("not_login_ticket")
                if not not_login_ticket:
                    print("未找到 not_login_ticket")
                    proxy_pool.add_proxy(proxy_ip)  # 放回代理
                    return "锁定失败 - 未找到 not_login_ticket"
                print(f"查询账号信息成功, not_login_ticket: {not_login_ticket}")

                is_send = json.loads(
                    send_code(area, mobile, not_login_ticket, device_id, install_id, device_token, proxy_ip))
                if is_send.get("message") == "error":
                    error_desc = is_send.get("data", {}).get("description", "未知错误")
                    print(f"发送验证码失败: {error_desc}")
                    proxy_pool.add_proxy(proxy_ip)  # 放回代理
                    return f"锁定失败 - {error_desc}"
                if is_send.get("message") == "success":
                    print("发送验证码成功")
                    code = get_verification_code(sms_api_url)
                    if code:
                        print(f"获取到验证码: {code}")
                        check_result = json.loads(
                            check_code(area, mobile, not_login_ticket, code, device_id, install_id, device_token,
                                       proxy_ip))
                        if check_result.get("message") == "error":
                            error_desc = check_result.get("data", {}).get("description", "未知错误")
                            print(f"验证码验证失败: {error_desc}")
                            proxy_pool.add_proxy(proxy_ip)  # 放回代理
                            return f"锁定失败 - {error_desc}"
                        if check_result.get("message") == "success":
                            print("验证码验证成功")
                            verify_ticket = check_result.get("data", {}).get("ticket")
                            if not verify_ticket:
                                print("未找到 verify_ticket")
                                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                                return "锁定失败 - 未找到 verify_ticket"
                            print(f"verify_ticket: {verify_ticket}")
                            lock_result = json.loads(
                                lock_account(not_login_ticket, verify_ticket, device_id, install_id, device_token,
                                             proxy_ip))
                            if lock_result.get("message") == "error":
                                error_desc = lock_result.get("data", {}).get("description", "未知错误")
                                print(f"账号锁定失败: {error_desc}")
                                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                                return f"锁定失败 - {error_desc}"
                            if lock_result.get("message") == "success":
                                print("账号锁定成功")
                                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                                return f"锁定成功"
                        else:
                            error_code = check_result.get("data", {}).get("error_code")
                            if error_code == 1202 and attempt < max_retries:
                                print("验证码错误，尝试重试...")
                                continue
                            proxy_pool.add_proxy(proxy_ip)  # 放回代理
                            return "锁定失败 - 验证码验证失败"
                else:
                    if is_send.get("data", {}).get('error_code') == 1105:
                        print(is_send.get("data", {}).get('description'))
                    proxy_pool.add_proxy(proxy_ip)  # 放回代理
                    return "锁定失败 - 发送验证码失败"
            elif json_data.get('message') == 'error' and json_data.get('data', {}).get('error_code') in [4021,4022]:
                success_desc = json_data.get("data", {}).get("description", "未知错误")
                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                print(f"锁定成功 - {success_desc}")
                return f"锁定成功 - {success_desc}"
            elif json_data.get("message") == "error":
                error_desc = json_data.get("data", {}).get("description", "未知错误")
                print(f"查询账号信息失败: {error_desc}")
                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                return f"锁定失败 - {error_desc}"
            else:
                print("查询账号信息失败")
                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                return "锁定失败 - 查询账号信息失败"
        except json.JSONDecodeError:
            print("无法解析 JSON 响应")
            proxy_pool.add_proxy(proxy_ip)  # 放回代理
            return "锁定失败 - 无法解析 JSON 响应"
    print("达到最大重试次数，验证失败")
    proxy_pool.add_proxy(proxy_ip)  # 放回代理
    return "锁定失败 - 达到最大重试次数"


def process_sms_unlock(str_data, proxy_retries=3, device_retries=3, max_retries=1):
    """
    处理解锁账号的 SMS 验证，支持验证码失败重试。
    成功返回 'Unlock successful'，否则返回 None。
    """
    try:
        mobile, area, sms_api_url = str_data.split('|')
    except ValueError:
        print("str_data 格式无效")
        return None

    # 为当前账号获取独立的代理 IP
    proxy_ip = None
    for attempt in range(proxy_retries):
        proxy_ip = proxy_pool.get_proxy()
        if proxy_ip:
            print(f"分配代理 IP: {proxy_ip}")
            break
        print(f"尝试 {attempt + 1}/{proxy_retries}: 无法获取代理 IP")
        time.sleep(1)
    if not proxy_ip:
        print("无法获取代理 IP，程序将退出")
        return None

    # 尝试注册设备
    device_info = None
    for attempt in range(device_retries):
        device_info = device_register()
        if device_info:
            device_id = device_info.get('device_id_str')
            install_id = device_info.get('install_id_str')
            device_token = device_info.get('device_token')
            if all([device_id, install_id, device_token]) and device_id != '0' and install_id != '0':
                print(f"注册设备成功: device_id={device_id}, install_id={install_id}, device_token={device_token}")
                break
            print(f"尝试 {attempt + 1}/{device_retries}: 设备注册信息无效: {device_info}")
        else:
            print(f"尝试 {attempt + 1}/{device_retries}: 设备注册失败")
        time.sleep(1)
    else:
        print("达到最大设备注册重试次数，未能获取有效设备信息")
        proxy_pool.add_proxy(proxy_ip)  # 放回代理
        return None

    device_id = device_info.get('device_id_str')
    install_id = device_info.get('install_id_str')
    device_token = device_info.get('device_token')

    for attempt in range(max_retries + 1):
        print(f"解锁尝试 {attempt + 1}/{max_retries + 1}")
        json_str = query_account(area, mobile, device_id, install_id, device_token, proxy_ip, scene="unlock")
        if not json_str:
            print("查询账号信息失败，可能是代理问题")
            proxy_pool.add_proxy(proxy_ip)  # 放回代理
            return "解锁失败 - 查询账号信息失败"
        try:
            json_data = json.loads(json_str)
            if json_data.get("message") == "success":
                not_login_ticket = json_data.get("data", {}).get("account", [{}])[0].get("not_login_ticket")
                if not not_login_ticket:
                    print("未找到 not_login_ticket")
                    proxy_pool.add_proxy(proxy_ip)  # 放回代理
                    return "解锁失败 - 未找到 not_login_ticket"
                print(f"查询账号信息成功, not_login_ticket: {not_login_ticket}")

                is_send = json.loads(
                    send_code(area, mobile, not_login_ticket, device_id, install_id, device_token, proxy_ip))
                if is_send.get("message") == "error":
                    error_desc = is_send.get("data", {}).get("description", "未知错误")
                    print(f"发送验证码失败: {error_desc}")
                    proxy_pool.add_proxy(proxy_ip)  # 放回代理
                    return f"解锁失败 - {error_desc}"
                if is_send.get("message") == "success":
                    print("发送验证码成功")
                    code = get_verification_code(sms_api_url)
                    if code:
                        print(f"获取到验证码: {code}")
                        check_result = json.loads(
                            check_code(area, mobile, not_login_ticket, code, device_id, install_id, device_token,
                                       proxy_ip))
                        if check_result.get("message") == "error":
                            error_desc = check_result.get("data", {}).get("description", "未知错误")
                            print(f"验证码验证失败: {error_desc}")
                            proxy_pool.add_proxy(proxy_ip)  # 放回代理
                            return f"解锁失败 - {error_desc}"
                        if check_result.get("message") == "success":
                            verify_ticket = check_result.get("data", {}).get("ticket")
                            if not verify_ticket:
                                print("未找到 verify_ticket")
                                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                                return "解锁失败 - 未找到 verify_ticket"
                            print(f"验证码验证成功, verify_ticket: {verify_ticket}")
                            unlock_result = json.loads(
                                unlock_account(not_login_ticket, verify_ticket, device_id, install_id, device_token,
                                               proxy_ip))
                            if unlock_result.get("message") == "error":
                                error_desc = unlock_result.get("data", {}).get("description", "未知错误")
                                print(f"账号解锁失败: {error_desc}")
                                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                                return f"解锁失败 - {error_desc}"
                            if unlock_result.get("message") == "success":
                                print("账号解锁成功")
                                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                                return "解锁成功"
                        else:
                            error_code = check_result.get("data", {}).get("error_code")
                            if error_code == 1202 and attempt < max_retries:
                                print("验证码错误，尝试重试...")
                                continue
                            proxy_pool.add_proxy(proxy_ip)  # 放回代理
                            return "解锁失败 - 验证码验证失败"
                else:
                    if is_send.get("data", {}).get('error_code') == 1105:
                        print(is_send.get("data", {}).get('description'))
                    proxy_pool.add_proxy(proxy_ip)  # 放回代理
                    return "解锁失败 - 发送验证码失败"
            elif json_data.get('message') == 'error' and json_data.get('data', {}).get('error_code') in [4021, 4022]:
                success_desc = json_data.get("data", {}).get("description", "未知错误")
                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                print(f"解锁成功 - {success_desc}")
                return f"解锁成功 - {success_desc}"
            elif json_data.get("message") == "error":
                error_desc = json_data.get("data", {}).get("description", "未知错误")
                print(f"查询账号信息失败: {error_desc}")
                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                return f"解锁失败 - {error_desc}"
            else:
                print("查询账号信息失败")
                proxy_pool.add_proxy(proxy_ip)  # 放回代理
                return "解锁失败 - 查询账号信息失败"
        except json.JSONDecodeError:
            print("无法解析 JSON 响应")
            proxy_pool.add_proxy(proxy_ip)  # 放回代理
            return "解锁失败 - 无法解析 JSON 响应"
    print("达到最大重试次数，解锁失败")
    proxy_pool.add_proxy(proxy_ip)  # 放回代理
    return "解锁失败 - 达到最大重试次数"


class AccountProcessor(QThread):
    progress_updated = pyqtSignal(int, str, str)
    completed = pyqtSignal()
    log_updated = pyqtSignal(str)

    def __init__(self, accounts, max_proxy_retries, max_device_retries, mode, concurrent_tasks=1):
        super().__init__()
        self.accounts = accounts
        self.max_proxy_retries = max_proxy_retries
        self.max_device_retries = max_device_retries
        self.mode = mode  # 'lock' or 'unlock'
        self.concurrent_tasks = concurrent_tasks
        self.running = True
        self.paused = False
        self.lock = threading.Lock()
        self.queue = queue.Queue()

        for i, account in enumerate(accounts):
            self.queue.put((i, account))

    def run(self):
        threads = []
        for _ in range(self.concurrent_tasks):
            t = threading.Thread(target=self.process_accounts)
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.completed.emit()

    def process_accounts(self):
        while not self.queue.empty() and self.running:
            with self.lock:
                if self.queue.empty():
                    return
                idx, account = self.queue.get()

            # 等待如果暂停
            while self.paused and self.running:
                time.sleep(0.5)

            if not self.running:
                return

            try:
                mobile, area, sms_api_url = account.split('|')
                status = "处理中..."
                self.progress_updated.emit(idx, status, "#FFA500")

                # 重定向 print 输出到 StringIO
                output = StringIO()
                with redirect_stdout(output):
                    if self.mode == "lock":
                        result = process_sms_verification(account, self.max_proxy_retries, self.max_device_retries)
                        if result.startswith("锁定成功"):
                            status = result
                        elif result.startswith("锁定失败"):
                            status = result
                        else:
                            status = "锁定失败 - 未知错误"
                    else:
                        result = process_sms_unlock(account, self.max_proxy_retries, self.max_device_retries)
                        if result.startswith("解锁成功"):
                            status = result
                        elif result.startswith("解锁失败"):
                            status = result
                        else:
                            status = "解锁失败 - 未知错误"

                # 发送日志
                self.log_updated.emit(output.getvalue())
                output.close()

                color = "#4CAF50" if "成功" in status else "#F44336"
                self.progress_updated.emit(idx, status, color)

            except Exception as e:
                status = f"错误: {str(e)}"
                self.progress_updated.emit(idx, status, "#F44336")
                self.log_updated.emit(str(e))

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.paused = False


class MainWindow(QMainWindow):
    def export_items(self, status_keyword):
        """导出符合指定状态的行到文本文件"""
        save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", "文本文件 (*.txt)")
        if not save_path:
            return
        with open(save_path, "w", encoding="utf-8") as f:
            for row in range(self.table.rowCount()):
                status_item = self.table.item(row, 3)
                if status_item and status_item.text().startswith(status_keyword):
                    items = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(3)]
                    f.write("|".join(items) + "\n")

    def delete_items(self, status_keyword):
        """删除符合指定状态的行，使用startswith匹配"""
        row = 0
        while row < self.table.rowCount():
            status_item = self.table.item(row, 3)
            if status_item and status_item.text().startswith(status_keyword):
                self.table.removeRow(row)
            else:
                row += 1

    def create_button_style(self, bg_color: str, hover_color: str) -> str:
        return f"""
        QPushButton {{
            background-color: {bg_color};
            color: white;
            font-size: 14px;
            padding: 6px 12px;
            border: none;
            border-radius: 8px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        """

    def update_button_visibility(self):
        """根据操作模式更新按钮的显示"""
        is_lock_mode = self.lock_radio.isChecked()
        self.export_success_btn.setVisible(is_lock_mode)
        self.export_fail_btn.setVisible(is_lock_mode)
        self.delete_success_btn.setVisible(is_lock_mode)
        self.delete_fail_btn.setVisible(is_lock_mode)
        self.export_unlock_success_btn.setVisible(not is_lock_mode)
        self.export_unlock_fail_btn.setVisible(not is_lock_mode)
        self.delete_unlock_success_btn.setVisible(not is_lock_mode)
        self.delete_unlock_fail_btn.setVisible(not is_lock_mode)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音账号锁定/解锁工具")
        self.setGeometry(100, 100, 1000, 700)

        # 初始化变量
        self.processor = None
        self.accounts = []

        # 创建主部件和布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 模式选择
        mode_group = QGroupBox("操作模式")
        mode_layout = QHBoxLayout()
        self.lock_radio = QRadioButton("锁定账号")
        self.unlock_radio = QRadioButton("解锁账号")
        self.lock_radio.setChecked(True)
        mode_layout.addWidget(self.lock_radio)
        mode_layout.addWidget(self.unlock_radio)
        mode_group.setLayout(mode_layout)

        # 连接单选按钮信号
        self.lock_radio.toggled.connect(self.update_button_visibility)
        self.unlock_radio.toggled.connect(self.update_button_visibility)

        # 导入账号部分
        import_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入账号")
        self.import_btn.setFixedHeight(40)
        self.import_btn.setStyleSheet(self.create_button_style("#01BEFF", "#3498DB"))
        self.import_btn.clicked.connect(self.import_accounts)
        import_layout.addWidget(self.import_btn)

        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet(self.create_button_style("#2DE88D", "#45B39D"))
        self.start_btn.clicked.connect(self.start_processing)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setFixedHeight(40)
        self.pause_btn.setStyleSheet(self.create_button_style("#FFCA28", "#DC7633"))
        self.pause_btn.clicked.connect(self.pause_processing)
        self.pause_btn.setEnabled(False)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setStyleSheet(self.create_button_style("#FF7043", "#CB4335"))
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)

        # 导出和删除按钮
        self.export_success_btn = QPushButton("导出锁定成功")
        self.export_success_btn.setStyleSheet(self.create_button_style("#01BEFF", "#28A1BA"))
        self.export_fail_btn = QPushButton("导出锁定失败")
        self.export_fail_btn.setStyleSheet(self.create_button_style("#01BEFF", "#28A1BA"))
        self.export_unlock_success_btn = QPushButton("导出解锁成功")
        self.export_unlock_success_btn.setStyleSheet(self.create_button_style("#01BEFF", "#28A1BA"))
        self.export_unlock_fail_btn = QPushButton("导出解锁失败")
        self.export_unlock_fail_btn.setStyleSheet(self.create_button_style("#01BEFF", "#28A1BA"))

        self.delete_success_btn = QPushButton("删除锁定成功项")
        self.delete_success_btn.setStyleSheet(self.create_button_style("#FF7043", "#CB4335"))
        self.delete_fail_btn = QPushButton("删除锁定失败项")
        self.delete_fail_btn.setStyleSheet(self.create_button_style("#FF7043", "#CB4335"))
        self.delete_unlock_success_btn = QPushButton("删除解锁成功项")
        self.delete_unlock_success_btn.setStyleSheet(self.create_button_style("#FF7043", "#CB4335"))
        self.delete_unlock_fail_btn = QPushButton("删除解锁失败项")
        self.delete_unlock_fail_btn.setStyleSheet(self.create_button_style("#FF7043", "#CB4335"))

        self.export_success_btn.clicked.connect(lambda: self.export_items("锁定成功"))
        self.export_fail_btn.clicked.connect(lambda: self.export_items("锁定失败"))
        self.export_unlock_success_btn.clicked.connect(lambda: self.export_items("解锁成功"))
        self.export_unlock_fail_btn.clicked.connect(lambda: self.export_items("解锁失败"))
        self.delete_success_btn.clicked.connect(lambda: self.delete_items("锁定成功"))
        self.delete_fail_btn.clicked.connect(lambda: self.delete_items("锁定失败"))
        self.delete_unlock_success_btn.clicked.connect(lambda: self.delete_items("解锁成功"))
        self.delete_unlock_fail_btn.clicked.connect(lambda: self.delete_items("解锁失败"))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.export_success_btn)
        btn_layout.addWidget(self.export_fail_btn)
        btn_layout.addWidget(self.export_unlock_success_btn)
        btn_layout.addWidget(self.export_unlock_fail_btn)
        btn_layout.addWidget(self.delete_success_btn)
        btn_layout.addWidget(self.delete_fail_btn)
        btn_layout.addWidget(self.delete_unlock_success_btn)
        btn_layout.addWidget(self.delete_unlock_fail_btn)

        # 初始化按钮显示状态
        self.update_button_visibility()

        # 设置部分
        settings_group = QGroupBox("参数设置")
        settings_layout = QGridLayout()

        # 代理设置
        settings_layout.addWidget(QLabel("代理 IP 链接:"), 0, 0)
        self.proxy_url_input = QLineEdit(
            "https://sch.shanchendaili.com/api.html?action=get_ip&key=HU27ca0c517041096372gnJQ&time=5&count=1&type=text&textSep=1&only=1")
        settings_layout.addWidget(self.proxy_url_input, 0, 1)

        # 重试次数设置
        settings_layout.addWidget(QLabel("代理请求最大重试次数:"), 1, 0)
        self.proxy_retries_input = QSpinBox()
        self.proxy_retries_input.setRange(1, 10)
        self.proxy_retries_input.setValue(3)
        settings_layout.addWidget(self.proxy_retries_input, 1, 1)

        settings_layout.addWidget(QLabel("设备注册最大重试次数:"), 2, 0)
        self.device_retries_input = QSpinBox()
        self.device_retries_input.setRange(1, 10)
        self.device_retries_input.setValue(3)
        settings_layout.addWidget(self.device_retries_input, 2, 1)

        # 并发设置
        settings_layout.addWidget(QLabel("并发处理数量:"), 3, 0)
        self.concurrent_input = QSpinBox()
        self.concurrent_input.setRange(1, 10)
        self.concurrent_input.setValue(3)
        settings_layout.addWidget(self.concurrent_input, 3, 1)

        settings_group.setLayout(settings_layout)

        # 账号表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["手机号", "区号", "短信API", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #f0f0f0; }")
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #4CAF50; }"
        )

        # 日志输出
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("border: 1px solid #ccc; border-radius: 3px; padding: 5px;")
        self.log_output.setMinimumHeight(150)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")

        # 添加到主布局
        main_layout.addWidget(mode_group)
        main_layout.addLayout(import_layout)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(QLabel("账号列表:"), alignment=Qt.AlignLeft)
        main_layout.addWidget(self.table)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("进度:"), alignment=Qt.AlignLeft)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(QLabel("日志输出:"), alignment=Qt.AlignLeft)
        main_layout.addWidget(self.log_output)
        main_layout.addWidget(self.status_label)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
            }
            QLineEdit, QSpinBox, QTextEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)

    def import_accounts(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入账号文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    accounts = [line.strip() for line in f.readlines() if line.strip()]

                self.accounts = accounts
                self.table.setRowCount(len(accounts))

                for i, account in enumerate(accounts):
                    parts = account.split('|')
                    if len(parts) >= 3:
                        self.table.setItem(i, 0, QTableWidgetItem(parts[0]))
                        self.table.setItem(i, 1, QTableWidgetItem(parts[1]))
                        self.table.setItem(i, 2, QTableWidgetItem(parts[2]))
                        self.table.setItem(i, 3, QTableWidgetItem("等待处理"))
                        self.table.item(i, 3).setForeground(QBrush(QColor("#2196F3")))

                self.status_label.setText(f"已导入 {len(accounts)} 个账号")
                self.progress_bar.setValue(0)
                self.log_output.clear()

            except Exception as e:
                QMessageBox.critical(self, "导入错误", f"导入账号文件时出错:\n{str(e)}")
                self.log_output.append(f"导入错误: {str(e)}")

    def start_processing(self):
        if not self.accounts:
            QMessageBox.warning(self, "警告", "请先导入账号！")
            self.log_output.append("警告: 请先导入账号！")
            return

        mode = "lock" if self.lock_radio.isChecked() else "unlock"

        self.processor = AccountProcessor(
            accounts=self.accounts,
            max_proxy_retries=self.proxy_retries_input.value(),
            max_device_retries=self.device_retries_input.value(),
            mode=mode,
            concurrent_tasks=self.concurrent_input.value()
        )

        self.processor.progress_updated.connect(self.update_account_status)
        self.processor.completed.connect(self.processing_completed)
        self.processor.log_updated.connect(self.update_log)

        # 更新按钮状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

        # 更新状态标签
        action = "锁定" if mode == "lock" else "解锁"
        self.status_label.setText(f"{action}处理进行中...")
        self.log_output.append(f"{action}处理开始...")

        # 重置进度条
        self.progress_bar.setValue(0)

        # 启动处理线程
        self.processor.start()

    def pause_processing(self):
        if self.processor:
            if self.processor.paused:
                self.processor.resume()
                self.pause_btn.setText("暂停")
                self.status_label.setText("处理继续中...")
                self.log_output.append("处理继续...")
            else:
                self.processor.pause()
                self.pause_btn.setText("继续")
                self.status_label.setText("处理已暂停...")
                self.log_output.append("处理暂停...")

    def stop_processing(self):
        if self.processor:
            self.processor.stop()
            self.processor.wait()
            self.status_label.setText("处理已停止")
            self.log_output.append("处理已停止")
            self.reset_buttons()

    def processing_completed(self):
        self.status_label.setText("处理完成！")
        self.log_output.append("处理完成！")
        self.reset_buttons()

    def reset_buttons(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self.stop_btn.setEnabled(False)

    def update_account_status(self, index, status, color):
        self.table.setItem(index, 3, QTableWidgetItem(status))
        self.table.item(index, 3).setForeground(QBrush(QColor(color)))

        # 更新进度条
        completed = sum(1 for i in range(self.table.rowCount())
                        if "成功" in self.table.item(i, 3).text() or "失败" in self.table.item(i, 3).text())
        total = self.table.rowCount()
        progress = int((completed / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)

    def update_log(self, log):
        self.log_output.append(log)
        self.log_output.ensureCursorVisible()

    def closeEvent(self, event):
        if self.processor and self.processor.isRunning():
            self.processor.stop()
            self.processor.wait()
        event.accept()


def xor(s):
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    result = ''
    for b in arr:
        result += chars[(b & 255) >> 4]
        result += chars[(b & 255) & 15]
    return result


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())