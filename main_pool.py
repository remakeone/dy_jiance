from datetime import datetime
import json
import os
import re
import time
import traceback
import urllib
import uuid
import random

import pandas as pd
from loguru import logger
import requests

from card_password import read_card_password, init_card_password
from flurl.core import core_sixgod

logger.add('log.log', rotation='10 MB', encoding='utf-8')
# # 方法：为未在环境中设置的项提供默认值（不覆盖 .env/系统环境中的值）
# os.environ.setdefault("PROXY_ENABLED", "true")
# os.environ.setdefault("PROXY_BASE_URL", "http://206.237.13.225:9999/proxy")
# try:
#     from module import proxy_patch  # noqa: F401
# except Exception as _:
#     print(_)
#     # 若代理模块导入失败，不影响原有逻辑
#     raise _
from concurrent.futures import ThreadPoolExecutor
from register_device import device_register


def exc_res(res):
    if res.get('message') == 'error':
        logger.error(f'注册失败：{res}')
        if res.get('data', {}).get('error_code') == 2140:
            logger.error("绑定")
            return False, '绑定'
        else:
            logger.error('未知错误')
            return False, '未知错误'

    elif res.get('message') == 'success':
        logger.info(f'注册成功：{res}')
        return True, res.get('data', {}).get("name") or '未检索到用户名'
    else:
        logger.error(f'未知状态：{res}')
        return False, '未知状态'


def get_email_code(url):
    for _ in range(20):
        for i in range(10):
            try:
                response = requests.get(url)
                break
            except:
                logger.error(f'获取邮箱时网络异常，重试{i}/10')
                time.sleep(1)
        else:
            raise Exception('获取邮箱时网络异常，重试10次后失败')

        if response.text:
            if "没有可显示的邮件" not in response.text:
                # 正则表达式提取验证码和时间
                captcha_pattern = r'(\d{6}) 是您的验证码'  # 匹配6位数字的验证码
                time_pattern = r'时间：</span><span class="v">(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})</span>'

                captcha = re.search(captcha_pattern, response.text)
                time_text = re.search(time_pattern, response.text)

                # 提取结果
                captcha_code = captcha.group(1) if captcha else None
                timestamp = time_text.group(1) if time_text else None

                if captcha_code and timestamp:
                    # 将时间字符串转为 datetime 对象
                    timestamp_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    current_time = datetime.now()

                    # 如果时间差超过 60 秒，认为验证码无效，继续请求
                    if (current_time - timestamp_time).total_seconds() > 60:
                        print("验证码不是最新验证码，等待3秒重新请求...")
                        time.sleep(3)
                    else:
                        return captcha_code
                else:
                    print("邮箱格式有误，等待3秒重新请求...")
                    time.sleep(3)
            else:
                print("响应为空，等待3秒重新请求...")
                time.sleep(3)
        else:
            print("网络卡顿，等待3秒重新请求...")
            time.sleep(3)
    else:
        raise Exception('接码失败')

def get_filename_name(filepath):
    filenames = [i for i in os.listdir(filepath) if "~" not in i]
    # print(len(filenames))
    # index = 0
    if len(filenames) == 0:
        print(f'当前目录为：{filepath},未检测到输入文件。')
        input("输入任意内容结束")
        exit()

    if len(filenames) == 1:
        print('只检测到一个文件名，直接返回')
        return os.path.join(filepath, filenames[0]), filenames[0]

    print('请选择输入文件')
    for index, filename in enumerate(filenames):
        print(f"{index}: {filename}")

    while True:
        try:
            index = int(input("请输入文件前的序号"))
        except:
            print('输入错误，请重新输入，请确保输入的是数字')
            continue

        # 检测数字是否合法，合法就结束输入，否则继续输入
        if index < 0 or index >= len(filenames):
            print("数字不合法，超出可取范围，请重新输入")
        else:
            break

    # if len(filenames) != 1:
    #     raise FileExistsError(f"文件数量异常。只允许为1。目前为：{len(filenames)}")
    return os.path.join(filepath, filenames[index]), filenames[index]


def read_input_file(filename,register_ed):
    result = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            email,email_url = line.split('----')
            if email in register_ed:
                logger.info(f'邮箱 {email} 已注册，跳过')
                continue
            result.append([email,email_url])
            # print(line)
    return result


def get_proxies(api_url):
    # api_url =
    # 获取API接口返回的代理IP

    if isinstance(api_url, dict):
        return api_url
    for i in range(3):
        try:
            proxy_ip = requests.get(api_url).text
            if not proxy_ip or 'error' in proxy_ip:
                raise Exception(f"获取代理IP失败:{proxy_ip}")
            # 用户名密码认证(私密代理/独享代理)
            proxies = {
                'http': f'http://{proxy_ip.strip()}',
                'https': f'http://{proxy_ip.strip()}',
            }
            return proxies
        except Exception as e:
            logger.error(f"获取代理IP失败:{e},重试{i}/3次")
            time.sleep(random.randint(1, 3))
            continue
    raise Exception("获取代理IP失败")


def toke_phone_num(phone_num):
    bytes_phone_number_data = phone_num.encode("utf-8")
    xor_bytes = bytes([byte ^ 5 for byte in bytes_phone_number_data])
    # 逐字节转换为十六进制字符串并拼接
    hex_string = ''.join(format(byte, '02x') for byte in xor_bytes)
    return hex_string


def encrypt_tt(tt):
    """加密device register info或者app log
    :param tt:
    :return:
    """
    encrypt = bytes.fromhex(ttencrypt().encrypt(json.dumps(tt, separators=(",", ";"))))
    return encrypt


def xor(s):
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    result = ''
    for b in arr:
        result += chars[(b & 255) >> 4]
        result += chars[(b & 255) & 15]
    return result


def fetch_data(url):
    while True:
        response = requests.get(url)
        if response.text:
            if "没有可显示的邮件" not in response.text:
                # 正则表达式提取验证码和时间
                captcha_pattern = r'(\d{6}) 是您的验证码'  # 匹配6位数字的验证码
                time_pattern = r'时间：</span><span class="v">(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})</span>'

                captcha = re.search(captcha_pattern, response.text)
                time_text = re.search(time_pattern, response.text)

                # 提取结果
                captcha_code = captcha.group(1) if captcha else None
                timestamp = time_text.group(1) if time_text else None

                if captcha_code and timestamp:
                    # 将时间字符串转为 datetime 对象
                    timestamp_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    current_time = datetime.now()

                    # 如果时间差超过 60 秒，认为验证码无效，继续请求
                    if (current_time - timestamp_time).total_seconds() > 60:
                        print("验证码不是最新验证码，等待3秒重新请求...")
                        time.sleep(3)
                    else:
                        return captcha_code, timestamp
                else:
                    print("邮箱格式有误，等待3秒重新请求...")
                    time.sleep(3)
            else:
                print("响应为空，等待3秒重新请求...")
                time.sleep(3)
        else:
            print("网络卡顿，等待3秒重新请求...")
            time.sleep(3)


def send_code(email, dev, uuid_without_dashes, proxies):
    email_code = toke_phone_num(email)
    # 拼接发送请求的 url
    url = "https://api3-normal-c-lq.amemv.com/passport/email/send_code/"

    params = {
        "passport-sdk-version": "601431",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "iid": dev["iid"],
        "device_id": dev["device_id"],
        "ac": "wifi",
        "channel": dev['channel'],
        "aid": "1128",
        "app_name": dev["app_name"],
        "version_code": "370100",
        "version_name": "37.1.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": dev["device_type"],
        "device_brand": dev["device_brand"],
        "language": "zh",
        "os_api": dev["os_api"],
        "os_version": dev["os_version"],
        "manifest_version_code": "370100",
        "resolution": dev["resolution"],
        "dpi": dev["dpi"],
        "update_version_code": "37109900",
        "_rticket": "1770624652624",
        "package": "com.ss.android.ugc.aweme.mobile",
        # "package": "com.ss.android.ugc.livepro",
        "first_launch_timestamp": "1766049783",
        "last_deeplink_update_version_code": "0",
        "cpu_support64": "true",
        "host_abi": dev["host_abi"],
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "is_preinstall": "0",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "is_android_fold": "0",
        "ts": "1770624650",
        "cdid": dev["cdid"],
        "md": "0",
        "cronet_version": "b9c3e521_2025-09-09",
        "ttnet_version": "4.2.243.16-douyin",
        "use_store_region_cookie": "1"
    }

    headers = {
        # ":method": "POST",
        # ":authority": "api3-normal-c-lq.amemv.com",
        # ":path": "/passport/email/send_code/?passport-sdk-version=601431&request_from_account_sdk=1&is_from_ttaccountsdk=1&iid=7604774384485746213&device_id=2051038435907593&ac=wifi&channel=googlePlay&aid=1128&app_name=aweme&version_code=370100&version_name=37.1.0&device_platform=android&os=android&ssmix=a&device_type=OPPO+A4&device_brand=OPPO&language=zh&os_api=33&os_version=13&manifest_version_code=370100&resolution=1080*2132&dpi=450&update_version_code=37109900&_rticket=1770624652624&package=com.ss.android.ugc.aweme.mobile&first_launch_timestamp=1766049783&last_deeplink_update_version_code=0&cpu_support64=true&host_abi=arm64-v8a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&is_preinstall=0&need_personal_recommend=1&is_android_pad=0&is_android_fold=0&ts=1770624650&cdid=c85ccce4-d2fa-49b4-8ebb-08d3ecaa5392&md=0&cronet_version=b9c3e521_2025-09-09&ttnet_version=4.2.243.16-douyin&use_store_region_cookie=1",
        # ":scheme": "https",
        # "content-length": "486",
        # "cookie": "ttreq=1$5d2ed25398d796fc11961d1bf9b034f0a256823f",
        # "x-tt-passport-csrf-token": "b224627dccef94606c9aeac84d0cb414",
        # "x-tt-dt": "AAA27EDINIESDZL6JZAWV47GMZYVNPJRIRWHL3TXUOOKAFN7KH52J5M7MHH4AYSMQNXMFJFOLWZXGPQGSKQJA5U6ZZTHUSLPMWVEJGO4J4XIKSMO73OJUAKWDVILI",
        "activity_now_client": "1770624651494",
        "x-ss-req-ticket": "1770624652626",
        "bd-ticket-guard-tee-status": "1",
        "bd-ticket-guard-display-os-version": "TQ3A.230705.001",
        "sdk-version": "2",
        # "bd-ticket-guard-ree-public-key": "BGlj0nh7FkMzE3yj+SoDtJL5je3nDX82ICsaEaybgIoRxoBvCiVXV3gXPy6qaljlJboSMYKo3bxOfwtoxZJEDOg=",
        "bd-ticket-guard-version": "3",
        "bd-ticket-guard-iteration-version": "2",
        # "bd-ticket-guard-client-cert": "cHViLkJHb2U1bWkwUC9IazJZQ2xoeHlzbnNmWXJmSlhMTWtwMC9HNi9wZHQyQ0swVktrZm5rZGFWTytJM1M1SVc0VjdaVlVVcFpZUU94alVjQWxUSTJ3d0VGVT0=",
        # "bd-ticket-guard-server-cert-sn": "533240336124694022040808462028007165443034493949",
        # "x-tt-passport-trace-id": "login_06ea97c18dda4b3daae03d7860146877",
        "x-tt-passport-trace-id": f"login_{uuid_without_dashes}",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "601431",
        "x-vc-bdturing-sdk-version": "4.1.1.cn",
        # "x-tt-cipher-version": "1.0.0",
        # "x-tt-encrypt-info": "1",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "Content-Type": "application/octet-stream",
        # "x-ss-stub": "56229ED539A3C5729C64A58A75D1A9BD",
        "x-tt-request-tag": "s=0;p=0",
        "x-ss-dp": "1128",
        # "x-tt-trace-id": "00-417416f70d749689964980967fe50468-417416f70d749689-01",
        # "user-agent": "com.ss.android.ugc.aweme.mobile/370100 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        "User-agent": "com.ss.android.ugc.aweme.mobile/370100 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        # "accept-encoding": "gzip, deflate, br"
        # "x-argus": "jJaJaQ==",
        # "x-gorgon": "840410ac0000ed532cde52035f4bfe0aa3dfcb730a6b02852973",
        # "x-helios": "tdK0LY1LtB64HMIZz3ECodfcAomQyGv9iUcmOzNX8iEttXpL",
        # "x-khronos": "1770624652",
        # "x-ladon": "9bIRew==",
        # "x-medusa": "iZaJaaHdxqPF44QqsyMnRa77RT85PQABZ3UU3P1Cgd0CGPVefAXpUjPVp8/4TTQrRBXZoEnzeB0kms60eRJ01RqcO6Ogtro02X9+xbWacTQLHKRYl3sdKGOUwlTBokzMCK7HmhF/QUQra6Tt8yaWsqdaxJJxv4esE+dGf0e6j+P6Vx2SCvH/cgso4wz4H74dZmAGhj0EhV/bBKYeJ8biL01QmLMJU+0yS4qNp5D2g2SPZ/uUn+TS4h7ab5GWwXp4LD5KPfJO19B1RPRf5gabMsFOyllOKBOqZSuqG7/ygPn/kavfsgQFF50WcaLVeEhsid6Apk8gFV6m8sUA3jqV76f09bu6nQi01aLQOlwUOUjhNq6IvoxpZDniwJLmyk9EB2yTRRSlVkMlaZsUOOcAPPv38zlvbrKXzSY7ald0mU0owUy3epsJL1dKQy02oRNCRIIDOHV9A9+6P3REJUI8kIX0dLs8hv64CtqT8B+OvkcpI/0uvhmaSiI3rQgi8cMb3dCKxT2vnR5wpVeplLF/5lQlIvFI6z2lSZialbkoQImi+SfwixRZKZNOn7CZbqRiWUedBB5pkKK/KEB8HWEIuJyExP+MSVDKwMaXLXX99T32eJO1BQjfwSWrUjFsbax5K2WWaQH69bGbQUPzYVRAgrEnFr9sVkj4UoZ8czVzkJbUk1A5ro42RDFCfu+7n2nqHokmoPxVni21xcz1dGLHGTm7ZU+7QDdwZNkSuGVfkUGXnWjpdWX3FWfeuegd9v1zfNsLelLRNedI6BnZz8GSX+nYDWIsntC0XeMuYoiRYVkUwBnCfAHWBQLMJt/lROOwx0s7jnNS0HJUiWb7xspg+y67JeT4XEeQsSyOh1YKlFS37lOtdCBKvCUUU5FTpOwN9UcsD5dgCnvLMiTZ02hnFB+OFCYa2bkLCXD4JV7CHCeWaL8Mvfa1iCzUt3EeADgA6pBfAtWntQlCMeUCH/AxSNHLQLjrWd2E1hgy63axiVw5O/X1XPrE/TAXx1WnoGe8kF3QC4flqZxxra2c7iQNcpllpBD1aGvs8x6v8PufEobNhAedSeIjrwbrH6joCT9CZGh9IqdpUnpcJK8n5STBfpuFXObKFDd6KxpkuLpDB0+6yHf5Rd9kWMHTXvtLUXsvOCsAyCYBRH7iMJ8uR/iQ+5CtyxKpqxa94tI58mO+uszgtn9kFkqjguBk8TEl3Xt22qXCQm82//jHNv/4x+cp"
    }

    cookie = {
        "passport_csrf_token": "b224627dccef94606c9aeac84d0cb414",
        "passport_csrf_token_default": "b224627dccef94606c9aeac84d0cb414",
        "store-region": "cn-hk",
        "store-region-src": "did",
        "odin_tt": "f364e36cd7250bd08e98b2eca5e1060f4ca2e3400241b303f9ba65a0a9ef1d0150686574b89200e8aa4614474ec165670089ed8b9e98e20023322362866563c248b5d38750765db8991a678d31775e0d",
        "install_id": "7604774384485746213",
        "ttreq": "1$5d2ed25398d796fc11961d1bf9b034f0a256823f"
    }

    # register_info = {
    #     "is_vcd": "0",
    #     "reg_cookie_opt": "true",
    #     "ttnet_sdk_version": "4.2.243.28-douyin",
    #     "auth_sdk_version": "4.6.2.4-bugfix",
    #     "mix_mode": 1,
    #     "account_app_language": "zh",
    #     "language": "zh",
    #     "multi_login": 1,
    #     "type": 3433,
    #     # "sec_sdk_version": 67700736,
    #     "sec_sdk_version": 67700992,
    #     "account_sdk_source": "app",
    #     "passport_support_flow": "real_name_check,choose_account,captcha,verify",
    #     "verify_sdk_version": "4.1.1.cn",
    #     "is_from_iesaccountsaas": 1,
    #     "email": email_code
    #     # "email": "6f6273327436757745343d3d68646c692b6666"
    # }
    register_info = {
        "is_vcd": "0",
        "reg_cookie_opt": "true",
        "account_sdk_source": "app",
        "passport_support_flow": "real_name_check,choose_account,captcha,verify",
        "mix_mode": "1",
        "is_from_iesaccountsaas": "1",
        "multi_login": "1",
        "type": "3433",
            "email": email_code
    }

    # 调用接口获取六神，并将六神更新至headers，更新业务接口params。注意，业务请求是POST时传data参数，GET不传。
    sixgoddata = core_sixgod(surl=url, params=params, data=register_info, devices={}, header=headers, log=False)
    sign_headers = sixgoddata["header"]
    sign_urls = sixgoddata["url"]

    # 请求体加密过程
    # register_body = encrypt_tt(register_info)
    for i in range(5):
        try:
            print(proxies)
            resp = requests.post(sign_urls, data=register_info, headers=sign_headers, proxies=proxies,timeout=30)
            return resp.json()
        except Exception as e:
            if '503' in str(e):
                raise Exception('ip无效')
            logger.debug(f'第{i}次请求失败,e:{e}')
    else:
        raise Exception("网络异常")


def submit_code(email, code, dev, uuid_without_dashes, proxies):
    # code = '762753'
    end_code = toke_phone_num(code)
    # mail = 'wrapks97@86mail.cc'
    email_code = toke_phone_num(email)

    # 拼接发送请求的 url
    url = "https://api3-normal-c-lq.amemv.com/passport/email/quick_login/"

    params = {
        "passport-sdk-version": "601431",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "iid": dev["iid"],
        "device_id": dev["device_id"],
        "ac": dev["device_id"],
        "channel": "googlePlay",
        "aid": dev["aid"],
        "app_name": dev["app_name"],
        "version_code": "370100",
        "version_name": "37.1.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": dev["device_type"],
        "device_brand": dev["device_brand"],
        "language": "zh",
        "os_api": dev["os_api"],
        "os_version": dev["os_version"],
        "manifest_version_code": "370100",
        "resolution": dev["resolution"],
        "dpi": dev["dpi"],
        "update_version_code": "37109900",
        "_rticket": "1770624661352",
        "package": "com.ss.android.ugc.aweme.mobile",
        "first_launch_timestamp": "1766049783",
        "last_deeplink_update_version_code": "0",
        "cpu_support64": "true",
        "host_abi": dev["host_abi"],
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "is_preinstall": "0",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "is_android_fold": "0",
        "ts": "1770624658",
        "cdid": dev["cdid"],
        "md": "0",
        "cronet_version": "b9c3e521_2025-09-09",
        "ttnet_version": "4.2.243.16-douyin",
        "use_store_region_cookie": "1"
    }

    headers = {
        # ":method": "POST",
        # ":authority": "api3-normal-c-lq.amemv.com",
        # ":path": "/passport/email/quick_login/?passport-sdk-version=601431&request_from_account_sdk=1&is_from_ttaccountsdk=1&iid=7604774384485746213&device_id=2051038435907593&ac=wifi&channel=googlePlay&aid=1128&app_name=aweme&version_code=370100&version_name=37.1.0&device_platform=android&os=android&ssmix=a&device_type=OPPO+A4&device_brand=OPPO&language=zh&os_api=33&os_version=13&manifest_version_code=370100&resolution=1080*2132&dpi=450&update_version_code=37109900&_rticket=1770624661352&package=com.ss.android.ugc.aweme.mobile&first_launch_timestamp=1766049783&last_deeplink_update_version_code=0&cpu_support64=true&host_abi=arm64-v8a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&is_preinstall=0&need_personal_recommend=1&is_android_pad=0&is_android_fold=0&ts=1770624658&cdid=c85ccce4-d2fa-49b4-8ebb-08d3ecaa5392&md=0&cronet_version=b9c3e521_2025-09-09&ttnet_version=4.2.243.16-douyin&use_store_region_cookie=1",
        # ":scheme": "https",
        # "content-length": "299",
        # "cookie": "ttreq=1$5d2ed25398d796fc11961d1bf9b034f0a256823f",
        # "x-tt-passport-csrf-token": "b224627dccef94606c9aeac84d0cb414",
        # "x-tt-dt": "AAA27EDINIESDZL6JZAWV47GMZYVNPJRIRWHL3TXUOOKAFN7KH52J5M7MHH4AYSMQNXMFJFOLWZXGPQGSKQJA5U6ZZTHUSLPMWVEJGO4J4XIKSMO73OJUAKWDVILI",
        "activity_now_client": "1770624660222",
        "x-ss-req-ticket": "1770624661354",
        "bd-ticket-guard-display-os-version": "TQ3A.230705.001",
        # "bd-ticket-guard-ree-public-key": "BGlj0nh7FkMzE3yj+SoDtJL5je3nDX82ICsaEaybgIoRxoBvCiVXV3gXPy6qaljlJboSMYKo3bxOfwtoxZJEDOg=",
        "bd-ticket-guard-version": "3",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "bd-ticket-guard-tee-status": "1",
        "sdk-version": "2",
        "bd-ticket-guard-iteration-version": "2",
        # "bd-ticket-guard-client-cert": "cHViLkJHb2U1bWkwUC9IazJZQ2xoeHlzbnNmWXJmSlhMTWtwMC9HNi9wZHQyQ0swVktrZm5rZGFWTytJM1M1SVc0VjdaVlVVcFpZUU94alVjQWxUSTJ3d0VGVT0=",
        # "bd-ticket-guard-server-cert-sn": "533240336124694022040808462028007165443034493949",
        "x-tt-passport-trace-id": f"login_{uuid_without_dashes}",
        # "x-tt-passport-verify-portrait": "14617606-545c-418a-9019-e63fc588ef7f.login",
        "passport-sdk-version": "601431",
        "x-vc-bdturing-sdk-version": "4.1.1.cn",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "x-ss-stub": "B5EF2D7D77671E138AFAED3A0B666A58",
        # "x-bd-content-encoding": "zstd",
        "x-tt-request-tag": "s=0;p=0",
        "x-ss-dp": "1128",
        # "x-tt-trace-id": "00-4174391b0d7496899649809f21910468-4174391b0d749689-01",
        "User-agent": "com.ss.android.ugc.aweme.mobile/370100 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        # "accept-encoding": "gzip, deflate, br"
        # "x-argus": "lZaJaQ==",
        # "x-gorgon": "8404106c000014c648e6357ec2b8c767e7f3160b98ff603a9488",
        # "x-helios": "qwiJdDgFsLJIcz8bqASdGdvvqUCC8bXL67KE88RyNfu23lgZ",
        # "x-khronos": "1770624661",
        # "x-ladon": "y8P4Xg==",
        # "x-medusa": "kJaJabjdxqPc44QqqiMnRbf7RT+0CAABUzUKig5wAb4FGP2WeBz+hIwH6uXBiSpa9+VxJl5SIbF0ySLJ46+ux1ytUojIQ3IpbOiyFO3ka9tMlx1iMrcfRwDt0u12H316ltKfJM+YcRPKBfJKr1osoxaRL9KxOKZhBvtXNL8/Ci8JwbGiDzbp2Lsflhk93DTvmybUMWWAOCnOFGabqMcCjYn9S3Gfz/34qzEjsQyHRjG90KQgnq7zGXIIECbDm3C8C+E26TChsRBf8q4d0K9azmCWfoS46cZimUCC/XoTNpz7Ga5omU01hyEGUEZykmpjQCntdGfb3iZRlRcmu/J7vUXOJOIxY5ia2fuc9RPoILEbALXFWeN8xA/Sc6QSrGz/Ye+dc+pmef3vihswVmMLc+D/mu686EcbW3MsWjAycaJjP6ARD9L/4iJynUYmTZ+cJ4X6rbCN52JYSjiRTrBbnBoaMy6fHyxmBCDi+tYhcM+00ohkJ5VNVW4lnvJAgWzVbi7pXwtyS/c7SPo7I0RuRqRiN5F2nwc7ZzOSN/nvOZfQdgU6T70B7nqT/lyboRhBEU4d5oz/ZoKcPZvChY/WiaGgr8achfLKP4xCdhWrR/9V3jLy30E8jIGVzdzrLA3rIa96myw6SLGvxELnrwE3T0HJAIoOwEUShQhKa/NJ4N6dUy139VfF8KaPwKbuLaBoef4ErWqRiFwGf0+1I7vJJHdA3TxXGOEH+oplb+MF1Dw7XTYlP1aD0cBuUg5CsTCi2a8snur10GVy1ZKSNEkA1qSdHZnq5MvR4Yvl3aCFq/c1hoFiAteDhLNkZsZC3GTxlnsFDJSC6KKVZv4UByBJ1YUNW5xqb/raDNEmMzeSRJXx9ki4Z5MBEojdKleYO2iv9BjSMjn4aBJVI6i5CgxT1BXti/R98EqPk0qxu6Txs/2j8ySWRbgYglWI8eNDM04ii+2+9CA1FX3fV1zaHM6FSoGVHSAkPav50DsuxztF6QkXcrFqypzWOuRhl/5XWK6Zb5lDNGbgPyljUhIc6R5AJIfJx9dq1ZfJuZC1n9O8boM50DyUnUBGLj/bC0yGwK9Nka8kSrwCx/VLG/yH9xXvEgC2y49jBdshB72CRHqs2HKH5HGGloHzdHWj0K4wk0jGIvQzdUoDsolZA9lTyFIviVvl1d4TpyCmrxV9NUSAGNqzXrknGHX4Ggcj3mk+h1rbcDutk+Qa//nXUf/511HFbQ=="
    }

    register_info = {
        "is_vcd": "0",
        "safe_mobile_register_to_login": "true",
        "reg_cookie_opt": "true",
        "account_sdk_source": "app",
        "passport_support_flow": "real_name_check,choose_account,captcha,verify",
        "mix_mode": "1",
        "is_from_iesaccountsaas": "1",
        "user_api_need_combine": "1",
        "multi_login": "1",
        "code": end_code,
        "email": email_code
    }

    # 调用接口获取六神，并将六神更新至headers，更新业务接口params。注意，业务请求是POST时传data参数，GET不传。
    sixgoddata = core_sixgod(surl=url, params=params, devices={}, header=headers, log=False)
    sign_headers = sixgoddata["header"]
    sign_urls = sixgoddata["url"]
    for i in range(10):
        try:
            resp = requests.post(sign_urls, data=register_info, headers=sign_headers, proxies=proxies,timeout=30)
            return resp.json()
        except:
            logger.debug(f'第{i}次请求失败')
    else:
        raise Exception("网络异常")



# def
def register(email, email_url, proxies_url:str,index, proxies_mode):
    try:
        logger.debug(f'第{index}个账号开始注册，email:{email},email_url:{email_url}')
        time.sleep(0.1)
        if proxies_url:
            if proxies_mode == 1:
                proxies = get_proxies(proxies_url)
                logger.debug(f'使用代理:{proxies}')
            else:
                proxies = {
                    'http': proxies_url if proxies_url.startswith('htt') else 'http://'+proxies_url,
                    'https':proxies_url if proxies_url.startswith('htt') else 'http://'+proxies_url,
                }
        else:
            proxies = {
                # 'http': "http://t6ih1770740268:t6ih24@127.0.0.1:7890",
                # 'https':"http://t6ih1770740268:t6ih24@127.0.0.1:7890",
            }
            logger.debug(f'未使用代理')
        # 生成一个新的 UUID
        original_uuid = uuid.uuid4()

        # 将 UUID 转为字符串并去除其中的横杠
        uuid_without_dashes = str(original_uuid).replace('-', '')

        for i in range(3):
            try:
                device_info = device_register(proxies)
                if 'install_id' in device_info:
                    break
            except Exception as e:
                logger.error(f'第{i}次设备注册失败,e：{e}')
        else:
            logger.error(f'3次设备注册失败,email:{email},email_url:{email_url}')
            return email, email_url, False, '设备注册失败'

        logger.debug(f'设备注册成功，install_id:{device_info["install_id"]},device_id:{device_info["device_id"]}')
        time.sleep(0.1)

        res = send_code(email, device_info, uuid_without_dashes, proxies)
        if res['message'] == 'error':
            logger.error(f'发送验证码失败,e:{res}')
            return email, email_url, False, '发送验证码失败'

        logger.debug(f'发送验证码结果:{res}')
        time.sleep(0.2)
        code = get_email_code(email_url)
        logger.debug(f'获取到验证码:{code}')
        res = submit_code(email, code, device_info, uuid_without_dashes, proxies)
        logger.debug(f'提交验证码结果:{res}')
        is_success, msg = exc_res(res)
        logger.success(f'第{index}个账号注册结果：{email},{email_url},{is_success},{msg}')
        if is_success:
            try:
                with open(f'注册结果/res_{email}.json', 'w', encoding='utf-8') as f:
                    json.dump(res, f, ensure_ascii=False, indent=4)
                logger.debug(f'已保存至 注册结果/res_{email}.json')
            except:
                logger.error(f'保存时出错：e：{traceback.format_exc()}')
        else:
            logger.error(f'注册失败：{msg},不记录')
        return email,email_url,is_success,msg
    except Exception as e:
        logger.error(f'注册时出未知异常：e：{traceback.format_exc()}')
        return email,email_url,False,'未知异常：e'


def run():
    input_path = 'input'
    output_path = '注册结果'
    input_file, filename = get_filename_name(input_path)
    output_name = f'{output_path}/{filename.split(".")[0]}-{datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")}.xlsx'
    os.makedirs('注册结果', exist_ok=True)

    proxies_mode = int(input(f'请输入代理类型，1：提取式，2:隧道式,(默认提取)') or 1)
    proxies_url = input('请输入代理(不输入则不使用代理)：')
    max_worker = int(input('请输入最大线程数(不输入则默认10)：') or 10)

    register_ed = [i.replace('.json','').replace("res_","") for i in os.listdir('注册结果') if '.json' in i]

    lis = read_input_file(input_file,register_ed)

    logger.info(f'开始检测口子')
    success_count=0
    for index, i in enumerate(lis):
        email, email_url = i
        logger.debug(f'当前使用邮箱：{email}')
        smail, email_url, is_success,msg = register(email, email_url, proxies_url, index, proxies_mode)
        # is_success = True
        if not is_success:
            success_count = 0
            logger.debug(f'注册失败：{msg},十秒后继续')
            time.sleep(10)
        else:
            logger.debug(f'注册成功：{msg}，计数器加一，当前成功数：{success_count}')
            success_count += 1
            if success_count >= 3:
                logger.info(f'成功注册3个账号，判定口子开了')
                break
    else:
        return
    pool = ThreadPoolExecutor(max_workers=max_worker)
    futures = []
    for index, i in enumerate(lis):
        email, email_url = i
        futures.append(pool.submit(register, email, email_url, proxies_url, index,proxies_mode))
    res = []
    for index,future in enumerate(futures):
        smail,email_url,is_success,msg = future.result()
        res.append([smail,email_url,is_success,msg])
        if index % 10 == 5:
            try:
                data_df = pd.DataFrame(res, columns=['email', 'email_url', 'is_success', 'msg'])
                data_df.to_excel(output_name, index=False)
                logger.info(f'已保存至表格 {output_name}')
            except:
                logger.error(f'保存时出错,跳过：e：{traceback.format_exc()}')


if __name__ == '__main__':

    # card_password = read_card_password()
    # init_card_password(card_password,app_key='d66ljtrdqusuiftotbbg',app_secret='DHaDSznj2iUu0UDTq9kMCmSJb4vBvW4c')  # 印钞机
    email = 'wcwps9xb@88vipmail.com'
    email_url='http://mail.88vipmail.com/m.php?u=wcwps9xb@88vipmail.com&p=506728'
    proxies_url=None
    index=0
    proxies_mode=1
    register(email, email_url, proxies_url, index, proxies_mode)

    # try:
    #     run()
    # except:
    #     logger.error(traceback.format_exc())
    # input('完成')

    # send_phone_code('+601167490342',iid, did, chanel)
    """
    闪臣
https://sch.shanchendaili.com/getip/
17041096372
122397ab c
O25120315460438725850:pwd=T3O2xQRh&pid=-1&cid=-1&uid=ATNrTdbmtM&dip=0@flow.hailiangip.com:14224
    """