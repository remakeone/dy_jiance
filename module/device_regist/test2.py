import base64
import binascii
import json
import time
from flurl.utils import *
from flurl.request_params import generate_url_params, generate_url_common_params
from flurl.utils import UUID, md5, generate_android_id, generate_random_mac, gzip_compress, printf, cookie_string, \
    cookie_json, get_trace_id
from flurl.ttEncryptorUtil import ttEncrypt
import requests
from flurl.core import core_sixgod


def get_post_data(dev_info):
    itime = round(time.time() * 1000)
    gtime = round(time.time() * 1000)
    postDataObj = {
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": "抖音",
            "update_version_code": dev_info['app']['update_version_code'],
            "manifest_version_code": dev_info['app']['manifest_version_code'],
            # "app_version_minor": "",
            "aid": 1128,
            "channel": dev_info['app']['channel'],
            "package": "com.ss.android.ugc.aweme",
            "app_version": dev_info['app']['version_name'],
            "version_code": dev_info['app']['version_code'],
            "sdk_version": "3.7.3-rc.53-douyin-bugfix",
            "sdk_target_version": 29,
            # "git_hash": "600a6e8",
            "os": dev_info['device']['os'],
            "os_version": dev_info['device']['os_version'],
            "os_api": dev_info['device']['os_api'],
            "device_model": dev_info['device']['device_type'],
            "device_brand": dev_info['device']['device_brand'],
            "device_manufacturer": "Google",
            "device_category": "phone",
            "cpu_abi": "arm64-v8a",
            "release_build": f"{UUID()}",
            "density_dpi": dev_info['device']['dpi'],
            "display_density": "mdpi",
            "resolution": dev_info['device']['resolution'].replace('*', 'x'),
            "language": "zh",
            "mac": generate_random_mac(),
            "timezone": 8,
            "access": "wifi",
            "not_request_sender": 0,
            "carrier": "CHINA MOBILE",
            "mcc_mnc": "46007",
            "rom": dev_info['device']['rom'],
            "rom_version": dev_info['device']['rom_version'],
            "cdid": dev_info['device']['cdid'],
            "sig_hash": md5(UUID()),
            "openudid": dev_info['device']['openudid'],
            # "udid": dev_info['device']['udid'],
            "clientudid": dev_info['device']['clientudid'],
            "sim_serial_number": [],
            # "ipv6_list": [],
            "region": "CN",
            "tz_name": "Asia/Shanghai",
            "tz_offset": 28800,
            "sim_region": "cn",
            "oaid_may_support": False,
            "req_id": UUID(),
            "device_platform": dev_info['device']['device_platform'],
            "custom": {
                "client_ipv4": "127.0.0.1"
            },
            "apk_first_install_time": itime,
            "is_system_app": 0,
            "sdk_flavor": "china",
            "guest_mode": 0
        },
        "_gen_time": gtime
    }

    return gzip_compress(json.dumps(postDataObj).encode(encoding='utf-8'))


def get_headers(dev_info, md5Hash=""):
    extra = {
        "content-type": "application/octet-stream;tt-data=a",
        'X-SS-STUB': md5Hash,
    }
    headers = {
        "accept-encoding": "gzip",
        "log-encode-type": "gzip",
        "x-tt-request-tag": "t=0;n=1",
        "x-ss-req-ticket": str(round(time.time() * 1000)),
        "sdk-version": "2",
        "passport-sdk-version": "203316",
        "x-vc-bdturing-sdk-version": "3.7.4.cn",
        "user-agent": dev_info['extra']['userAgent'],
        "host": "log.snssdk.com",
        "connection": "Keep-Alive",
    }
    if md5Hash:
        return headers | extra
    return headers


class DeviceRegister:
    def __init__(self, proxy=None):
        """
        初始化设备注册类
        :param proxy: 代理IP地址，格式如 '49.70.137.45:30554'
        """
        self.proxy = self.format_proxy(proxy)
        self.dev_info = self._init_device_info()

    def _init_device_info(self):
        """初始化设备信息"""
        openudid = generate_android_id()
        uuid = UUID()
        cdid = UUID()
        clientudid = UUID()
        rom = f'EMUI-{rand_str(13)}'
        manifest_version_code = '320901'
        os_version = '10'
        device_type = 'MI 12'
        ttNet = "TTNetVersion:9ac8d95c 2024-11-25 QuicVersion:3f326df4 2024-11-14"

        return {
            'device': {
                'os': 'Android',
                'device_platform': 'android',
                'device_type': device_type,
                'device_brand': 'Xiaomi',
                'os_api': '29',
                'os_version': os_version,
                'openudid': openudid,
                'resolution': '1440*2392',
                'dpi': '560',
                'cdid': cdid,
                'uuid': uuid,
                'clientudid': clientudid,
                'rom': rom,
                'rom_version': rand_str(2),
            },
            'app': {
                'channel': 'douyin-ls-sm-xz-and-18',
                'version_code': '320900',
                'version_name': '32.9.0',
                'manifest_version_code': manifest_version_code,
                'update_version_code': '32909900',
                'okhttp_version': '4.2.210.13-douyin',
            },
            'extra': {
                'userAgent': f'com.ss.android.ugc.aweme/{manifest_version_code} (Linux; U; Android {os_version}; zh_CN; {device_type}; '
                             f'Build/MMB29M; Cronet/{ttNet})',
                'cookies': '',
            }
        }

    @staticmethod
    def format_proxy(proxy):
        """格式化代理地址"""
        if not proxy:
            return None

        if not isinstance(proxy, str):
            return None

        proxy = proxy.strip()
        if not proxy.startswith(('http://', 'https://')):
            proxy = f'http://{proxy}'

        return {"http": proxy, "https": proxy}

    def register(self):
        """执行设备注册流程"""
        extra = {}
        self.post_device_register(extra)
        self.send_app_alert_check()
        # 只返回需要的信息
        return {
            'aid': '1128',
            'iid': self.dev_info['device']['iid'],
            'install_id': self.dev_info['device']['iid'],
            'device_id': self.dev_info['device']['deviceId'],
            'channel': self.dev_info['app']['channel']
        }

    def post_device_register(self, extra):
        """发送设备注册请求"""
        url = "https://log.snssdk.com/service/2/device_register/"
        params = generate_url_params(self.dev_info, extra)
        req_url = f"{url}?{urllib.parse.urlencode(params)}"

        gzip_post_data = get_post_data(self.dev_info)
        post_data = ttEncrypt(gzip_post_data)

        headers = {
            "content-type": "application/octet-stream;tt-data=a",
            "accept-encoding": "gzip",
            "user-agent": self.dev_info['extra']['userAgent'],
            "host": "log.snssdk.com",
            "connection": "Keep-Alive",
        }

        response = requests.post(
            url=req_url,
            headers=headers,
            data=post_data,
            proxies=self.proxy
        )

        obj = json.loads(response.text)
        self.dev_info['device']['deviceId'] = str(obj["device_id"])
        self.dev_info['device']['iid'] = str(obj["install_id"])

        if response.cookies:
            cookies_dict = cookie_json(response)
            self.dev_info['extra']['cookies'] = json.loads(json.dumps(cookies_dict, indent=4))

        time.sleep(2)
        return response

    def send_app_alert_check(self):
        """发送应用告警检查请求"""
        url = "https://ichannel.snssdk.com/service/2/app_alert_check/"

        extra = {
            'device_id': self.dev_info['device']['deviceId'],
            'iid': self.dev_info['device']['iid'],
        }

        params = generate_url_params(self.dev_info, extra)
        headers = get_headers(self.dev_info)
        dev = {}

        sign_headers, sign_urls = core_sixgod(surl=url, params=params, devices=dev, header=headers, log=False)

        response = requests.get(
            sign_urls,
            headers=sign_headers,
            proxies=self.proxy
        )

        if response.cookies:
            cookies_dict = cookie_json(response)
            self.dev_info['extra']['cookies'] = json.loads(json.dumps(cookies_dict, indent=4))

        time.sleep(2)


# 使用示例
if __name__ == "__main__":
    all_count = 0  # 程序运行计数器
    print("\033[92m")  # 设置绿色文字
    print("┌────────────────────────────────────────────────────┐")
    print("│                                                    │")
    print("│             欢迎使用企鹅检测设备上传工具           │")
    print("│                                                    │")
    print("│----------------------------------------------------│")
    print("│                                                    │")
    print("│                   使用方式说明                     │")
    print("│                                                    │")
    print("│            【方式一】使用代理IP模式                │")
    print("│            【方式二】使用隧道模式                  │")
    print("│                                                    │")
    print("│----------------------------------------------------│")
    print("│                                                    │")
    print("│               ！！！特别提醒！！！                 │")
    print("│        使用任意模式都需要提前加白本机IP            │")
    print("│                                                    │")
    print("│                开发者：企鹅检测团队                │")
    print("│                版本号：v1.0.0                      │")
    print("│                                                    │")
    print("└────────────────────────────────────────────────────┘")
    print("\r\n")
    print("\033[0m")
    # type = input("请选择模式：1.代理IP模式 2.隧道模式\r\n请输入选项：")
    # if type == "1":
    #     ip_url = input("请输入代理ip的url：")
    #     if ip_url == "":
    #         print("输入错误，请重新运行输入代理IP！")
    #         exit()
    #     count = 0  # 计数器
    #     while True:
    #         try:
    #             all_count += 1
    #             print(f"当前运行任务序号：{all_count}\n")
    #             if count % 3 == 0:  # 每三次请求新的代理IP
    #                 proxy = for_proxy(ip_url)
    #
    #             device = DeviceRegister(proxy=proxy)
    #             result = device.register()
    #             row = requests.post(url="http://156.225.26.131/index/update", json=result)
    #             print(f"设备注册信息结果: {result}\n数据上传结果: {row.text}\n")
    #         except Exception as e:
    #             print(f"发生错误: {e}")  # 输出错误信息
    #         # 可以选择在这里添加其他处理逻辑，例如记录日志等
    # elif type == "2":
    #     ip_url = input("请输入隧道IP：")
    #     port = input("请输入隧道端口：")
    #     if ip_url == "" or port == "":
    #         print("输入错误，请重新运行输入隧道IP和隧道端口！")
    #         exit()

    while True:
        try:
            all_count += 1
            print(f"当前运行任务序号：{all_count}\n")
            proxy = "l506.kdltps.com:15818"
            device = DeviceRegister(proxy=proxy)
            result = device.register()
            print(f"设备注册信息结果: {result}\n")
            # row = requests.post(url="http://156.225.26.131/index/update", json=result)
            # print(f"设备注册信息结果: {result}\n数据上传结果: {row.text}\n")
        except Exception as e:
            print(f"发生错误: {e}\n")  # 输出错误信息
    # else:
    #     print("输入错误，请重新输入")
    #     exit()