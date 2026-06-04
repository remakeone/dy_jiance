import json
import queue
import traceback
from collections import deque

import requests
import time
from loguru import logger

from flurl3.core import core_sixgod
from module.error.error import SystemBusyException, ProxyInvalidException, CaptchaFailedException

# 滑块最多尝试次数
MAX_CAPTCHA_ATTEMPTS = 10
# 判定为系统繁忙的接口文案
BUSY_DESCRIPTIONS = ('访问太频繁，请稍后再试', '系统繁忙，请稍后再试')
# 查询账号接口
QUERY_ACCOUNT_URL = "https://aggr5-normal-s12.amemv.com/passport/safe/query_account/"
# 设备注册接口
DEVICE_REGISTER_URL = "http://154.23.189.16:31818/device/v1/0602/getDevice"
# 滑块服务接口
SLIDE_API_URL = 'http://180.97.215.147:9954/api/douyin/slide/android'

logger.add(
    "log/log_new.log",
    rotation="100 MB",
    retention="1 week",
    encoding="utf-8",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
           "Thread: {thread} | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
)


class WorkerContext:
    """单个消费者线程内的设备与代理会话，负责复用与失效回收。"""

    def __init__(self, proxies_mode, proxies_url):
        """
        :param proxies_mode: 代理模式，1=提取式，2=隧道（兼容字符串或数字）
        :param proxies_url: 提取 API 或隧道地址
        """
        self.proxies_mode = str(proxies_mode)
        self.proxies_url = proxies_url
        self.device = None
        self.proxies = None

    def is_tunnel(self):
        """是否为隧道代理模式。"""
        return self.proxies_mode in ('2',2,)

    def invalidate_device(self):
        """系统繁忙后废弃当前设备，下次查询重新注册。"""
        self.device = None
        logger.debug("已废弃当前设备，等待重新注册")

    def invalidate_proxy(self):
        """提取式代理失效后清空，下次重新拉取；隧道模式不清理。"""
        if not self.is_tunnel():
            self.proxies = None
            logger.debug("已废弃当前提取式代理，等待重新获取")

    def _build_tunnel_proxies(self):
        """组装隧道代理 dict。"""
        url = self.proxies_url.replace("http://", "").replace("https://", "")
        proxy_url = f"http://{url}"
        return {'http': proxy_url, 'https': proxy_url}

    def ensure_proxies(self):
        """确保代理可用：隧道只建一次，提取式在为空时拉取。"""
        if self.proxies:
            return
        # 隧道模式：固定地址，长期复用
        if self.is_tunnel():
            self.proxies = self._build_tunnel_proxies()
            logger.success("隧道代理已就绪")
            return
        # 提取式：拉取新 IP
        self.proxies = get_proxies(self.proxies_url)
        logger.success(f"提取式代理已就绪: {self.proxies.get('http', '')}")

    def ensure_device(self):
        """确保设备已注册；注册请求走当前代理。"""
        self.ensure_proxies()
        while not self.device:
            logger.debug("开始注册设备")
            device = device_register(proxies=self.proxies)
            device_id = device.get('device_id') if device else None
            # 设备 ID 为 0 或缺失视为失败
            if not device or device_id == 0 or device_id == '0':
                logger.warning("设备注册失败，稍后重试")
                time.sleep(1)
                continue
            self.device = device
            logger.success(f"注册设备成功 device_id={device_id}")

    def ensure_ready(self):
        """同时保证代理与设备就绪。"""
        self.ensure_device()


def device_register(proxies):
    """
    从远程服务获取抖音设备信息。
    :param proxies: 与后续查询一致的代理
    :return: 设备 dict，含 install_id / device_id
    """
    try:
        response = requests.get(DEVICE_REGISTER_URL, timeout=30)
        response.raise_for_status()
        res_json = response.json()
        res_json['install_id'] = res_json.get('iid') or res_json.get('install_id')
        return res_json
    except requests.exceptions.RequestException as e:
        logger.error(f"设备注册网络异常: {e}")
        raise ProxyInvalidException(f"设备注册网络异常: {e}") from e


def api_slide_test(detail, log_id, iid, did, proxies):
    """
    调用第三方 Android 滑块接口。
    :return: 接口 JSON；失败返回 None
    """
    payload = {
        "uid": "dea889cd-d1e9-46ab-a2ac-71adcbc1156b",
        "service_name": "dy_android_slide_api",
        "aid": "1128",
        "detail": detail,
        "log_id": log_id,
        "server_sdk_env": "{\"idc\":\"lf\",\"region\":\"CN\",\"server_type\":\"passport\"}",
        "proxies": proxies if '127.0.0.1' not in str(proxies) else {},
        "device_dict": {"did": did, "iid": iid},
    }
    try:
        response = requests.post(
            SLIDE_API_URL,
            json=payload,
            timeout=20,
            headers={"Content-Type": "application/json"},
        )
        logger.debug(f"滑块返回值: {response.json()}")
        result = response.json()
        return result
    except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError) as e:
        logger.error(f"滑块请求异常: {e}")
        return None


def get_proxies(api_url):
    """
    从提取 API 获取一条代理 IP。
    :raises ProxyInvalidException: 拉取失败或内容为空
    """
    try:
        proxy_ip = requests.get(api_url, timeout=15).text.strip()
    except requests.exceptions.RequestException as e:
        raise ProxyInvalidException(f"获取代理IP网络异常: {e}") from e
    if not proxy_ip:
        raise ProxyInvalidException("获取代理IP失败: 响应为空")
    return {
        'http': f'http://{proxy_ip}',
        'https': f'http://{proxy_ip}',
    }


def parse_area_code(area: str) -> str:
    """
    从区号字符串解析 API 用的 area_code（不含 +）。
    例如 +86 -> 86，+1 -> 1
    """
    code = (area or '').strip().lstrip('+')
    return code if code else '86'


def get_data(area=None, phone=None, card_name=None, card=None):
    """
    构造 query_account 表单 body。
    手机号模式传 area + phone；身份证模式传 card_name + card。
    """
    # 手机号找回
    if card_name is None and card is None:
        area_code = parse_area_code(area)
        return {
            "is_vcd": "1",
            "reg_cookie_opt": "true",
            "ttnet_sdk_version": "4.2.278.8-douyin",
            "auth_sdk_version": "4.7.5",
            "enter_from": "recover",
            "hide_user_name_v3": "1",
            "mix_mode": "1",
            "area_code": area_code,
            "account_app_language": "zh",
            "mobile": xor_encrypt(phone),
            "language": "zh",
            "query_type": "0",
            "multi_login": "1",
            "account_api_standard": "emo_douyin_account_recover",
            "scene": "find_account",
            "sec_sdk_version": "67764480",
            "account_sdk_source": "app",
            "passport_support_flow": "choose_account,captcha,real_name_check,verify",
            "verify_sdk_version": "4.1.3.cn",
        }
    # 身份证找回
    return {
        'enter_from': 'recover',
        'find_account_ab_group': 'v0',
        'hide_user_name_v3': '1',
        'is_vcd': '1',
        'mix_mode': '1',
        'identity_name': str(xor_encrypt(card_name)),
        'identity_no': str(xor_encrypt(card)),
        'query_type': '3',
        'scene': 'find_account',
    }


def xor_encrypt(s):
    """对字符串做异或加密并转为十六进制文本。"""
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    return ''.join([chars[(b & 255) >> 4] + chars[(b & 255) & 15] for b in arr])


def _build_query_params(device):
    """拼装 query_account 的 URL 查询参数。"""
    return {
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
        "use_store_region_cookie": "1",
    }


def _build_query_headers(device):
    """拼装 query_account 请求头（签名前）。"""
    return {
        'User-Agent': "com.ss.android.ugc.aweme/380901 (Linux; U; Android 11; zh_CN_#Hans; "
                      "AOSP on taimen; Build/RP1A.200720.009; Cronet/TTNetVersion:e3d16265 2026-05-11 "
                      "QuicVersion:afeca321 2026-04-27)",
        'x-tt-request-tag': "bdr-cnt=1;s=-1;p=0",
        'x-security-argus': "BridgeNetworkRequest/unknown aid/1128/huoshan_fans_page_douyin/Android/38.9.0/h5/213 "
                            "https://api.amemv.com/ucenter_web/app/aweme/account_rebind_auth_verify",
        'contenttype': "application/x-www-form-urlencoded",
        'bd-ticket-guard-display-os-version': "RP1A 200720.009 release-keys",
        'bd-ticket-guard-ree-public-key': "BESw/v0g6c3E7LP6vrPxKgmUjsOOTUhV9BdDexqSwUDFXsaowzboMa83bO11UkauzZrThxQEi72fHtGfvHmXm5M=",
        'bd-ticket-guard-version': "3",
        'bd-ticket-guard-tee-status': "1",
        'sdk-version': "2",
        'bd-ticket-guard-iteration-version': "2",
        'passport-sdk-version': "60571",
        'x-ss-req-ticket': "1780240253926",
        'x-vc-bdturing-sdk-version': "4.1.3.cn",
        'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
        'x-ss-stub': "1FB719D47D4070285F442B93B5FE4561",
        'x-tt-bdturing-retry': "1",
        'x-tt-ttnet-origin-host': "api5-normal-lq.amemv.com",
        'x-ss-dp': "1128",
        'Cookie': (
            f"store-region=cn-fj; store-region-src=did; install_id={device['install_id']}; "
            f"ttreq=1$9380e7ed80dc051525b7e3479b6c1959535ad289; "
            f"passport_csrf_token=01ff0f8438de198ae2c202b60e1ffc91; "
            f"passport_csrf_token_default=01ff0f8438de198ae2c202b60e1ffc91; "
            f"odin_tt=204d6bcdabd115d2eba759df0c519c1cdcd44c12c2f726b371a36ba196b86cb69b7c4ee053979b567563edba4527a1ed0fa2d018c21d4ad349087c01d629e4e88f4a1079230d4713d2f8ba28060db270"
        ),
    }


def _is_system_busy(response_data: dict) -> bool:
    """根据接口 body 判断是否系统繁忙。"""
    if not isinstance(response_data, dict):
        return False
    data = response_data.get('data') or {}
    description = data.get('description') or ''
    if description in BUSY_DESCRIPTIONS:
        return True
    # 成功体里账号条目的 reason 也可能带繁忙
    accounts = data.get('account') or []
    if accounts and isinstance(accounts[0], dict):
        reason = accounts[0].get('reason') or ''
        if '系统繁忙' in reason or '请稍后再试' in reason:
            return True
    return False


def _signed_post(device, data, proxies):
    """
    六签后对 query_account 发起 POST。
    :raises ProxyInvalidException: 网络层失败
    """
    params = _build_query_params(device)
    headers = _build_query_headers(device)
    try:
        signed = core_sixgod(
            surl=QUERY_ACCOUNT_URL,
            params=params,
            data=data,
            devices=device,
            header=headers,
            log=False,
        )
        response = requests.post(
            url=signed["url"],
            headers=signed["header"],
            data=data,
            proxies=proxies,
            timeout=25,
            verify=False,
        )
        return response
    except requests.exceptions.RequestException as e:
        raise ProxyInvalidException(f"查询账号网络异常: {e}") from e


def _solve_captcha(device, response_data, proxies) -> bool:
    """
    解析 1105 响应并调用滑块服务。
    :return: 滑块是否成功
    """
    data = response_data.get('data') or {}
    conf_raw = data.get('verify_center_decision_conf')
    if not conf_raw:
        logger.error("滑块配置 verify_center_decision_conf 缺失")
        return False
    try:
        conf = json.loads(conf_raw) if isinstance(conf_raw, str) else conf_raw
    except json.JSONDecodeError as e:
        logger.error(f"滑块配置 JSON 解析失败: {e}")
        return False
    hk = api_slide_test(
        conf.get('detail'),
        conf.get('log_id'),
        str(device['install_id']),
        str(device['device_id']),
        proxies,
    )
    return isinstance(hk, dict) and hk.get('code') == 200


def query_phone(device, area=None, phone=None, card_name=None, card=None, proxies=None):
    """
    查询账号是否注册及状态。
    :param device: 设备信息
    :param area: 区号，如 +86（手机号模式）
    :param phone: 手机号（手机号模式）
    :param card_name: 姓名（身份证模式）
    :param card: 身份证号（身份证模式）
    :param proxies: 代理
    :return: 接口 JSON dict
    :raises SystemBusyException: 系统繁忙，应更换设备
    :raises ProxyInvalidException: 代理/网络失效
    :raises CaptchaFailedException: 滑块失败
    """
    data = get_data(area=area, phone=phone, card_name=card_name, card=card)

    for captcha_round in range(MAX_CAPTCHA_ATTEMPTS):
        response = _signed_post(device, data, proxies)
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise CaptchaFailedException(f"响应非 JSON: {e}") from e

        logger.debug(f"query_account 响应: {response_data}")

        # 系统繁忙：抛专用异常，由 run 废弃设备
        if _is_system_busy(response_data):
            raise SystemBusyException("系统繁忙，请稍后再试")

        data_block = response_data.get('data') or {}
        error_code = data_block.get('error_code')

        # 需要滑块：过码后重新签名再请求（下一轮循环会重新 core_sixgod）
        if error_code == 1105:
            try:
                if not _solve_captcha(device, response_data, proxies):
                    logger.error(f"滑块失败，重试 {captcha_round + 1}/{MAX_CAPTCHA_ATTEMPTS} 次")
                    continue
            except Exception as e:
                logger.error(f"滑块失败，重试 {captcha_round + 1}/{MAX_CAPTCHA_ATTEMPTS} 次")
                continue
        else:
            return response_data

    raise CaptchaFailedException(f"滑块重试已达上限 {MAX_CAPTCHA_ATTEMPTS}")


def exc_face_verify(not_login_ticket, device, proxies):
    """
    查询正常老号的实名/验证方式说明（verify_reason）。
    :return: 验证说明字符串，失败返回 False
    """
    url = "https://aggr5-normal-s12.amemv.com/passport/safe/query_decision/"
    params = {
        "passport-sdk-version": "60571",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "sec_sdk_version": "67764480",
        "ttnet_sdk_version": "4.2.278.8-douyin",
        "auth_sdk_version": "4.7.5",
        "account_flow": "verify",
        "account_app_language": "zh",
        "verify_sdk_version": "4.1.3.cn",
        "verify_scene": "find_account",
        "language": "zh",
        "not_login_ticket": not_login_ticket,
        "hide_mobile_by_region": "true",
        "multi_login": "1",
        "account_sdk_source": "app",
        "passport_support_flow": "choose_account,captcha,real_name_check,verify",
        "klink_egdi": "AAKm_yCa2llmlc_Hv7NG6_ZUe47wGUYo8zlW-h0QcBlCVei4Iv2IPrYS",
        "iid": str(device.get('install_id', '')),
        "device_id": str(device.get('device_id', '')),
        "ac": "wifi",
        "channel": device.get('channel') or "huoshan_fans_page_douyin",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "380900",
        "version_name": "38.9.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "AOSP on taimen",
        "device_brand": "Android",
        "os_api": "30",
        "os_version": "11",
        "manifest_version_code": "380901",
        "resolution": "1440*2712",
        "dpi": "560",
        "update_version_code": "38909900",
        "_rticket": "1780499067509",
        "package": "com.ss.android.ugc.aweme",
        "first_launch_timestamp": "1780331169",
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
        "ts": "1780499099",
        "cdid": "a928357e-4b19-4e4f-83ff-4a101ce7d4a6",
        "cronet_version": "5e677c20_2026-03-23",
        "ttnet_version": "4.2.278.4-douyin",
        "use_store_region_cookie": "1",
    }
    headers = {
        'User-Agent': "com.ss.android.ugc.aweme/380901 (Linux; U; Android 11; zh_CN_#Hans; AOSP on taimen; "
                      "Build/RP1A.200720.009; Cronet/TTNetVersion:e3d16265 2026-05-11 QuicVersion:afeca321 2026-04-27)",
        'contenttype': "application/x-www-form-urlencoded",
        'passport-sdk-version': "60571",
        'x-vc-bdturing-sdk-version': "4.1.3.cn",
        'x-tt-ttnet-origin-host': "api5-normal-lq.amemv.com",
        'x-ss-dp': "1128",
    }
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=25, verify=False)
            body = response.json()
            return body["data"]["event_params"]["verify_reason"]
        except (requests.exceptions.RequestException, KeyError, TypeError, json.JSONDecodeError) as e:
            logger.warning(f"实名查询失败 {attempt + 1}/3: {e}")
            time.sleep(1)
    return False


def _result_row(area, phone, status, is_real_name=False, user_name='无', year='无'):
    """构造写入 result_dict 的标准行。"""
    return {
        "area": area,
        "phone": phone,
        "user_name": user_name,
        "year": year,
        "status": status,
        "is_real_name": is_real_name,
    }


def handle_result(proxies, device, result, area, phone, result_dict: dict, status_override=None):
    """
    将接口 JSON 转为业务状态并写入 result_dict。
    :param status_override: 强制状态（如滑块失败、请求失败）
    """
    if status_override:
        result_dict[phone] = _result_row(area, phone, status_override)
        return

    if not result or not isinstance(result, dict):
        result_dict[phone] = _result_row(area, phone, '请求失败')
        return

    message = result.get('message', '')
    data = result.get('data') or {}

    # 锁定账号
    if '账号已被锁定' in message or '账号已被锁定' in str(data):
        accounts = data.get('account') or []
        account = accounts[0] if accounts else {}
        result_dict[phone] = _result_row(
            area, phone, '锁定账号',
            user_name=account.get('nickname', '无'),
            year=account.get('register_time', '无'),
        )
        return

    # 未注册
    if '用户不存在' in message or '用户不存在' in str(data):
        result_dict[phone] = _result_row(area, phone, '未注册号')
        return

    accounts = data.get('account') or []
    if not accounts:
        result_dict[phone] = _result_row(area, phone, '无信息')
        return

    account = accounts[0]
    account_status_code = account.get('account_status_code')
    register_time = account.get('register_time', '无')
    account_group_id = account.get('account_group_id')
    nickname = account.get('nickname', '无')

    if account_group_id == 18:
        status = "火山账号"
        is_real_name = False
    elif account_status_code in (2132, 2089):
        status = "封禁号"
        is_real_name = False
    else:
        status = "正常老号"
        ticket = account.get('not_login_ticket')
        # 有 ticket 才查实名
        is_real_name = exc_face_verify(ticket, device, proxies) if ticket else False

    result_dict[phone] = _result_row(
        area, phone, status,
        is_real_name=is_real_name,
        user_name=nickname,
        year=register_time,
    )


def run(input_q: deque, output_dict, proxies_mode, proxies_url, user_card=False):
    """
    消费者线程：从队列取任务查询，设备复用至系统繁忙，提取式代理复用至网络异常。
    :param input_q: 任务队列 (area, phone)
    :param output_dict: 线程共享结果 dict
    :param proxies_mode: 1 提取 / 2 隧道
    :param proxies_url: 代理配置
    :param user_card: True 表示身份证模式（area=姓名, phone=身份证号）
    """
    ctx = WorkerContext(proxies_mode, proxies_url)
    try:
        while True:
            if len(input_q) == 0:
                time.sleep(1)
                return True

            area, phone = input_q.pop()
            logger.info(f"开始查询: {phone}")

            try:
                ctx.ensure_ready()

                if not user_card:
                    result = query_phone(
                        device=ctx.device,
                        area=area,
                        phone=phone,
                        proxies=ctx.proxies,
                    )
                else:
                    result = query_phone(
                        device=ctx.device,
                        card_name=area,
                        card=phone,
                        proxies=ctx.proxies,
                    )

                handle_result(ctx.proxies, ctx.device, result, area, phone, output_dict)
                logger.debug(f"查询完成 {phone}: {result}")

            except SystemBusyException as e:
                # 仅废弃设备，代理继续复用；任务回队
                logger.warning(f"系统繁忙，更换设备后重试: {phone} | {e}")
                ctx.invalidate_device()
                input_q.appendleft((area, phone))

            except ProxyInvalidException as e:
                # 提取式：废弃代理；隧道：仅记录，仍回队重试
                logger.warning(f"代理失效: {phone} | {e}")
                ctx.invalidate_proxy()
                input_q.appendleft((area, phone))

            except CaptchaFailedException as e:
                logger.error(f"滑块失败: {phone} | {e}")
                handle_result(ctx.proxies, ctx.device, None, area, phone, output_dict, status_override='滑块失败')

            except Exception as e:
                logger.error(f"查询异常: {phone} | {e}\n{traceback.format_exc()}")
                handle_result(ctx.proxies, ctx.device, None, area, phone, output_dict, status_override='请求失败')

    except Exception as e:
        logger.error(f"消费者线程退出: {e}\n{traceback.format_exc()}")


def test(area, phone):
    """本地单条调试：设备与代理复用规则与 run 一致。"""
    proxies_url = "http://1342522532909436928:4FA258Uu@http-dynamic-S02.xiaoxiangdaili.com:10030"
    proxies_url = "http://127.0.0.1:10809"
    proxies_mode = '2'
    # ctx = WorkerContext('2', proxies_url)
    # ctx.ensure_ready()
    # ctx.proxies = {}
    # ctx.ensure_device()
    init_queue = deque([(area, phone)])
    output_dict = {}
    run(init_queue, output_dict, proxies_mode, proxies_url, user_card=False)
    # result = query_phone(device=ctx.device, area=area, phone=phone, proxies=ctx.proxies)
    # handle_result(ctx.proxies, ctx.device, result, area, phone, output)
    logger.info(f"调试结果: {output_dict}")


if __name__ == '__main__':
    # 本地调试示例（按需取消注释）
    test('+1', '13100000000')
    pass
