import json
import uuid
import random
import time
import requests
import hashlib
import string
import binascii
import os
from module.six_god2.ttEncrypt import ttencrypt
# from sixgods.Encrypt import Encrypt
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

def device_register(proxies=None):
    if proxies is None:
        proxies = {}
    cdid = str(uuid.uuid4())
    clientudid = str(uuid.uuid4())
    openudid = binascii.hexlify(os.urandom(8)).decode()
    device_model = generate_modern_xiaomi_model()
    channel = "xiaomi_1128_64"
    china_operators = {"46000": "中国移动", "46002": "中国移动", "46007": "中国移动", "46001": "中国联通",
                       "46006": "中国联通", "46009": "中国联通", "46003": "中国电信", "46005": "中国电信",
                       "46011": "中国电信"}
    mcc_mnc = random.choice(list(china_operators.keys()))
    carrier = china_operators[mcc_mnc]
    url = "https://log.amemv.com/service/2/device_register/"
    params = {
        "tt_data": "a",
        "ac": "wifi",
        'channel': channel,
        "aid": "1349",
        "app_name": "maya",
        "version_code": "370300",
        "version_name": "37.3.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        'device_type': device_model,  # 这是一个变量
        "device_brand": "OPPO",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "370301",
        "resolution": "1080*2132",
        "dpi": "450",
        "update_version_code": "37309900",
        "_rticket": "1767902262950",
        "package": "my.maya.android",
        "first_launch_timestamp": "1767902260",
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
        "ts": "1767902261",
        "cdid": cdid,
        "md": "0",
        "cronet_version": "6f1e308d_2025-12-08",
        "ttnet_version": "4.2.243.28-douyin",
        "use_store_region_cookie": "1"
    }
    register_info = {
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": "多闪",
            "update_version_code": 37309900,
            "manifest_version_code": 370301,
            "app_version_minor": "",
            "aid": 1349,
            "channel": channel,
            "package": "my.maya.android",
            "app_version": "37.3.0",
            "version_code": 370300,
            "sdk_version": "3.7.3-rc.101-douyin-bugfix.1",
            "sdk_target_version": 29,
            "git_hash": "5b97dbd",
            "os": "Android",
            "os_version": "13",
            "os_api": 33,
            "device_model": device_model,
            "device_brand": "Xiaomi",
            "device_manufacturer": "Xiaomi",
            "device_category": "phone",
            "cpu_abi": "armeabi-v7a",
            "release_build": "",
            "density_dpi": 450,
            "display_density": "mdpi",
            "resolution": "2132x1080",
            "language": "zh",
            "timezone": 8,
            "access": "wifi",
            "not_request_sender": 0,
            "rom": "2302281012",
            "rom_version": "coloros__TQ3A.230705.001",
            "cdid": cdid,
            "sig_hash": "e152469dcfae090f5f09fd38fddb07ba",
            "openudid": openudid,
            "clientudid": clientudid,
            "region": "CN",
            "tz_name": "Asia/Shanghai",
            "tz_offset": 28800,
            "sim_serial_number": [],
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
        'User-Agent': "my.maya.android/370301 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        'Content-Type': "application/octet-stream",
        'log-encode-type': "gzip",
        'x-tt-request-tag': "t=0;n=1;s=0;p=0",
        'activity_now_client': "0",
        'x-ss-req-ticket': "1767902262953",
        'sdk-version': "2",
        'passport-sdk-version': "601441",
        'x-vc-bdturing-sdk-version': "4.1.1.cn",
        'content-type': "application/octet-stream;tt-data=a",
        'x-ss-stub': "56AE8287A429F36CC6DB3768BD4B0912",
        'x-ss-dp': "1349",
        'x-tt-trace-id': "00-9f2fb879010683974439016a76600545-9f2fb87901068397-01",
        # 'x-argus': "NwxgaQ==",
        # 'x-gorgon': "840430300000c1940d635adb9d462406d5ba36e2874707d20f9e",
        # 'x-helios': "B0+ldPBNMW3a5DRZ+QBZvp3seeGkQPu8jqW2QUXDz5focKtk",
        # 'x-khronos': "1767902263",
        # 'x-ladon': "+v8uFQ==",
        # 'x-medusa': "MgxgaRpHL6N+eW0qCLnORRVhrD9S+wABQOE7oIFugeAKGHO6ascQY+XdNoLAXGu2p5JOiitwwIBXO+S41tsn40vsleG2B0EotkudV3e3LTPPMVAtr5gq7m4ADqU23UJiRadQpStIO/rxwIfBAckbwrQLA8MIERboAjsHPS9iVTmU/v79HP9P/LTDdgan90df21CnpNnsKt1r1GT6IK2Ip0Lhi76J1B5KhaUXIK3n45jBLgM0G3p11sFIuI+b7gLD95G6ZE2lQ0AhTSoa2ZwMZQ13onErzjJMQwhp7Yb/R6kE/Zh7N1xi8334aDwB2bsFBjjAqUdThYv8vGx6ehXCYMohv/7QVnPuEg0tR5eRqlefn9C2Uy6cdq8s2t4jeuHPPHNn5UxwdVIjykP3cnCLhUvXrv4eWwUhx/7mnu5GHqNKjK3Dxyd5KQrvqy2pcNWNJ2i7ygXdg4KQAT/6hFzdPXbf9itrMSuxKebsCH+KiodY9fUAUMecyLYFbQ2p7YLtF0Fjr5QQ3HC10eYFjmKPtzhsDiP6aYF+hRqd1x31AE1CDmTtHyPOh3FZCEdHpgGikbZhbJ2IGx8xI/MP9wnmf1w7XQ4lcurIACV5L6KuzexUJ+8qV0QKawibo9b4/O5x9C/9rdQR70QYDOJfuLMMf3a6sMZagjzBRQoWNGIuvb4BEnXMz6MCiA2qIhAjx7VYOF2rHRIO4xLD4V57SXoKzsGg96U2h/kLCXBb7Eg/RJROURjFujMogfylsJaw1gPl9jy6LHyOF5tmXGazXQdGHhXN+HSUEx/zaUG4fRaNZbIldcAPwQXCH7HzdTbPFHCTnWD3oYSsr+xlU0kZwGeokgI9k0j9odCAzPeXI6F8AdBx52A5dbjU/vxdFFEKLplRI+Qb8gyl3NojVobn2LI7nfD51gzJawCPVHtD1BAVPf2XDTdAmLG27JRE7/CEiUMowdvxtEboozsjqrKq8f00d+4dXyyDbdAGZsKucq3hF4+EKMFYvqSp2PdAWTYzKLKa5pHdW1oMxssVZCjCSu13bb477xryMJcUOI0JwZ/258JLX5RLRqOvUvrOo1f6U2P6vxn/+r8Z/6hL",
        # 'Cookie': "passport_csrf_token=b9388a7ca9d2eccb604d7a244f0f1b19; passport_csrf_token_default=b9388a7ca9d2eccb604d7a244f0f1b19"
    }

    sign_headers, sign_urls = sign_android(url=url, params=params, data=register_body, header=headers, cell=True, log=False)
    try:
        # print(sign_urls)
        # resp = requests.post(sign_urls, data=register_body, headers=headers,proxies=proxies)

        resp = requests.post(sign_urls, data=register_body, headers=sign_headers,proxies=proxies,timeout=30,verify=False)
        resp_json = resp.json()
        if resp_json.get('install_id', 0) == 0 or resp_json.get('device_id', 0) == 0:
            print('【注册失败!】', resp.json())
            return resp.json()
        else:
            # s1 = f"https://api5-normal-m-hj.amemv.com/aweme/v1/aweme/detail/?aweme_id=7501871923145067812&origin_type=web&request_source=0&is_story=0&location_permission=0&aweme_type=1&recommend_collect_feedback=0&iid={resp_json['install_id']}&device_id={resp_json['device_id']}&ac=wifi&channel=tengxun_1128_1025&aid=1128&app_name=aweme&version_code=190000&version_name=19.0.0&device_platform=android&os=android&ssmix=a&device_type=2203121C&device_brand=Xiaomi&language=zh&os_api=33&os_version=13&manifest_version_code=190001&resolution=1440*3007&dpi=560&update_version_code=19009900&_rticket=1740576157432&package=com.ss.android.ugc.aweme&mcc_mnc=46001&cpu_support64=true&host_abi=armeabi-v7a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&need_personal_recommend=1&is_android_pad=0&ts=1740576156&cdid={cdid}&oaid=4067ae1c4d619ec8"
            # print('s1', s1)
            # headers = {
            #     "Host": "api5-normal-m-hj.amemv.com",
            #     "x-tt-dt": resp_json['device_token'],
            #     "activity_now_client": "1740576158403",
            #     "sdk-version": "2",
            #     "passport-sdk-version": "20356",
            #     "x-ss-req-ticket": "1740576157433",
            #     "x-vc-bdturing-sdk-version": "2.2.1.cn",
            #     "x-tt-request-tag": "s=1;p=0",
            #     "x-ss-dp": "1128",
            #     "x-tt-trace-id": resp.headers["x-tt-trace-id"],
            #     "user-agent": "com.ss.android.ugc.aweme/190001 (Linux; U; Android 13; zh_CN; 2203121C; Build/TKQ1.220829.002; Cronet/TTNetVersion:a7be068c 2021-12-02 QuicVersion:68cae75d 2021-08-12)",
            # }
            #
            # response = requests.get(s1, headers=headers)
            # print(response.text)
            return resp_json
    except Exception as e:
        print(print('【注册失败!】', e,proxies))


if __name__ == '__main__':
    print(device_register({
        # 'http': 'http://t13610080308813:inevg9s5@l505.kdltps.com:15818',
        # 'https': 'http://t13610080308813:inevg9s5@l505.kdltps.com:15818',
    }))
