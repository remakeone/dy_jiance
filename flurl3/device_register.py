import json
import uuid
import random
import time
from urllib.parse import urlencode

import requests
import hashlib
import string

from flurl.ttencrypt import ttencrypt


def encrypt_tt(tt):
    encrypt = bytes.fromhex(ttencrypt().encrypt(json.dumps(tt).replace(" ", "")))
    return encrypt


def create_xiaomi_device():
    # 品牌固定为 Xiaomi
    brand = "Xiaomi"

    # 现代型号：如 "24129PN74C"
    year = str(random.randint(20, 25))
    month = str(random.randint(1, 12)).zfill(2)
    sequence = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    region = random.choice(["C", "G", "I"])
    model = year + month + sequence + region

    # 分辨率
    resolution_options = ["1080x2400", "1220x2712", "1260x2800", "1440x3200", "1344x2992"]
    resolution = random.choice(resolution_options)

    # display_density 和 dpi
    density_options = {"hdpi": (120, 240), "xhdpi": (240, 320), "xxhdpi": (320, 480), "xxxhdpi": (480, 640)}
    density = random.choice(["xxhdpi", "xxxhdpi"]) if resolution in ["1440x3200", "1344x2992"] else random.choice(
        list(density_options.keys()))
    dpi = random.randint(density_options[density][0], density_options[density][1])

    # Build
    prefix = ''.join(random.choices(string.ascii_uppercase, k=3)) + random.choice(string.digits)
    build_date = year + month + str(random.randint(1, 28)).zfill(2)
    revision = str(random.randint(1, 999)).zfill(3)
    build = f"{prefix}.{build_date}.{revision}"

    # ROM 和 rom_version
    major_version = str(random.randint(13, 15))
    minor_version = str(random.randint(0, 9))
    patch_version = str(random.randint(0, 20))
    build_version = str(random.randint(0, 9))
    build_code = ''.join(random.choices(string.ascii_uppercase, k=4)) + random.choice(["CNXM", "INXM", "EUXM"])
    rom = f"MIUI-V{major_version}.{minor_version}.{patch_version}.{build_version}.{build_code}"
    rom_version = f"miui_V{major_version}0_V{major_version}.{minor_version}.{patch_version}.{build_version}.{build_code}"

    # 固定字段
    device_platform = "android"
    os = "Android"

    # os_version 和 os_api
    os_options = {"11": 30, "12": 31, "13": 33, "14": 34, "15": 35}
    os_version = random.choice(list(os_options.keys()))
    os_api = os_options[os_version]

    # mcc_mnc 和 carrier（仅中国运营商）
    china_operators = {"46000": "中国移动", "46002": "中国移动", "46007": "中国移动", "46001": "中国联通",
                       "46006": "中国联通", "46009": "中国联通", "46003": "中国电信", "46005": "中国电信",
                       "46011": "中国电信"}
    mcc_mnc = random.choice(list(china_operators.keys()))
    carrier = china_operators[mcc_mnc]

    # cpu_abi
    cpu_abi_options = ["armeabi-v7a", "arm64-v8a"]  # 小米设备常见 ABI
    cpu_abi = random.choice(cpu_abi_options)

    return {
        "brand": brand,
        "model": model,
        "resolution": resolution,
        "dpi": dpi,
        "build": build,
        "rom": rom,
        "rom_version": rom_version,
        "device_platform": device_platform,
        "display_density": density,
        "os": os,
        "os_version": os_version,
        "os_api": os_api,
        "mcc_mnc": mcc_mnc,
        "carrier": carrier,
        "cpu_abi": cpu_abi
    }


def device_register(proxies=None):
    cdid = str(uuid.uuid4())
    # openudid = binascii.hexlify(os.urandom(8)).decode()
    channel = "xiaomi_1128_64"
    simple_device = create_xiaomi_device()
    # print("设备信息：",simple_device)
    url = "https://log.snssdk.com/service/2/device_register/"
    params = {
        "tt_data": "a",
        "ac": "wifi",
        "channel": channel,
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "380900",
        "version_name": "38.9.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        'device_type': simple_device['model'],  # 这是一个变量
        'device_brand': simple_device['brand'],
        "language": "zh",
        "os_api": "30",
        "os_version": "11",
        "manifest_version_code": "380901",
        "resolution": "1440*2712",
        "dpi": "560",
        "update_version_code": "38909900",
        '_rticket': str(round(time.time() * 1000)),
        "package": "com.ss.android.ugc.aweme",
        "first_launch_timestamp": "1780247969",
        "last_deeplink_update_version_code": "0",
        "cpu_support64": "true",
        # "host_abi": "arm64-v8a",
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "is_preinstall": "0",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "is_android_fold": "0",
        'ts': str(round(time.time())),
        'cdid': cdid,  # 这是一个变量
        "md": "0",
        "cronet_version": "5e677c20_2026-03-23",
        "ttnet_version": "4.2.278.4-douyin",
        "use_store_region_cookie": "1",
        'mcc_mnc': simple_device['mcc_mnc'],
        'host_abi': simple_device['cpu_abi'],

    }
    register_info = {
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": "抖音",
            # "update_version_code": 34009900,
            "update_version_code": 38909900,
            # "manifest_version_code": 340001,
            "manifest_version_code": 380901,
            "app_version_minor": "",
            "aid": 1128,
            "channel": channel,
            # "appkey": "57bfa27c67e58e7d920028d3",
            "package": "com.ss.android.ugc.aweme",
            # "app_version": "34.0.0",
            # "version_code": 340000,
            "app_version": "38.9.0",
            "version_code": 380900,
            "sdk_version": "3.7.3-alpha.16-doubleupload",
            "sdk_target_version": 29,
            "git_hash": "f86c2ef",
            "os": "Android",
            "os_version": "13",
            "os_api": 33,
            "device_model": simple_device['model'],
            "device_brand": simple_device['brand'],
            "device_manufacturer": simple_device['brand'],
            "cpu_abi": simple_device['cpu_abi'],
            "release_build": "",
            "density_dpi": 560,
            "display_density": "mdpi",
            "resolution": "3007x1440",
            "language": "zh",
            "timezone": 8,
            "access": "wifi",
            "not_request_sender": 0,
            "carrier": simple_device['carrier'],
            "mcc_mnc": simple_device['mcc_mnc'],
            "rom": simple_device['rom'],
            "rom_version": simple_device['rom_version'],
            "cdid": cdid,
            "sig_hash": "aea615ab910015038f73c47e45d21466",
            "openudid": "86c34f420d9ff2aa",
            "clientudid": str(uuid.uuid4()),
            "region": "CN",
            "tz_name": "Asia/Shanghai",
            "tz_offset": 28800,
            "sim_region": "cn",
            "sim_serial_number": [],
            # "rom": "eng.root.20230501.013644",
            # "rom_version": "RP1A 200720.009 release-keys",
            # "cdid": "a914fb24-ab1c-478f-a9d7-a66b530ff059",
            # "sig_hash": "aea615ab910015038f73c47e45d21466",
            # "openudid": "fa3ccdb4d33e701c",
            # "clientudid": "9be38ae8-be84-4a58-b3d0-be7f2c8a9ca6",
            # "oaid": {
            #     "req_id": str(uuid.uuid4()),
            #     "hw_id_version_code": "0",
            #     "take_ms": "75",
            #     "is_track_limited": "false",
            #     "query_times": "1",
            #     "id": "4067ae1c4d619ec9",
            #     "time": str(round(time.time() * 1000))
            # },
            # 'oaid': "72121217a960884d",
            "oaid_may_support": False,
            "req_id": str(uuid.uuid4()),
            "device_platform": "android",
            "custom": {
                "app_session_id_vcloud": "",
                "filter_warn": 0,
                "web_ua": f"Mozilla/5.0 (Linux; Android 13; {simple_device['model']} Build/{simple_device['build']}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36",
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
        "User-Agent": f"com.ss.android.ugc.aweme/340000 (Linux; U; Android 13; zh_CN; {simple_device['model']}; Build/{simple_device['build']};tt-ok/3.12.13.4-tiktok)",
        "x-ss-req-ticket": str(int(time.time())) + "000",
        "x-tt-dm-status": "login=0;ct=0",
    }
    # sign_headers, sign_urls = Encrypt().sign_android(url=url, params=params, data=register_body, header=headers, cell=True, log=True)
    try:
        url = url + "?" + urlencode(params)
        resp = requests.post(url, data=register_body, headers=headers, proxies=proxies, timeout=30)
        resp_json = resp.json()
        if resp_json.get('install_id', 0) == 0 or resp_json.get('device_id', 0) == 0:
            print('【注册失败!】', resp.json())
            return None
        else:
            # s1 = f"https://api5-normal-m-hj.amemv.com/aweme/v1/aweme/detail/?aweme_id=7438333354237267251&origin_type=web&request_source=0&is_story=0&location_permission=0&aweme_type=1&recommend_collect_feedback=0&iid={resp_json['install_id']}&device_id={resp_json['device_id']}&ac=wifi&channel=tengxun_1128_1025&aid=1128&app_name=aweme&version_code=190000&version_name=19.0.0&device_platform=android&os=android&ssmix=a&device_type=2203121C&device_brand=Xiaomi&language=zh&os_api=33&os_version=13&manifest_version_code=190001&resolution=1440*3007&dpi=560&update_version_code=19009900&_rticket=1740576157432&package=com.ss.android.ugc.aweme&mcc_mnc=46001&cpu_support64=true&host_abi=armeabi-v7a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&need_personal_recommend=1&is_android_pad=0&ts=1740576156&cdid={cdid}&oaid=4067ae1c4d619ec8"
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
            # response = requests.get(s1, headers=headers)
            # print(response.text)
            resp_json = resp_json | params
            if 'install_id' not in resp_json:
                resp_json['iid'] = resp_json['install_id']
            resp_json['channel'] = channel
            if 'iid' not in resp_json:
                resp_json['iid'] = resp_json['install_id']
            return resp_json
    except Exception as e:
        return None
        # print(print('【注册失败!】', e))


if __name__ == '__main__':
    # print(device_register(daili="hw.shanchendaili.com:1000:4Dn2De0Wr5Wd-res-any-sid-52892729:6Ty3Yc3Ve8Mc8Tb6Cq"))
    print(device_register({
        'http': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
        'https': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
    }))
