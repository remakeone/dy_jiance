import json
import uuid
import random
import time
import requests
import hashlib
import string
import binascii
import os
# from device_register.ttencrypt import ttencrypt
# from sixgods.Encrypt import Encrypt

from module.device_regist.ttEncrypt import ttencrypt
from module.six_god import Encrypt
from module.six_god2.core import sign_android


def encrypt_tt(tt):
    """加密device register info或者app log
    :param tt:
    :return:
    """
    encrypt = bytes.fromhex(ttencrypt().encrypt(json.dumps(tt).replace(" ", "")))
    return encrypt

def generate_modern_xiaomi_model():
    year = str(random.randint(20, 25))  # 年份：2020-2025
    month = str(random.randint(1, 12)).zfill(2)  # 月份：01-12
    sequence = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))  # 5位序列
    region = random.choice(["C", "G", "I"])  # 地区代码：C=国行, G=全球, I=印度
    return year + month + sequence + region


def device_register(channel="xiaomi_1128_64",proxies=None):
    cdid = str(uuid.uuid4())
    clientudid = str(uuid.uuid4())
    openudid = binascii.hexlify(os.urandom(8)).decode()
    device_model = generate_modern_xiaomi_model()
    china_operators = {"46000": "中国移动", "46002": "中国移动", "46007": "中国移动", "46001": "中国联通",
                       "46006": "中国联通", "46009": "中国联通", "46003": "中国电信", "46005": "中国电信",
                       "46011": "中国电信"}
    mcc_mnc = random.choice(list(china_operators.keys()))
    carrier = china_operators[mcc_mnc]
    url = "https://log.snssdk.com/service/2/device_register/"
    params = {
        'tt_data': 'a',
        'ac': 'wifi',
        'channel': channel,
        'aid': '1128',
        'app_name': 'aweme',
        'version_code': '340000',
        'version_name': '34.0.0',
        'device_platform': 'android',
        'os': 'android',
        'ssmix': 'a',
        'device_type': device_model,  # 这是一个变量
        'device_brand': 'Xiaomi',
        'language': 'zh',
        'os_api': '33',
        'os_version': '13',
        'manifest_version_code': '340001',
        'resolution': '1440*3007',
        'dpi': '560',
        'update_version_code': '34009900',
        '_rticket': '1742379901287',
        'package': 'com.ss.android.ugc.aweme',
        'mcc_mnc': mcc_mnc,
        'cpu_support64': 'true',
        'host_abi': 'armeabi-v7a',
        'is_guest_mode': '0',
        'app_type': 'normal',
        'minor_status': '0',
        'appTheme': 'light',
        'need_personal_recommend': '1',
        'is_android_pad': '0',
        'ts': '1742379900',
        'cdid': cdid  # 这是一个变量
    }
    register_info = {
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": "抖音",
            "update_version_code": 34009900,
            "manifest_version_code": 340001,
            "app_version_minor": "",
            "aid": 1128,
            "channel": channel,
            "appkey": "57bfa27c67e58e7d920028d3",
            "package": "com.ss.android.ugc.aweme",
            "app_version": "34.0.0",
            "version_code": 340000,
            "sdk_version": "3.7.3-alpha.16-doubleupload",
            "sdk_target_version": 29,
            "git_hash": "a94ff77",
            "os": "Android",
            "os_version": "13",
            "os_api": 33,
            "device_model": device_model,
            "device_brand": "Xiaomi",
            "device_manufacturer": "Xiaomi",
            "cpu_abi": "armeabi-v7a",
            "release_build": "",
            "density_dpi": 560,
            "display_density": "mdpi",
            "resolution": "3007x1440",
            "language": "zh",
            "timezone": 8,
            "access": "wifi",
            "not_request_sender": 0,
            "carrier": carrier,
            "mcc_mnc": "46001",
            "rom": "MIUI-V14.0.11.0.TKBCNXM",
            "rom_version": "miui_V140_V14.0.11.0.TKBCNXM",
            "cdid": cdid,
            "sig_hash": "aea615ab910015038f73c47e45d21466",
            "openudid": "86c34f420d9ff2aa",
            "clientudid": clientudid,
            "region": "CN",
            "tz_name": "Asia/Shanghai",
            "tz_offset": 28800,
            "sim_region": "cn",
            "sim_serial_number": [],
            "oaid": {
                "req_id": str(uuid.uuid4()),
                "hw_id_version_code": "0",
                "take_ms": "75",
                "is_track_limited": "false",
                "query_times": "1",
                "id": "4067ae1c4d619ec8",
                "time": str(round(time.time() * 1000))
            },
            "oaid_may_support": True,
            "req_id": str(uuid.uuid4()),
            "device_platform": "android",
            "custom": {
                "app_session_id_vcloud": "",
                "filter_warn": 0,
                "web_ua": f"Mozilla/5.0 (Linux; Android 13; {device_model} Build/TKQ1.220829.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36",
                "is_android_pad": 0,
                "client_ipv6": "",
                "is_new_user": True,
                "is_64_apk": False
            },
            "apk_first_install_time": int(round(time.time() * 1000)) - random.randint(13999, 15555),
            "is_system_app": 0,
            "sdk_flavor": "china",
            "guest_mode": 0
        },
        "_gen_time": round(time.time() * 1000)
    }
    register_body = encrypt_tt(register_info)
    headers = {
        "Host": "log.snssdk.com",
        "Connection": "keep-alive",
        "Content-Length": str(len(register_body)),
        "x-tt-request-tag": "t=0;n=1;s=0;p=0",
        "activity_now_client": str(time.time() * 1000),
        "X-SS-REQ-TICKET": str(time.time() * 1000),
        "x-vc-bdturing-sdk-version": "3.1.0.cn",
        "sdk-version": "2",
        "passport-sdk-version": "20380",
        "Content-Type": "application/octet-stream;tt-data=a",
        "X-SS-STUB": hashlib.md5(register_body).hexdigest().upper(),
        "X-SS-DP": str(register_info['header']['aid']),
        "User-Agent": f"com.ss.android.ugc.aweme/340000 (Linux; U; Android 13; zh_CN; {device_model}; Build/TKQ1.220829.002;tt-ok/3.12.13.4-tiktok)",
        "x-ss-req-ticket": str(int(time.time())) + "000",
        "x-tt-dm-status": "login=0;ct=0",
    }
    sign_headers, sign_urls = sign_android(url=url, params=params, data=register_body, header=headers, cell=True, log=False)
    try:
        resp = requests.post(sign_urls, data=register_body, headers=sign_headers,proxies=proxies)
        resp_json = resp.json()
        if resp_json.get('install_id', 0) == 0 or resp_json.get('device_id', 0) == 0:
            print('【注册失败!】', resp.json())
            return resp.json()
        else:
            s1 = f"https://api5-normal-m-hj.amemv.com/aweme/v1/aweme/detail/?aweme_id=7501871923145067812&origin_type=web&request_source=0&is_story=0&location_permission=0&aweme_type=1&recommend_collect_feedback=0&iid={resp_json['install_id']}&device_id={resp_json['device_id']}&ac=wifi&channel=tengxun_1128_1025&aid=1128&app_name=aweme&version_code=190000&version_name=19.0.0&device_platform=android&os=android&ssmix=a&device_type=2203121C&device_brand=Xiaomi&language=zh&os_api=33&os_version=13&manifest_version_code=190001&resolution=1440*3007&dpi=560&update_version_code=19009900&_rticket=1740576157432&package=com.ss.android.ugc.aweme&mcc_mnc=46001&cpu_support64=true&host_abi=armeabi-v7a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&need_personal_recommend=1&is_android_pad=0&ts=1740576156&cdid={cdid}&oaid=4067ae1c4d619ec8"
            print('s1', s1)
            headers = {
                "Host": "api5-normal-m-hj.amemv.com",
                "x-tt-dt": resp_json['device_token'],
                "activity_now_client": "1740576158403",
                "sdk-version": "2",
                "passport-sdk-version": "20356",
                "x-ss-req-ticket": "1740576157433",
                "x-vc-bdturing-sdk-version": "2.2.1.cn",
                "x-tt-request-tag": "s=1;p=0",
                "x-ss-dp": "1128",
                "x-tt-trace-id": resp.headers["x-tt-trace-id"],
                "user-agent": "com.ss.android.ugc.aweme/190001 (Linux; U; Android 13; zh_CN; 2203121C; Build/TKQ1.220829.002; Cronet/TTNetVersion:a7be068c 2021-12-02 QuicVersion:68cae75d 2021-08-12)",
            }

            response = requests.get(s1, headers=headers,proxies=proxies)
            print(response.text)
            return resp_json
    except Exception as e:
        print(print('【注册失败!】', e))

if __name__ == '__main__':
    print(device_register('huawei',proxies={
        # 'http': "http://127.0.0.1:7890",
        # 'https': "http://127.0.0.1:7890",
    }))