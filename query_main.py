import json
import traceback
from collections import deque
import random
from loguru import logger

from flurl3.core import core_sixgod
from module.error.error import RetryException
import requests,time,hashlib
from module.six_god2.core import sign_android
from flurl3.device_register import device_register
from module.six_god1.captcha import ByteDanceCaptchaAndroid


logger.add("log/log_new.log", rotation="100 MB", retention="1 week", encoding="utf-8",
           format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | Thread: {thread} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           )

def api_slide_test(verify_center_decision_conf, iid, did, proxies,retry = 0):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    json_data = {
        'device_id': did,
        'iid': iid,
        'proxy_ip': proxies['https'].replace("http://","" ) if proxies else "",
        # 'proxy_ip': "",
        'verify_str': verify_center_decision_conf
    }
    # print(json_data)

    response = requests.post('http://8.148.67.111:19000/api/god/slider/android', headers=headers, json=json_data)

    if response.json()['data'] == '验证失败':
        if retry < 3:
            return api_slide_test(verify_center_decision_conf, iid, did, proxies,retry+1)
        else:
            raise RetryException(f"滑块异常，重试3次失败,{response.json()}")

    return response.json()

def get_proxies(api_url):
    # api_url =
    # 获取API接口返回的代理IP
    proxy_ip = requests.get(api_url).text
    if not proxy_ip:
        raise Exception("获取代理IP失败")
    # 用户名密码认证(私密代理/独享代理)
    proxies = {
        'http': f'http://{proxy_ip}',
        'https': f'http://{proxy_ip}',
    }
    return proxies


def get_data(area_phone=None,username=None,password=None):
    """根据手机号生成请求数据。"""
    if area_phone:
        data = {
            "is_vcd": "1",
            "reg_cookie_opt": "true",
            "ttnet_sdk_version": "4.2.278.8-douyin",
            "auth_sdk_version": "4.7.5",
            "enter_from": "recover",
            "hide_user_name_v3": "1",
            "mix_mode": "1",
            "area_code": "86",
            "account_app_language": "zh",
            "mobile": xor_encrypt(area_phone),
            # "mobile": "2e3d33253432323d3d3d3d3c3c3c3d",
            "language": "zh",
            "query_type": "0",
            "multi_login": "1",
            "account_api_standard": "emo_douyin_account_recover",
            "scene": "find_account",
            "sec_sdk_version": "67764480",
            "account_sdk_source": "app",
            "passport_support_flow": "choose_account,captcha,real_name_check,verify",
            "verify_sdk_version": "4.1.3.cn"
        }
        return data

    else:
        return {
            'enter_from': 'recover',
            'find_account_ab_group': 'v0',
            'hide_user_name_v3': '1',
            'is_vcd': '1',
            'mix_mode': '1',
            'identity_name': str(xor_encrypt(username)),
            'identity_no': str(xor_encrypt(password)),
            'query_type': '3',
            'scene': 'find_account',
        }


def xor_encrypt(s):
    """对手机号进行异或加密。"""
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    result = ''.join([chars[(b & 255) >> 4] + chars[(b & 255) & 15] for b in arr])
    return result


def py_account_password(area: str, val: str):
    """
    账号密码加密
    """

    map_ = {'+': '2e', '8': '3d', '6': '33', ' ': '25', '1': '34', '2': '37', '3': '36', '4': '31', '5': '30', '7': '32', '9': '3c', '0': '35'}

    return "".join([map_[i] for i in area+" "+val])


def handle_result(proxies, result, area, phone, result_dict: dict):
    """处理返回的结果并保存到文件。"""

    # 这里提前判定一下是否实名
    has_face_verify = False
    # for i in range(10):
    #     try:
    #         # print(result)
    #         if "account" not in result['data']:
    #             raise Exception("查询异常")
    #         # has_face_verify = is_real_name(result["data"]["account"][0]["not_login_ticket"], proxies)
    #         has_face_verify = False
    #         break
    #     except Exception as e:
    #         logger.error(f"实名查询失败，重试中{i}/10,错误信息：{e}")
    #         has_face_verify = str(e)
    #         time.sleep(1)

    if not result:
        result_dict.update({phone: {
            "area": area,
            "phone": phone,
            "status": '请求失败',
            "is_real_name":has_face_verify
        }})
    elif '账号已被锁定' in str(result):
        result_dict.update({phone: {
            "area": area,
            "phone": phone,
            "user_name": result["data"]["account"][0]["nickname"],
            "year": result["data"]["account"][0]["register_time"],
            "status": '锁定账号',
            "is_real_name": has_face_verify
        }})
    elif "用户不存在" in str(result):
        result_dict.update({phone: {
            "area": area,
            "phone": phone,
            "status": '未注册号',
            "is_real_name": has_face_verify
        }})

    else:
        if 'account' in result['data'] and result['data']['account']:
            account = result['data']['account'][0]
            account_status_code = account.get('account_status_code')
            register_time = account.get('register_time', "无")
            account_group_id = account.get('account_group_id', "无")
            nickname = account.get('nickname', "无")
            if account_group_id == 18:
                status = "火山账号"
            elif account_status_code in [2132, 2089]:
                status = "封禁号"
            else:
                status = "正常老号"
            result_dict.update({phone: {
                "area": area,
                "phone": phone,
                "user_name": nickname,
                "year": register_time,
                "status": status,
                "is_real_name": has_face_verify
            }})
        else:
            result_dict.update({phone: {
                "area": area,
                "phone": phone,
                "status": '无信息',
                "is_real_name": has_face_verify
            }})


def is_real_name(ticket, proxies):
    # print(ticket)
    headers = {
        "Host": "api5-normal-lf.amemv.com",
        "x-vc-bdturing-sdk-version": "3.7.5",
    }
    headers = {
        "Host": "api5-normal-lf.amemv.com",
        "sdk-version": "2",
        "x-vc-bdturing-sdk-version": "3.7.5",
        "user-agent": "com.ss.android.ugc.aweme/330801 (Linux; U; Android 13; zh_CN; M2011K2C; Build/TKQ1.220829.002;tt-ok/3.12.13.18)",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "content-length": "178"
    }
    cookies = {

    }
    url = "https://api5-normal-lf.amemv.com/passport/safe/query_decision/"
    params = {
        "app_id": "1128",
        "account_flow": "verify",
        "version_code": "34.2.0",
        'iid': random.randint(1000000000000000, 9999999999999999),
        'device_id': random.randint(1000000000000000, 9999999999999999),
        "aid": "1128",
        "resolution": "1290*2796",
        "not_login_ticket": ticket,
        "verify_scene": "find_account",
    }
    for i in range(5):
        try:
            response = requests.get(url, headers=headers, cookies=cookies, params=params,proxies=proxies,timeout=30,verify=False)
            # sign_headers, sign_urls = sign_android(url=url, params=params, header=headers, cell=True,
            #                                        log=False)
            #
            # response = requests.get(
            #     url=sign_urls,
            #     headers=sign_headers,
            #     # data=data,
            #     proxies=proxies,
            #     timeout=25
            # )
            break
        except Exception as e:
            logger.error(f"请求失败 重试{i}/10")
            time.sleep(1)
    else:
        raise Exception("请求异常")
    print(response.text)
    # print(response.status_code)
    if response.status_code == 200:
        jsondata = response.json()
        has_face_verify = False
        try:
            if jsondata.get("message") =='error':
                raise Exception("查询风控")

            verify_ways = jsondata.get("data", {}).get("verify_ways", {})
            verify_ways_list = [i.get("verify_way") for i in verify_ways]
            if "face_verify" in verify_ways_list:
                has_face_verify = True
            elif "caijing_auth_verify" in verify_ways_list:
                has_face_verify = "钱包认证"
        except AttributeError:  # 处理verify_ways不是可迭代对象的情况
            pass
        # logger.debug(f"实名状态：{has_face_verify}")
        return has_face_verify

def query_phone(device, area_phone=None,card_name=None, card=None, proxies=None):
    """

    :param device: 设备信息
    :param area_phone: 区号+手机号：+86 13123456789
    :param card_name:   姓名  （当身份证模式时使用）
    :param card:        身份证号    （当身份证模式时使用）
    :param proxies:     代理
    :return:
    """

    url = "https://aggr5-normal-s12.amemv.com/passport/safe/query_account/"
    params = {
        "passport-sdk-version": "60571",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "klink_egdi": "AALTZSVMzS6nbmKZNTlCACoSZbfufCiZJBMe0WnRg5iBpQ7emFB54Oc",
        "iid": device['install_id'],
        "device_id": device['device_id'],
        "ac": "wifi",
        "channel": device.get('channel') or "xiaomi_1128_64",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "380900",
        "version_name": "38.9.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "AOSP on taimen",
        "device_brand": "Android",
        "language": "zh",
        "os_api": "30",
        "os_version": "11",
        "manifest_version_code": "380901",
        "resolution": "1440*2712",
        "dpi": "560",
        "update_version_code": "38909900",
        "_rticket": "1780240253909",
        "package": "com.ss.android.ugc.aweme",
        "first_launch_timestamp": "1779907858",
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
        "ts": "1780240290",
        "cdid": "2ba297c6-2411-48bb-9fc3-3c9d04edb4c8",
        "cronet_version": "5e677c20_2026-03-23",
        "ttnet_version": "4.2.278.4-douyin",
        "use_store_region_cookie": "1"
    }
    data = get_data(area_phone=area_phone,username=card_name,password=card)
    headers = {
        'User-Agent': "com.ss.android.ugc.aweme/380901 (Linux; U; Android 11; zh_CN_#Hans; AOSP on taimen; Build/RP1A.200720.009; Cronet/TTNetVersion:e3d16265 2026-05-11 QuicVersion:afeca321 2026-04-27)",
        # 'Content-Type': "application/octet-stream",
        'x-tt-request-tag': "bdr-cnt=1;s=-1;p=0",
        'x-security-argus': "BridgeNetworkRequest/unknown aid/1128/huoshan_fans_page_douyin/Android/38.9.0/h5/213 https://api.amemv.com/ucenter_web/app/aweme/account_rebind_auth_verify",
        'contenttype': "application/x-www-form-urlencoded",
        # 'x-tt-passport-csrf-token': "01ff0f8438de198ae2c202b60e1ffc91",
        # 'x-tt-dt': "AAA6YGPFLZAOFVKA347OABDOAMX2LZLMVYWWSAE64DISCTXSXUOLVOFQOIYO3OQOOIFA72TO3UCLPO6DRSDYXQODE4XM3ILYZMRDY5GALQWJQ2E7FVNI6WVZJDVHBG6SK3SLYL7DOH6ERBSNUGY44OI",
        # 'activity_now_client': "1780240293418",
        # 'x-tt-device-dtrait': "a0_NdDdbaqXc/iwH4AV+WtO+PvaJh7LpAK3B66QwdrDEqianSsLdXCUOfcaPGUxUd/QS9NlbBYgaI0HhAEAzlUAmOwrFqAlDsPkdeZ+taXdtH+z/zQFEDq70TTTZWJqrbPebplItMHJsLfCZKwnrCKgIALEE/9ynI9KtAw/xMHXdco5oXpHZdvk9BUYMEC0iN/ym3uyBzDdpSPbivAc1V41XmT9TetcpMTORxl6cltpfWbTIB+ODe9kDZuY/m429+nwpsyoVrFmzEOxuL6rO4wwYaJOitjcwUK1qjyQ+H0P6j4s9x/Hm0aYGjtmbvIo1+oOpOK2+lfhSZ8mtr8oz1/+DA==",
        'bd-ticket-guard-display-os-version': "RP1A 200720.009 release-keys",
        'bd-ticket-guard-ree-public-key': "BESw/v0g6c3E7LP6vrPxKgmUjsOOTUhV9BdDexqSwUDFXsaowzboMa83bO11UkauzZrThxQEi72fHtGfvHmXm5M=",
        'bd-ticket-guard-version': "3",
        # 'x-tt-passport-verify-portrait-outer': "829ce87d-b795-49e2-9dcf-dc95cbe4ec87.find_account",
        # 'passport-sdk-settings': "x-tt-token,sec_user_id,device_transfer_s_0,device_transfer_ab_0",
        # 'passport-sdk-sign': "x-tt-token,sec_user_id",
        'bd-ticket-guard-tee-status': "1",
        'sdk-version': "2",
        'bd-ticket-guard-iteration-version': "2",
        # 'bd-ticket-guard-client-cert': "cHViLkJKcmFaNzd0MGc3d1hOSnV4RzNVaVR0d2s2YVVYZktHb2xiR3Q4Y1VrK3gvYUxtSHkrOVlEcGMySzJaeDMwYU51K0loa3dRSGxJT21vd1ZxeE9PLzJ2VT0=",
        # 'bd-ticket-guard-static-sign': "MEUCIQC0tLRiPkA1ge0V7Mwnyxn2uG7U506ysAh/DTHpo20FuAIgfDVSS0kf1fWiqABgZJHrzDQeDuwX/+2Y4mpsdqLsr3c=",
        # 'bd-ticket-guard-server-cert-sn': "533240336124694022040808462028007165443034493949",
        # 'x-tt-passport-trace-id': "find_account_20e1cf0de00747f5a9626a4528478651",
        # 'bd-ticket-guard-sec-ts': "#f7xqQJXp6YM3USgf3ZGQ6Ou8OnTTVTOnkhYmrvi35NE2GY6/uLe1qI85n6pg",
        'passport-sdk-version': "60571",
        'x-ss-req-ticket': "1780240253926",
        'x-vc-bdturing-sdk-version': "4.1.3.cn",
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
        'x-ss-stub': "1FB719D47D4070285F442B93B5FE4561",
        # 'x-bd-content-encoding': "zstd",
        'x-tt-bdturing-retry': "1",
        'x-tt-ttnet-origin-host': "api5-normal-lq.amemv.com",
        'x-ss-dp': "1128",
        # 'x-tt-trace-id': "01-7e96f65b0d9b167d1902e83098ba0468-7e96f65b0d9b167d-00",
        # 'x-perseus': "LpLLLlNWN65jjiF/nzZvl9xvpt6shTLg54vRKUcHYvin6LwKnaDHWhybts/lRdYp1ZxxerWygBqXlqxheY8hgIjLy9v2RhWqQzxtwcwfhTqIRR8z3xdH2eXzDlPhURySbx53cL0mQEZvbypAufYh2SQBt3m0EJ8QlUw+cdIP5C11G4kFt4/PXwNzHMSgaAoIJ9rgeOw6QP6Lb6/x7br7oXQqJARxCDTYxWSJZ8nDirddSQRAWxvqsTcSqeOeF+Yy7evG1aPAsai8Ly5e0WLT6hj2YzyM+2iZDAzGYS4O7EulxffNJYja4y5uEDdvGzFWqTz+KhCTvnwgzF7kCBmS3n+PshRovmDRxVhDC3fvsGu3SBL6ai5O7u5XpbnjklLeRKbU4BbVNyI16dXd2Q7zMwpKrW/50FJOHARI3wh8dX6xzYtKLKcwn4JQDaAmbo9JJdrgvFoTSeQlmQVd7GwG9oEJQbedOGttcu9jPTU9+xKEsGRtmR1YZ/Iys2yNjZ71zU+gNx7mGc84UiAYv3NkDlto5nngCqJeNSWricbG/jaHqUmdmPCHIKYF8j8VkfX0sWuIVdTwEqIY+/+Wzx3cTmJNTUU2tJcb8NrFm8dPoEXilOOHfgqWqIQ6Zj7AkVKZ0E+2uyMPQkCHlHOS6F7f4AgxobDFoe7gAA9mTFmuSY9zYOkT2sgECuiP1CrNg3BYKT05PzCIorGcPMfv33ChQBF/YZFRjpZ/t8/NycHhnHj9e4IDEOMZ49wh52ed8NSgM4VCLRkLImgv7OqJQkd0iKb1/jqE9HrQoT4t/sH6/07QvYWSPVbUwomZpQws7MOQVh/9klWpmoR5D3kZSkTo7NPGfYwye7MeX0b5VaMk4nQjPGEQeuSCIQgkAsy7+0l/gxD9PeludD==",
        # 'x-medusa': "ck8cah7VN0A31LP79IUeALd5uJRwYwANJouELpi/19t7CJT+yDVfNrV1AUIZmCENNrlDloqyPnqcraad1T9zOeB03P8O1BACpOxUmpByPu7Wv625zhDicBs0vzDD5caLN/M5885DEvQ1drYMAS1HdBkdKg6LY+eZTJwJAfAtzixvgOAnt87Ulcud6oq2Lo8D3y81lPDGSCxFaXlQORO+gjyrOc+aTGYBgbRAGAFrx05rS4bpwFFEFxX8QxB2/8PakxvKpetdRxj7Qlg/mTMfzPW2MFYJbn3chZWq2up1V5kUtwff9SLlj007rry4y6cRuQZ83acTivpR+dajPy5izWh1A/h+Mf/4pzH/+KfrIg==",
        # 'x-argus': "dU8cag==",
        # 'x-gorgon': "8404c0c200004d604c291c751ef5e77fd68e594e2341c7e9df6b",
        # 'x-helios': "nI0BKZn4qH8iEd0Dim4CCA3qENyUJwr7JzVuAdjHlMZDLPue",
        # 'x-ladon': "et2C+w==",
        # 'x-khronos': "1780240245",
        'Cookie': f"store-region=cn-fj; store-region-src=did; install_id={device['install_id']}; ttreq=1$9380e7ed80dc051525b7e3479b6c1959535ad289; passport_csrf_token=01ff0f8438de198ae2c202b60e1ffc91; passport_csrf_token_default=01ff0f8438de198ae2c202b60e1ffc91; odin_tt=204d6bcdabd115d2eba759df0c519c1cdcd44c12c2f726b371a36ba196b86cb69b7c4ee053979b567563edba4527a1ed0fa2d018c21d4ad349087c01d629e4e88f4a1079230d4713d2f8ba28060db270"
    }

    try:
        sixgoddata = core_sixgod(surl=url, params=params, data=data, devices={}, header=headers, log=False)
        sign_headers = sixgoddata["header"]
        sign_urls = sixgoddata["url"]
        # Perform the actual POST request
        response = requests.post(
            url=sign_urls,
            headers=sign_headers,
            data=data,
            proxies=proxies,
            timeout=25,
            verify=False
        )

        # 尝试解析JSON响应
        response_data = response.json()
        print(response_data)
        # 检查错误码
        if 'data' in response_data and response_data['data'].get('error_code') == 1105:
            logger.info(f"需要过滑块" )
            # hk = ByteDanceCaptchaAndroid(did=device['device_id_str'], iid=device['install_id_str'],
            #                              detail=json.loads(response_data['data']['verify_center_decision_conf'])[
            #                                  'detail'],proxy=proxies).verify_track()
            verify_center_decision_conf = response.json()['data']['verify_center_decision_conf']
            hk = api_slide_test(verify_center_decision_conf,str(device['install_id']), str(device['device_id']), proxies)

            # print(hk)
            logger.debug(f"滑块返回值：{hk}")
            # if hk['code'] == 502:
            #     raise RetryException("ip异常，重试")
            if "code" in hk and hk['code'] == 200:
                response = requests.post(
                    url=sign_urls,
                    headers=sign_headers,
                    data=data,
                    proxies=proxies,
                    timeout=25,
                    verify=False
                )
                logger.success("滑块成功")
                return response.json()
            else:
                logger.error(f"滑块返回值异常，{hk}")
        elif response_data['data'].get("description") in ['访问太频繁，请稍后再试','系统繁忙，请稍后再试']:
            raise RetryException("系统繁忙，请稍后再试")
        else:
            return response_data

    except requests.exceptions.RequestException as e:
        raise RetryException(f"请求错误: {e}")
    except RetryException as e:
        raise RetryException(f"重试错误: {e}")
    except Exception as e:
        logger.error(f"未知错误: {traceback.format_exc()}")
        raise RetryException(f"{e}")


def run(input_q: deque, output_dict, proxies_mode, proxies_url, user_card=False):
    """

    :param input_q:
    :param output_dict:
    :param proxies_mode:
    :param proxies_url:
    :param user_card:   是否使用身份证查询
    :return:
    """
    try:
        device = None
        # proxies = get_proxies()
        # proxies = {
        #     'http': 'http://l506.kdltps.com:15818',
        #     'https': 'http://l506.kdltps.com:15818',
        # }
        busy_counter = 0
        while True:
            if len(input_q) == 0:
                time.sleep(1)
                continue
            # 有两种情况，第一种情况下这两个分别代表手机的区号和手机号，第二种情况下这两个分别代表身份证的姓名和身份证号
            # 这两种情况不由这边控制，由添加队列的那一端控制
            area, phone = input_q.pop()
            logger.info(f"开始查询：{phone}")
            try:
                while True:
                    if device:
                        break
                    logger.debug(f'开始注册设备')
                    if proxies_mode == '2':
                        proxies = {
                            'http': "http://"+proxies_url.replace("http://", ""),
                            'https': "http://"+proxies_url.replace("http://", ""),
                        }
                    else:
                        proxies = get_proxies(proxies_url)
                    device = device_register(proxies=proxies)  # 注册设备
                    if not device or device['device_id'] == 0:
                        logger.warning("设备注册失败，重试")
                    else:
                        logger.success('注册设备成功')
                        break

                if not user_card:
                    # # encrypto_phone = str(py_account_password(area, phone))
                    # result = query_phone(encrypto_phone, device, proxies)
                    # logger.debug(f"{phone},{result}")
                    # handle_result(result, area, phone, output_dict)
                    result = query_phone(device=device, area_phone=f"{area} {phone}", proxies=proxies)
                    logger.debug(f"{phone},{result}")
                    handle_result(proxies,result, area, phone, output_dict)
                else:
                    # encrypto_name = str(xor_encrypt(f"{area}"))
                    # encrypto_idcard = str(xor_encrypt(f"{phone}"))
                    result = query_phone(
                        device=device,
                        card_name=area,
                        card=phone,
                        proxies=proxies
                    )
                    logger.debug(f"{area}----{phone},{result}")
                    handle_result(proxies,result, area, phone, output_dict)
                busy_counter = 0

            except Exception as e:
                # pass
                # if "系统繁忙，请稍后再试" in str(e):
                logger.warning(f"{e}")
                busy_counter += 1
                device = None
                if busy_counter > 10:
                    logger.warning("系统繁忙，重试次数过多，跳过")
                    handle_result(proxies,None, area, phone, output_dict)
                    busy_counter = 0
                    continue

                input_q.appendleft((area, phone))
    except Exception as e:
        logger.error(f"发生了一个神奇的错误导致消费者消失：{e}")
    logger.error(f"一次莫名其妙的消费者消失")

def test(area, phone):
    # device = {'aid': '1128', 'iid': '279743516904147', 'install_id': '279743516904147', 'device_id': '279743516687059', 'channel': 'douyin-ls-sm-xz-and-20'}
    # device = {"server_time": '1744461439', "device_id": '1880644408316201', "install_id": '1880644408320297', "new_user": '1',
    #           "device_id_str": "1880644408316201", "install_id_str": "1880644408320297",
    #           "ssid": "b49e6818-a579-4f7f-baf2-9be4d5f7bada","channel":"xiaomi_664226_64","aid":"664226",
    #           "devicetoken": "AAATHOHUGX7AM7LYTJZ43KGJ3NXAEHQZ4YFHDL4SIRGBNE5XVWXYXVDICFDZYQGCK5P6OUL7FKCGIAHGNEFENWNT4TBWNHDB5KRMJ26ATEIDD6BVDZJMKMXAWK3OK"}
    device = None
    # device = None
    # proxies = get_proxies()
    proxies = {
        # 'http': 'http://t14404650039763:y80nll0f@p226.kdltpspro.com:15818',
        # 'https': 'http://t14404650039763:y80nll0f@p226.kdltpspro.com:15818',
        # 'http': 'http://t13610080308813:inevg9s5@l505.kdltps.com:15818',
        # 'https': 'http://t13610080308813:inevg9s5@l505.kdltps.com:15818',
        # 'http': 'http://218.78.124.95:32324',
        # 'https': 'http://218.78.124.95:32324',
    }
    busy_counter = 0

    while True:
        if device:
            break
        logger.debug(f'开始注册设备')
        # print(proxies)
        device = device_register(proxies=proxies)
        print(device)
        if not device:
            logger.warning("设备注册失败，重试")
        else:
            logger.success('注册设备成功')
            break
    # logger.debug(device)
    for i in range(1):
        print(f"第{i}次查询")
        # time.sleep(180)
        try:
            result = query_phone(device=device,area_phone=f"{area} {phone}", proxies=proxies)
            busy_counter = 0
            logger.debug(f"{phone},{result}")
            a = {}
            handle_result(proxies,result, area, phone, a)
            print(a)
        except RetryException as e:
            # pass
            # if "系统繁忙，请稍后再试" in str(e):
            logger.warning(f"{e}")
            busy_counter += 1
            # device = None
            if busy_counter > 10:
                logger.warning("系统繁忙，重试次数过多，跳过")
                # handle_result(proxies,None, phone, output_dict)
                busy_counter = 0
                # continue

            # input_q.appendleft((area, phone))



if __name__ == '__main__':
    # print(xor_encrypt("于子川"))
    # main()
    # device = device_register(proxies={})
    # print(device)
    # response_data ={"data":{"captcha":"","desc_url":"","description":"滑动滑块进行验证","error_code":1105,"verify_center_decision_conf":"{\"code\":\"10000\",\"from\":\"shark_admin\",\"type\":\"verify\",\"version\":\"1\",\"region\":\"cn\",\"subtype\":\"slide\",\"ui_type\":\"\",\"detail\":\"3lJymgFSwxAHXrBpOgRc*j50ONSkec2PRmX6h49WrQ2pUVdG1QsBwWCSXDNuU*kFefPc2vcWfL3WyJompqrdjnvoh0wu6OXj9tOnd-xvACZfzy45pf6s0N5mFxRuM4NtZlvxpmuX3KHqcEFv9fCxEA3Yizc28tuZTAQX2*YRPY4EjhKZJHShgJtdFwW6nFNlyMATQRjB75vUuKeJCcqytMgTl2PmzpyAcwbeEL0hsod9mh3KaYHWBWu02A6S16f1jNL6pSl1zg1LnMw3fOSccxnPGTo0f8YVmO1uiCEIo1oO7ULqg0TAMAZT7ODw8rJF7Kksj26yHMe6czQwqXylQk5bbzG32K5zNFulCdAKnhpncrT10CszzUJg14OShNT2cRa1CaWEKSG65dhXcXF5fPM3SyiMUPmBSHkUmvALDlok1e5A8INw9Q..\",\"verify_event\":\"tt_check_account_registered\",\"fp\":\"\",\"verify_ticket\":\"VTIDEF94BM6CXQAP6WJMTZQKUV8358X7HE3ZZ8_lq\",\"server_sdk_env\":\"{\\\"idc\\\":\\\"lq\\\",\\\"region\\\":\\\"CN\\\",\\\"server_type\\\":\\\"passport\\\"}\",\"log_id\":\"20260109044222519C15C95980B87D3ACD\",\"is_assist_mobile\":false,\"is_complex_sms\":false,\"identity_action\":\"\",\"identity_scene\":\"\",\"verify_scene\":\"passport\",\"login_status\":0,\"aid\":0,\"replay_data\":{\"x-tt-passport-replay-params\":\"{}\"}}","verify_ticket":"VTIDEF94BM6CXQAP6WJMTZQKUV8358X7HE3ZZ8_lq"},"message":"error"}
    #
    #
    # #
    # hk = ByteDanceCaptchaAndroid(did='3986167761006761', iid='3986167761223849',
    #                              detail=json.loads(response_data['data']['verify_center_decision_conf'])[
    #                                  'detail'], proxy={}).verify_track()
    # print(hk)
    # exit()
    # a = {"data": {"account": [{"uid_hash": "", "register_time": "2024", "nickname": "5***",
    #                            "avatar_url": "https://lf3-static.bytednsdoc.com/obj/eden-cn/oabh_ylauljb/ljhwZthlaukjlkulzlp/account:default-avatar.png",
    #                            "not_login_ticket": "NLTDEFHSX62S7XAA5QPR3CA9BP8DM7NW4SS4YU",
    #                            "reason": "系统繁忙，请稍后再试", "passport_enterprise_user_type": 0,
    #                            "account_status_code": 7, "cert_type": 2, "account_type": 0, "account_group_id": 1,
    #                            "has_two_element": False}]}, "message": "success"}
    # aa = {}
    # handle_result({}, a, 1, 1, aa)
    # print(aa)
    # test('+1 ', '12637008719')
    # for i in range(10):
    #     test('+1 ', '17576983697')
    # is_real_name('NLTDEFMPC44FD34MHT35HXQA8UYBHYYVTDTYP9',{})
    # test('+1', '18734828403')

    lis = [
        "18382885795",
        "12895702471",
        "15185758753",
        "18382370380",
        "18382410107",
        "19342040587",
        "18382410788",
        "19342070307",
        "18382390126",
        "18382410984",
        "12894889090",
        "18382420063",
        "15182150828",
        "18382360818",
        "14107059631",
        "18382370080",
        "18382560203",
        "18382178227",
        "18382430064",
        "18382430173",
        "18382410676",
        "18382560595",
        "18382390770",
        "18382370281",
        "18382560503",
        "12607311013",
        "19342040904",
        "19342050257",
        "19342050121",
        "15182141889",
        "15182141462",
        "15182141226",
        "15182141539",
        "15184486993",
        "15182019783",
        "15182141977",
        "15184031200",
        "15182028027",
        "15186099296",
        "15185152989",
        "15185440126",
        "15186540052",
        "15186540432",
        "15186540869",
        "15186241773",
        "15189068438",
        "15186099552",
        "15187870568",
        "15186671642",
        "15186175635",
        "15186241542",
        "15187168417",
        "15186099014",
        "15189068355",
        "15188969159",
        "18389990784",
        "15186790854",
        "15187396276",
        "15186175809",
        "15184908641",
        "15184486292",
        "15186099693",
        "18382228650",
        "15188035376",
        "15187870644",
        "15186671210",
        "15189901757",
        "15858429306",
        "12048164207",
        "15186660206",
    ]

    proxies = {
        # 'http': 'http://127.0.0.1:7890',
        # 'https': 'http://127.0.0.1:7890',
        'http': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
        'https': 'http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030',
        }
    area='+'
    phone='14384445076'
  #   device = device_register(proxies=proxies)  # 注册设备
    device = {"install_id": "1325331944583875", "device_id": "1325331944579779", "secDeviceToken": "AvBZdrKW2BWURRNxkIZdrhUbD",
              "device_token": "AAA6HFWWLSJTFZ2KCOVMG72TQXC7AHC7AXZHQYCPOGXYQ5OA4JZPKFDPQDHD2KF5MTHDNBMSU3MFR3FOYMSV73HDNG7PHWSLBOGHOIILZY7NF6E4QZNT5KWLJCJ7S",
              "channel": "huawei_1128_free", "os_version": "13", "os_api": 33, "device_model": "V2244A",
              "device_type": "V2244A", "device_brand": "vivo", "device_manufacturer": "vivo", "cpu_abi": "arm64-v8a",
              "density_dpi": 480, "display_density": "xxhdpi", "resolution": "2400×1080",
              "rom": "eng.compil.20230104.233131",
              "rom_version": "qssi-user 13 TP1A.220624.014 eng.compil.20230104.233131 release-keys",
              "cdid": "78c9ad45-c454-4bdb-b1ef-87251c116c8e", "openudid": "504a4fdc1691f62b",
              "clientudid": "7c512082-e902-4fad-833a-86eafde9518c", "serial_number": "", "sim_serial_number": None,
              "launcherReferrer": "com.bbk.launcher2",
              "fingerprint": "vivo/PD2244/PD2244:13/TP1A.220624.014/compiler01042331:user/release-keys",
              "platform": "kona", "event": "caijing_initialization"}

    # device = {
    #     'install_id': '1325331944583875',
    #     'device_id': '2996589340402360',
    #     'channel':"360_1128_new_64"
    #     # 'device_id': '1677175443962540',
    # }
    logger.debug(f'设备注册结果：{device}')
    for phone in lis:
        phone = '16727729829'
        try:
            result = query_phone(device=device, area_phone=f"{area} {phone}", proxies=proxies)
        except Exception as e:
              result = f"查询失败：{e}"
        # result = query_phone(device=device, card_name='付贵',card='612425198407151435', proxies=proxies)
        logger.debug(f"{phone},{result}")
        break
    # test('+1', '16723016113')
    # test('+1', '13193183513')
    # for i in range(10):
    #     try:
    #         test('+1', '18192821474')
    #     except Exception as e:
    #         print(e)
    #         time.sleep(1)
    # test('+1', '18192821474')

    # pass
    # handle_result(None, '13193183513', {})
    # print(py_account_password('+1', '13193183513'))




