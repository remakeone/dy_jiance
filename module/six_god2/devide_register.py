import json
import uuid
import random
import time
import requests
import hashlib
import string
import binascii
import os
from flurl.ttEncrypt import ttencrypt
from loguru import logger
def encrypt_tt(tt):
    encrypt = bytes.fromhex(ttencrypt().encrypt(json.dumps(tt).replace(" ", "")))
    return encrypt
def generate_modern_xiaomi_model():
    year = str(random.randint(20, 25))  # 年份：2020-2025
    month = str(random.randint(1, 12)).zfill(2)  # 月份：01-12
    sequence = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))  # 5位序列
    region = random.choice(["C", "G", "I"])  # 地区代码：C=国行, G=全球, I=印度
    return year + month + sequence + region

def device_register(proxies):
    cdid = str(uuid.uuid4())
    clientudid = str(uuid.uuid4())
    openudid = binascii.hexlify(os.urandom(8)).decode()
    device_model = generate_modern_xiaomi_model()
    channel = "xiaomi_664226_64"
    # print('device_model',device_model)
    device_register_url = f'https://log.snssdk.com/service/2/device_register/?tt_data=a&ac=wifi&channel={channel}&aid=664226&app_name=douyinos&version_code=330800&version_name=33.8.0&device_platform=android&os=android&ssmix=a&device_type={device_model}&device_brand=Xiaomi&language=zh&os_api=33&os_version=13&openudid={openudid}&manifest_version_code=330800&resolution=1080*2255&dpi=420&update_version_code=33809905&_rticket=1744457586983&package=com.ss.android.ugc.aweme.mobile&mcc_mnc=46001&first_launch_timestamp=1744457530&last_deeplink_update_version_code=0&cpu_support64=true&host_abi=arm64-v8a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&is_preinstall=0&need_personal_recommend=1&is_android_pad=0&is_android_fold=0&ts=1744457586&cdid={cdid}&md=0&okhttp_version=4.2.210.5-douyin&use_store_region_cookie=1'
    register_info = {
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": "抖音",
            "update_version_code": 33809905,
            "manifest_version_code": 330800,
            "app_version_minor": "",
            "aid": 664226,
            "channel": channel,
            "package": "com.ss.android.ugc.aweme.mobile",
            "app_version": "33.8.0",
            "version_code": 330800,
            "sdk_version": "3.7.3-rc.53-douyin-gang-ao",
            "sdk_target_version": 29,
            "git_hash": "1747e38",
            "os": "Android",
            "os_version": "13",
            "os_api": 33,
            "device_model": device_model,
            "device_brand": "Xiaomi",
            "device_manufacturer": "Xiaomi",
            "device_category": "phone",
            "cpu_abi": "arm64-v8a",
            "release_build": "a031e57_20250117",
            "density_dpi": 420,
            "display_density": "mdpi",
            "resolution": "2255x1080",
            "language": "zh",
            "timezone": 8,
            "access": "wifi",
            "not_request_sender": 0,
            "rom": "MIUI-V14.0.10.0.TKBCNXM",
            "rom_version": "miui_V140_V14.0.10.0.TKBCNXM",
            "cdid": cdid,
            "sig_hash": "e89b158e4bcf988ebd09eb83f5378e87",
            "openudid": openudid,
            "clientudid": clientudid,
            "ipv6_list": [],
            "region": "CN",
            "tz_name": "Asia/Shanghai",
            "tz_offset": 28800,
            "sim_serial_number": [],
            "req_id": str(uuid.uuid4()),
            "device_platform": "android",
            "custom": {
                "is_android_fold": 0,
                "filter_warn": 0,
                "web_ua": f"Mozilla/5.0 (Linux; Android 13; {device_model} Build/TKQ1.220829.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36",
                "is_android_pad": 0,
                "loc_switch": False
            },
            "pre_installed_channel": "",
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
        "User-Agent": f"com.ss.android.ugc.aweme.mobile/330800 (Linux; U; Android 13; zh_CN; {device_model}; Build/TKQ1.220829.002;tt-ok/3.12.13.4-tiktok)",
        "x-ss-req-ticket": str(int(time.time())) + "000",
        "x-tt-dm-status": "login=0;ct=0",
    }
    #headers = encrypt_six_gods(device_register_url,headers)
    try:
        resp = requests.post(device_register_url, data=register_body, headers=headers,proxies=proxies,timeout=10)
        resp_json = resp.json()
        if resp_json.get('install_id', 0) == 0 or resp_json.get('device_id', 0) == 0:
            # print('【注册失败!】', resp.json())
            return None
        else:
            return resp_json
    except Exception as e:
        logger.error(f'【注册失败!】:{e}')


if __name__ == '__main__':
    print(device_register({}))