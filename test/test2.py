import random
import time
import urllib
import uuid

import requests

from TTEncrypt import TT
from flurl3.device_register import encrypt_tt, create_xiaomi_device

t = TT()
e = t.encrypt
d = t.decrypt
url = "https://klink.amemv.com/service/2/device_register/?tt_data=a&ac=wifi&channel=huoshan_fans_page_douyin&aid=1128&app_name=aweme&version_code=380900&version_name=38.9.0&device_platform=android&os=android&ssmix=a&device_type=AOSP+on+taimen&device_brand=Android&language=zh&os_api=30&os_version=11&manifest_version_code=380901&resolution=1440*2712&dpi=560&update_version_code=38909900&_rticket=1780247974121&package=com.ss.android.ugc.aweme&first_launch_timestamp=1780247969&last_deeplink_update_version_code=0&cpu_support64=true&host_abi=arm64-v8a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&is_preinstall=0&need_personal_recommend=1&is_android_pad=0&is_android_fold=0&ts=1780248009&cdid=a914fb24-ab1c-478f-a9d7-a66b530ff059&md=0&cronet_version=5e677c20_2026-03-23&ttnet_version=4.2.278.4-douyin&use_store_region_cookie=1"
simple_device = create_xiaomi_device()

payload = {
    "magic_tag": "ss_app_log",
    "header": {
        "display_name": "抖音",
        "update_version_code": 38909900,
        "manifest_version_code": 380901,
        "app_version_minor": "",
        "aid": 1128,
        "channel": "huoshan_fans_page_douyin",
        "package": "com.ss.android.ugc.aweme",
        "app_version": "38.9.0",
        "version_code": 380900,
        "sdk_version": "3.7.3-rc.106-douyin",
        "sdk_target_version": 29,
        "git_hash": "f86c2ef",
        "os": "Android",
        "os_version": "11",
        "os_api": 30,
        "device_model": simple_device['model'],
        "device_brand": simple_device['brand'],
        "device_manufacturer": simple_device['brand'],
        "cpu_abi": simple_device['cpu_abi'],
        "release_build": "5fb4fcd_20260525_850596d0-581d-11f1-8b3a-9a9044081a9f",
        "density_dpi": 560,
        "display_density": "mdpi",
        "resolution": "2712x1440",
        "language": "zh",
        "timezone": 8,
        "access": "wifi",
        "not_request_sender": 0,
        "rom": "eng.root.20230501.013644",
        "rom_version": "RP1A 200720.009 release-keys",
        "cdid": str(uuid.uuid4()),
        "sig_hash": "aea615ab910015038f73c47e45d21466",
        "openudid": "fa3ccdb4d33e701c",
        "clientudid": str(uuid.uuid4()),
        "ipv6_list": [
            {
                "type": "client_tun",
                "value": "FE80::8813:5FF:FE44:4E92"
            },
            {
                "type": "client_anpi",
                "value": "FE80::E809:7FF:FE56:4F97"
            }
        ],
        "region": "CN",
        "tz_name": "Asia/Shanghai",
        "tz_offset": 28800,
        "sim_serial_number": [],
        "oaid_may_support": False,
        "req_id": str(uuid.uuid4()),
        "device_platform": "android",
        "custom": {
            "is_android_fold": 0,
            "enterprise_user_type": -1,
            "filter_warn": 0,
            # "web_ua": "Mozilla/5.0 (Linux; Android 11; AOSP on taimen Build/RP1A.200720.009; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.120 Mobile Safari/537.36",
            "is_android_pad": 0,
            "loc_switch": False
        },
        "apk_first_install_time": int(round(time.time() * 1000)) - random.randint(13999, 15555),
        "is_system_app": 0,
        "sdk_flavor": "china",
        "guest_mode": 0
    },
    "_gen_time": round(time.time() * 1000)
}

# payload_new = encrypt_tt(payload)
payload_new = encrypt_tt(payload)

# with open(rf'C:\Users\remake\Desktop\小黄鸟会话保存\53','rb') as f:
#     payload_new = f.read()

headers = {
    'User-Agent': "com.ss.android.ugc.aweme/380901 (Linux; U; Android 11; zh_CN_#Hans; AOSP on taimen; Build/RP1A.200720.009; Cronet/TTNetVersion:e3d16265 2026-05-11 QuicVersion:afeca321 2026-04-27)",
    'Content-Type': "application/json",
    'Cookie': "passport_csrf_token=bed12ddb6984be2ac1abe2b6cd78fb1b; passport_csrf_token_default=bed12ddb6984be2ac1abe2b6cd78fb1b",
    # "x-bd-content-encoding": "zstd",
    "x-tt-encrypt-info": "1",

}
proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
    # 'http': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
    # 'https': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
}
response = requests.post(url, data=payload_new, headers=headers, proxies=proxies)

print(response.json())
