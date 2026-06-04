import threading
import traceback

from datetime import datetime
import requests
import secrets
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
import os
import time
import random
import pandas as pd

# 10m 旋转日志
logger.add('log/check_new_old.log',level='DEBUG',rotation='10Mb')

IS_RUN = True

def read_txt_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 读取文件的每一行并存储在列表中
            lines = file.readlines()
            # 去除每行末尾的换行符
            lines = [line.strip() for line in lines]
            return lines
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
        return []


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
    for index,filename in enumerate(filenames):
        print(f"{index}: {filename}")

    while True:
        try:
            index = int(input("请输入文件前的序号"))
        except:
            print('输入错误，请重新输入，请确保输入的是数字')
            continue

        # 检测数字是否合法，合法就结束输入，否则继续输入
        if index<0 or index>=len(filenames):
            print("数字不合法，超出可取范围，请重新输入")
        else:
            break

    # if len(filenames) != 1:
    #     raise FileExistsError(f"文件数量异常。只允许为1。目前为：{len(filenames)}")
    return os.path.join(filepath, filenames[index]), filenames[index]


def save_excel(lis,columns,output_name):
    global IS_RUN
    old_len = len(lis)
    while IS_RUN:
        new_len = len(lis)
        if new_len != old_len:
            try:
                df = pd.DataFrame(lis, columns=columns)
                df.to_excel(output_name, index=False)
                logger.info(f'已保存至 {output_name}')
            except Exception as e:
                logger.error(f'保存时出错：e：{traceback.format_exc()}')
                continue
            old_len = new_len

        time.sleep(1)

    # 到这里说明主线程已经完成了，但是为了以防万一，等待三秒后再保存一次
    time.sleep(3)
    df = pd.DataFrame(lis, columns=columns)
    df.to_excel(output_name, index=False)
    logger.info(f'已保存至 {output_name}')


def save_text(lis,columns,output_name):
    global IS_RUN
    old_len = len(lis)
    while IS_RUN:
        new_len = len(lis)
        if new_len != old_len:
            try:
                with open(output_name, 'w', encoding='utf-8') as f:
                    f.write("----".join([str(j) for j in columns])+"\n")
                    f.write('\n'.join(["----".join([str(j) for j in i]) for i in lis]))
                logger.info(f'已保存至 {output_name}')
            except Exception as e:
                logger.error(f'保存时出错：e：{traceback.format_exc()}')
                continue
            old_len = new_len
        time.sleep(1)
    # 到这里说明主线程已经完成了，但是为了以防万一，等待三秒后再保存一次
    time.sleep(3)
    with open(output_name, 'w', encoding='utf-8') as f:
        f.write("----".join([str(j) for j in columns]) + "\n")
        f.write('\n'.join(["----".join([str(j) for j in i]) for i in lis]))
    logger.info(f'已保存至 {output_name}')


def api_get_proxies(api_url):
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


def get_proxies(proxies_url,proxies_mode):
    """
    :param proxies_url: 代理IP接口地址,为空则不使用代理
    :param proxies_mode: 在proxies_url不为空的情况下 判断代理模式，1:提取式，2:隧道式
    :return: 代理IP字典
    """
    if proxies_url:
        if proxies_mode == 1:
            proxies = api_get_proxies(proxies_url)
            logger.debug(f'使用代理:{proxies}')
        else:
            proxies = {
                'http': proxies_url if proxies_url.startswith('htt') else 'http://' + proxies_url,
                'https': proxies_url if proxies_url.startswith('htt') else 'http://' + proxies_url,
            }
    else:
        proxies = {
            # 'http': "http://t6ih1770740268:t6ih24@127.0.0.1:7890",
            # 'https':"http://t6ih1770740268:t6ih24@127.0.0.1:7890",
        }
        logger.debug(f'未使用代理')
    return proxies


def xor(s):
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    result = ''
    for b in arr:
        result += chars[(b & 255) >> 4]
        result += chars[(b & 255) & 15]
    return result

def generate_random_hex(length: int = 40) -> str:
    """
    生成指定长度的十六进制随机字符串
    :param length: 字符串长度（字符数），默认40
    :return: 十六进制随机字符串
    """
    return secrets.token_hex(int(length/2))


def api_send_code(phone,proxies):
    headers = {
        "accept": "application/json, text/javascript",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "content-length": "0",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://open.douyin.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://open.douyin.com/platform/oauth/mobile/auth?response_type=code&redirect_uri=https%3A%2F%2Fapi.snssdk.com%2Foauth%2Fauthorize%2Fcallback%2F&client_key=aw0spz4aixhst4rt&state=dy_state&from=opensdk&scope=user_info&optionalScope=mobile%2C1&signature=aea615ab910015038f73c47e45d21466&app_identity=01a90b78fc7d7a6ca703e46c87839575&device_platform=android&live_enter_from=&enter_from=auth_login&is_wifi=1&comment_id=&is_other_account_auth=2",
        "sec-ch-ua": "\"Chromium\";v=\"148\", \"Microsoft Edge\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"iOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1 Edg/148.0.0.0",
        "x-tt-passport-csrf-token": "6b5fa83dec24aa5298547ad2c79a457d",
        "x-tt-passport-trace-id": "1c4f7c31"
    }
    cookies = {
        # "d_ticket_dy_open": "21c5494248e56af3812387e5cf78731b110bd",
        # "enter_pc_once": "1",
        # "UIFID_TEMP": "48df845ec17e24d3e136cf9cb5f33ae5ff0d6a60613b8e70d731bae9b37d4b9361f8e1b0f86d68a19c89af5beada794968259f2c27675ce95cac9163b82e18ace105c2ca2eecda9fd0052137606482cb",
        # "bd_ticket_guard_client_web_domain": "2",
        # "UIFID": "48df845ec17e24d3e136cf9cb5f33ae5ff0d6a60613b8e70d731bae9b37d4b93d9dab758e74e1f7fc24776453b8614e7a294831bd66b40ec37d4cf6997ca0ca336356052575f8f767b63e7cced95a5dfd1dd446330931bee5163af4a0e3423dc830e13e21624dbab1714cb53f3a02ea45c93f8d0a394d4e04bc91e9a39c1bfe22b2786c49e6b0ea9fdef069e55814711b3ba9b535e90b811a0db6e76e902149d",
        # "_bd_ticket_crypt_doamin": "2",
        # "__security_server_data_status": "1",
        # "my_rd": "2",
        # "passport_mfa_token": "Cjd9Dhr5WMj%2FH3QFbtnltw%2FouUaAYg9frcQFt2YqE%2BCu5H5uwGulcN0yzlJq5IES7m5NZKQqbNSjGkoKPAAAAAAAAAAAAABQRM8mtWlPQfXhGN5f33Kq2sRgRy68nACOqmuEHFkF1hfq7B3GlaU6IQvDjALkDWEeLRCCgY4OGPax0WwgAiIBAy4U6ic%3D",
        # "d_ticket": "a103f5a98ca9d858b1f1aaa7acb33b5ffabf1",
        # "n_mh": "gPIQKbVX2NF5IpVobZYd0v-p2yWe_noXDcpMdV3Ta2w",
        # "is_staff_user": "false",
        # "has_biz_token": "false",
        # "live_use_vvc": "%22false%22",
        # "SearchResultListTypeChangedManually": "%221%22",
        # "SEARCH_RESULT_LIST_TYPE": "%22multi%22",
        # "__live_version__": "%221.1.5.1831%22",
        # "passport_assist_user": "CkF4AcwSZ0vbDh94GKx26mGZcA0pDBLzAfB_TVk0JpiJGL5rXD8bKFlSTxf6dxJNbr55Bmv8e0cX5iBZ2dXSIurx9xpKCjwAAAAAAAAAAAAAUGhBhhb_XWG2r9NLiNUsyD6n3UiRrBJYtO5XmGn5Gwivu2qJBnQAS-Miildx8jN1AY4QmpiRDhiJr9ZUIAEiAQMRGilA",
        # "sid_guard": "cdccab94a8f552a2eebbbfc1e6df244b%7C1778523099%7C5183999%7CFri%2C+10-Jul-2026+18%3A11%3A38+GMT",
        # "uid_tt": "68f47f795f819d83baaf222d06685bce",
        # "uid_tt_ss": "68f47f795f819d83baaf222d06685bce",
        # "sid_tt": "cdccab94a8f552a2eebbbfc1e6df244b",
        # "sessionid": "cdccab94a8f552a2eebbbfc1e6df244b",
        # "sessionid_ss": "cdccab94a8f552a2eebbbfc1e6df244b",
        # "session_tlb_tag": "sttt%7C9%7CzcyrlKj1UqLuu7_B5t8kS__________7vIfXy4GfiF-MemttTOr_xBK0q-5mQxY-QKB-NMsKz0M%3D",
        # "sid_ucp_v1": "1.0.0-KGViODU3NjI4N2VjOWMyOWI1YjAzOTI3NDAyN2MxYmYxNzY4MDk1ZDQKIQiws7DTxKzcBRDbt4jQBhjvMSAMMPjOksIGOAdA9AdIBBoCbHEiIGNkY2NhYjk0YThmNTUyYTJlZWJiYmZjMWU2ZGYyNDRi",
        # "ssid_ucp_v1": "1.0.0-KGViODU3NjI4N2VjOWMyOWI1YjAzOTI3NDAyN2MxYmYxNzY4MDk1ZDQKIQiws7DTxKzcBRDbt4jQBhjvMSAMMPjOksIGOAdA9AdIBBoCbHEiIGNkY2NhYjk0YThmNTUyYTJlZWJiYmZjMWU2ZGYyNDRi",
        # "_bd_ticket_crypt_cookie": "264b3adf8c11e49a77ffbf07e617b834",
        # "login_time": "1778523098918",
        # "passport_csrf_token": "6b5fa83dec24aa5298547ad2c79a457d",
        # "passport_csrf_token_default": "6b5fa83dec24aa5298547ad2c79a457d",
        # "SelfTabRedDotControl": "%5B%7B%22id%22%3A%227610415716746922024%22%2C%22u%22%3A50%2C%22c%22%3A0%7D%5D",
        # "PhoneResumeUidCacheV1": "%7B%2261196082606%22%3A%7B%22time%22%3A1775063114679%2C%22noClick%22%3A1%7D%2C%223220900303083952%22%3A%7B%22time%22%3A1778847000578%2C%22noClick%22%3A4%7D%7D",
        # "LivePausePop": "%22%257B%2522todayCount%2522%253A1%252C%2522closeNum%2522%253A0%252C%2522todayShowRoom%2522%253A%25227640083418541198080%2522%252C%2522lastTimer%2522%253A1778847305378%257D%22",
        # "live_debug_info": "%7B%22roomId%22%3A%227640083418541198080%22%2C%22resolution%22%3A%7B%22width%22%3A960%2C%22height%22%3A720%7D%2C%22fps%22%3A1%2C%22audioDataRate%22%3A0%2C%22speed%22%3A%7B%22totalByteSize%22%3A83748139%2C%22currentSpeed%22%3A252%2C%22avgSpeed%22%3A2016000%2C%22recentSpeed%22%3A2032000%7D%2C%22droppedFrames%22%3A169%2C%22totalFrames%22%3A9944%2C%22videoBuffer%22%3A%5B%5B322.066%2C336.806312%5D%5D%2C%22src%22%3A%22https%3A%2F%2Fpull-flv-q1.douyincdn.com%2Fthird%2Fstream-695837055999542077_sd.flv%3Fkeeptime%3D00093a80%26wsSecret%3D7e2af1953ee23d812858abac71902c40%26wsTime%3D6a070c8c%26arch_hrchy%3Dh1%26exp_hrchy%3Dh1%26neq%3D1%26major_anchor_level%3Dcommon%26unique_id%3Dstream-695837055999542077_829_flv_sd%26t_id%3D037-202605152007398C3A3A56EFDA9A6E9EB8-e0VHk1%26_session_id%3D037-202605152007398C3A3A56EFDA9A6E9EB8-e0VHk1.1778846876692.60619%26rsi%3D1%26abr_pts%3D-800%22%2C%22linkmicInfo%22%3A%7B%22uiLayout%22%3A0%2C%22playModes%22%3A%5B%5D%2C%22allDevices%22%3A%22%E8%BF%9E%E7%BA%BF%E8%AE%BE%E5%A4%87%EF%BC%9A%E7%94%B3%E8%AF%B7%E8%BF%9E%E7%BA%BF%E5%90%8E%E6%89%8D%E8%8E%B7%E5%8F%96%22%2C%22audioInputs%22%3A%5B%5D%2C%22videoInputs%22%3A%5B%5D%7D%2C%22href%22%3A%22https%3A%2F%2Flive.douyin.com%2F92684025686%3Fanchor_id%3D101358335464%26category_name%3Dall%26is_vs%3D0%26page_type%3Dmain_category_page%26vs_ep_group_id%3D%26vs_episode_id%3D%26vs_episode_stage%3D%26vs_season_id%3D%22%7D",
        # "__druidClientInfo": "JTdCJTIyY2xpZW50V2lkdGglMjIlM0E1NDglMkMlMjJjbGllbnRIZWlnaHQlMjIlM0E4ODElMkMlMjJ3aWR0aCUyMiUzQTU0OCUyQyUyMmhlaWdodCUyMiUzQTg4MSUyQyUyMmRldmljZVBpeGVsUmF0aW8lMjIlM0ExLjUlMkMlMjJ1c2VyQWdlbnQlMjIlM0ElMjJNb3ppbGxhJTJGNS4wJTIwKFdpbmRvd3MlMjBOVCUyMDEwLjAlM0IlMjBXaW42NCUzQiUyMHg2NCklMjBBcHBsZVdlYktpdCUyRjUzNy4zNiUyMChLSFRNTCUyQyUyMGxpa2UlMjBHZWNrbyklMjBDaHJvbWUlMkYxNDguMC4wLjAlMjBTYWZhcmklMkY1MzcuMzYlMjBFZGclMkYxNDguMC4wLjAlMjIlN0Q=",
        # "stream_recommend_feed_params": "%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A2560%2C%5C%22screen_height%5C%22%3A1440%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A12%2C%5C%22device_memory%5C%22%3A32%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22",
        # "strategyABtestKey": "%221780310918.817%22",
        # "bd_ticket_guard_client_data": "eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCUFFLb2xVQnI5Rk9hQzFGMG9vYWFwYnFHWlVRMGRsejgyckp3cTBYSTgyUmxpVzBKSXkwYW5qTlpOVFF6Mzk2WGtRKzZXTFVGeEZwUnhyY1ZxQlVxWTg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D",
        # "is_dash_user": "1",
        # "home_can_add_dy_2_desktop": "%221%22",
        # "publish_badge_show_info": "%220%2C0%2C0%2C1780310920410%22",
        # "odin_tt": "d7ecc5f1a6acea816699f79fc226cbcd21cadb98ff2ff6d250729e29e8d0c780d68a41e05479c9bce4f665bfaab91b208fa3d83ebf8e8087135dbbd9ce275b8aa443fcbe989e18fc1c6287a6e90e9caf",
        # "volume_info": "%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.6%7D",
        # "download_guide": "%222%2F20260601%2F0%22",
        # "__security_mc_1_s_sdk_crypt_sdk": "bf968403-4849-a771",
        # "__security_mc_1_s_sdk_cert_key": "3845b577-4c59-a18c",
        # "__security_mc_1_s_sdk_sign_data_key_web_protect": "75d27a51-42df-bc63",
        # "playRecommendGuideTagCount": "1",
        # "totalRecommendGuideTagCount": "1",
        # "IsDouyinActive": "false",
        # "bd_ticket_guard_client_data_v2": "eyJyZWVfcHVibGljX2tleSI6IkJQUUtvbFVCcjlGT2FDMUYwb29hYXBicUdaVVEwZGx6ODJySndxMFhJODJSbGlXMEpJeTBhbmpOWk5UUXozOTZYa1ErNldMVUZ4RnBSeHJjVnFCVXFZOD0iLCJ0c19zaWduIjoidHMuMi41YmU5NjNmZjkwOTUxZDJkYTQ3ZTg2ZDZjMGU3NmYxNGI3YTFlZTgxNWFiOWQ2ZGZiMWRkNWI1MzE1ZmFjMGY1YzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJUYytsWUp3OEZHMDR5aGsvTmJvUWZsNGhZZEp4RmkwYzVsR1Q0Qm9UWFA0PSIsInNlY190cyI6IiN2ODcxVzVNbzl2blhZTlpSQktxMVo1MytPNmVSTDN2VWFTeGFkYmtTYVhSK2NzdEZlOGNLYkZtVnlQdTYifQ%3D%3D",
        # "s_v_web_id": "verify_mpvhmh2z_dadc8afe_c6de_2fe6_bf81_91efdd6cdfb9",
        # "__tea_cache_tokens_1243": "{%22web_id%22:%227646481438543808051%22%2C%22user_unique_id%22:%227646481438543808051%22%2C%22timestamp%22:1780335284223%2C%22_type_%22:%22default%22}",
        # "ttwid": "1%7CTBrJtyaNli7yBCDY2lBQc4Skf3yNkpX077_vLvRWTxs%7C1780335284%7Cd81553a566e795dfc1fee183d98def915a0fe1a997e54718ffcf824c6bbeaff6",
        # "biz_trace_id": "1c4f7c31"
    }
    url = "https://open.douyin.com/oauth/send_code/"
    params = {
        "passport_jssdk_version": "2.0.8",
        "passport_jssdk_type": "pro",
        "aid": "1128",
        "language": "zh",
        "mix_mode": "1",
        "mobile": xor(phone),
        "type": "3732",
        "account_sdk_source": "web",
        "account_sdk_source_info": generate_random_hex(),
        "passport_ztsdk": "3.0.28",
        "passport_verify": "1.0.17",
        "request_host": "https%3A%2F%2Fopen.douyin.com",
        "biz_trace_id": "1c4f7c31",
        "is_vcd": "1",
        "sign": generate_random_hex(60),
        # "qs": "6466666a706b715a76616e5a766a70776660296466666a706b715a76616e5a766a707766605a6c6b636a29646c6129676c7f5a71776466605a6c61296c765a7366612969646b627064626029686c7d5a686a616029686a676c69602975647676756a77715a6f7676616e5a717c
    }

    # proxies = {
    #     # 'http': 'http://127.0.0.1:7890',
    #     # 'https': 'http://127.0.0.1:7890',
    #     'http': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
    #     'https': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
    # }
    for i in range(3):
        try:
            response = requests.post(url, headers=headers, cookies=cookies, params=params, proxies=proxies)
            return response.json()
        except Exception as e:
            logger.error(f"请求失败，第{i}次，错误信息：{e}")
    raise Exception("请求失败，3次均失败")

def exc_result(data):

    error_code = data.get("data",{}).get("error_code")
    description = data.get("data",{}).get("description")
    # 放回
    result = None   # 标记是新号\老号\异常号
    remark = ""
    if error_code in [1003]:
        result = "异常号"
    elif error_code in [1108]:  # 出验证码了,是老号
        result = "老号"
    elif error_code in [2036]:
        result = "新号"
    elif error_code in [1105]:  # 出滑块了,是新号
        result = "新号"
    else:
        result = "未知"
        remark = data
    return  result,description,remark


def check_new_old(area,phone,proxies_mode, proxies_url,output_lis = None):

    for i in range(3):
        try:
            proxies = get_proxies(proxies_url,proxies_mode)
            logger.info(f"开始检查手机号{area}{phone}，代理：{proxies}")
            result = api_send_code(f"{area}{phone}",proxies)
            # print(result)
            result,description,remark = exc_result(result)

            if output_lis is not None:
                output_lis.append((phone, result,description,remark))
            return phone, result,description,remark
        except Exception as e:
            logger.error(f"检查手机号{area}{phone}，第{i}次，错误信息：{e}")
            pass
    if output_lis is not None:
        output_lis.append((phone, "查询异常", "", str(e)))
    return phone, "查询异常", "", str(e)



def run():
    global IS_RUN
    input_path = "input"
    if not input_path:
        os.makedirs(input_path)

    os.makedirs("查新老结果",exist_ok=True)

    area = input(f'请输入区号')
    input_file, filename = get_filename_name(input_path)
    try:
        proxies_mode = input("请选择代理模式：1. 提取式代理 2. 隧道代理")
        if int(proxies_mode) not in [1,2]:
            input("输入错误")
            exit()
    except:
        input("输入错误")
        exit()
    proxies_url = input("请输入代理链接：")
    max_workers = int(input("请输入线程数："))
    output_name = f'查新老结果/{filename.split(".")[0]}-{datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")}.xlsx'

    phone_list = read_txt_file(input_file)
    pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []
    output_lis = []
    columns = ['手机号','结果','描述','备注']
    save_excel_thread = threading.Thread(target=save_excel, args=(output_lis, columns, output_name))
    save_excel_thread.start()
    save_text_thread = threading.Thread(target=save_text, args=(output_lis, columns, output_name.replace('.xlsx', '.txt')))
    save_text_thread.start()

    for phone in phone_list:
        futures.append(pool.submit(check_new_old, area, phone, proxies_mode, proxies_url,output_lis))

    long = len(phone_list)
    for index, future in enumerate(futures):
        phone, result,description,remark = future.result()
        logger.success(f"{index}/{long},手机号{phone}，结果：{result}，描述：{description}，备注：{remark}")
    IS_RUN = False
    save_excel_thread.join()
    save_text_thread.join()



if __name__ == '__main__':
    # try:
    #     run()
    # except Exception as e:
    #     logger.error(f"运行异常，错误信息：{traceback.format_exc()}")
    #     exit()
    #
    # input(f"请输入任意内容结束")
    # print(generate_random_hex(32))
    phone = '19429996012'
    proxies = {
        # 'http': 'http://127.0.0.1:7890',
        # 'https': 'http://127.0.0.1:7890',
        'http': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
        'https': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
    }
    proxies_url = "http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030"
    print(check_new_old('+',phone,2, proxies_url,[]))
