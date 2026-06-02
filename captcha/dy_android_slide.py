from curl_cffi import requests
import os, json, time, random
from loguru import logger
from captcha.slide_payload import build_plain_payload
from captcha.captcha_body import generate_captcha_body

H5_SDK_VERSION = os.getenv("H5_SDK_VERSION", '3.5.77')
AID = os.getenv("AID", '1128')
BD_VERSION = os.getenv("CAPTCHA_BD_VERSION", "1.0.0.759")
APP_NAME = os.getenv("APP_NAME", 'gold_browser')


def dumps(data_dict):
    return json.dumps(data_dict, separators=(',', ':'), ensure_ascii=False)


def get_distance(target_bytes, background_bytes):
    """
    ddddocr 识别滑动距离
    """
    import ddddocr
    det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    return int(det.slide_match(target_bytes, background_bytes)["target"][0] * 0.6159420289855072)


def parse_verify_data(verify_data):
    """兼容 verify_center_decision_conf 非标准 JSON。

    线上有时返回 Python 风格布尔值 True/False/None，直接 json.loads 会失败。
    这里优先按标准 JSON 解析，失败后用 ast.literal_eval 兜底；如果外层已经是 dict
    或被二次 JSON 包裹，也一并兼容。
    """
    import ast

    if isinstance(verify_data, dict):
        return verify_data
    if verify_data is None:
        raise ValueError("verify_data is None")

    text = verify_data.decode("utf-8") if isinstance(verify_data, (bytes, bytearray)) else str(verify_data)
    text = text.strip()
    if not text:
        raise ValueError("verify_data is empty")

    last_error = None
    for loader in (json.loads, ast.literal_eval):
        try:
            value = loader(text)
            # 兼容外层是 JSON 字符串、内层才是配置对象的情况
            if isinstance(value, str) and value.strip() and value.strip() != text:
                try:
                    value = parse_verify_data(value)
                except Exception:
                    pass
            if isinstance(value, dict):
                return value
            raise ValueError(f"verify_data parsed to {type(value).__name__}, expected dict")
        except Exception as exc:
            last_error = exc

    raise ValueError(f"parse verify_data failed: {last_error}; raw={text[:200]!r}")


def get_current_timestamp13():
    """
    获取13位数时间戳
    :return:
    """
    return "{}".format(int(time.time() * 1e3))


class DouYinSlide():

    def __init__(self):
        pass

    def pass_slide(self, data_dict):
        logger.info(f'抖音Android滑块 H5_SDK_VERSION:{H5_SDK_VERSION}'.center(50, '-'))
        proxies = data_dict['proxies']
        verify_data = data_dict['verify_data']
        verify_dict = parse_verify_data(verify_data)
        device_dict = data_dict['device_dict']
        log_id = verify_dict['log_id']
        detail = verify_dict['detail']
        server_sdk_env = verify_dict['server_sdk_env']
        get_url = "https://verify-hl.zijieapi.com/captcha/get"
        verify_url = "https://verify-hl.zijieapi.com/captcha/verify"
        get_headers = {
            "User-Agent": "com.cat.readall/14000 (Linux; U; Android 11; zh_CN; M2012K11C; Build/RKQ1.201112.002; Cronet/TTNetVersion:fc4cebd3 2024-12-10 QuicVersion:d9628e3d 2024-10-11)",
            "content-type": "application/json; charset=utf-8",
            "sdk-version": "2",
            "x-tt-token": "00de77138fa8cb388c51e99fcab90d000e04e1727ddb789c06136d13be0e19bb40be2e78a5cc92e65a5d96a566cd61bbef83f8891404e1586c2335653e6bb38df3b0bb6592a997f11ac6091508b0fad4e7bceed8c4a0e2f906a59a03c72cccfdee891--0a490a2066fcf12fb31b0dcc6cd2f7d8128d153e123d9b8162c1393a6454b82a73c635d812205bcef25447ab042b7dc04bec14f55c8529c54b911d7dbaae1b0d460cf9c5207318f6b4d309-3.0.1",
            "passport-sdk-version": "505109",
            "x-vc-bdturing-sdk-version": "3.7.2.cn",
            "x-tt-dt": "AAARIJXJR5AZEE5CPWKR6MTOPTYEF2DDDFNANQUEKVFGWLF6KV373FIFCRL7VY462R6CDLCFMDVB4N6GG642CO6Y54BXOKZYE4CLDZ7SCPTBL7JVZGSEPUAR3RZYPTFPA2FE3R5I267UKTPAQAP2Q6A",
            "x-tt-request-tag": "n=1;t=0;n=0;s=0;p=0",
            "x-tt-trace-id": "00-d482649a0d771666360426c6f11f19bd-d482649a0d77166601",
            'x-perseus': "7R777I2O7M2OI4CFGRpg/ZufMCgumhfj8jPcfI8l58+S4uzwJ82uIj5LveSfqJpRRxIBR7ociUt3i+O8getbQZ+5jMGFXjbGi46i/UMSXYCz8/sOnfstqj4e2l/xOKD7+51jsWlX2rsxLEkA2MYM/0gkFtXCPKvU6CALXHorX2WLekqIpQ9iiLE2U2gxzuRkii5tDHM5WWTccPvOz7WRiT1/nbkWunWz28Ihd3RuQtNKnRCtV8pgFHUOqTe1VrqTCq9tjIqRQ+LAQRE6SoJfjIxxkoV1tGboeK7bSrFyes9fkSZSoA5LKReK6YjY+um2tl+tWUThk8qMTjX9HaPyyUzp9ZkgSrk3XPGnDsAfX8LtFCKZnGnyKG2KDutkOzY7wVIMV1tmiBHu5P03SvjAz/V5iO8gr+cTAHXQWl3pisLWXZk1VWmyTGrgusLFm7c7/DwUnMQARbPmq19peIiYzgKF9BxqlyB5vdn3thyYoFzqjXBQO71Uh0IzcO+8ppoBE3Nsirxy3F4HNmwCZyELMWdFdYHZTPVY3vq6D6H+V0dxtuM9K83XIilERausZ1k7AjuPxHEDkuaYdXrrRXzaY0OUmqU+fv++TOFVjPeAkDj4zDrTXBloTC7UzRraUOvCElPNnUSVqfNb/RwzWmLCeBi90gjvn+wZO2ccWZpGPZHm7NAOCZ/I0YWo+GSvEeT+Y+nEM6DJInFadjcUwnjBQBu5jiYXBsjEvtvm4S12DW2cQwd6axtELPYFoFH3gu7gIGllSydgLOO2wToOEux9EOZ17yhCNMRoM5zT1ZJvov5HqdkwIZ4+mGbWiPc+XhTccl99m+BPa4gbuNJ26Ek3XjC2zgb+Vi2Qtg6N3LNB6Mgcu+JBgpl+CxumXKpYGa5wcRYX2tsmCp==",
            'x-medusa': "XU8cajHVN0AY1LP724UeAJh5uJQVEQANuSOb+rJqumf8QltXFTXE9VAQAA4DmMieNKGNd7kMwcsvnnYwUxBXh07sA0R4KZnQftV9KW4jl9diuDpCrFyPfRJ6he7HMtMKr6dOu5Qc/0ZlNT0yFrEvDMFiyNLr8oT+rzcg+msGjcp4L3o7wfyoHPKW/kSsshjwp+7h7vJumhgKdxNqkJvINsaxlqBKUNMX8X3lDR3nQP5gzJGSOeXcvFrS8wFhJ/tmUEOWd+FF0vt8BovpcRh0UWQOUzadPmirJJVFDoqdj0NJd4St/UU/HFbXu/TNcSGobnes8CCY+j67TWB4mUVGmSlqR6p1NYX+P+f//j/n/zgh",
            'x-argus': "Wk8cag==",
            'x-gorgon': "8404e0e60000447e1ffc148da5edb70a2003a7b5b4941e49815b",
            'x-helios': "k7IPSzi3f8X/Y6hqrRJAHu//yhKSb7r5EgBAtLRZL18f/MsF",
            'x-ladon': "/qKdqA==",
            'x-khronos': "1780240218",

        }
        get_params = {
            "aid": AID,
            "lang": "zh",
            "bd_version": BD_VERSION,
            "subtype": "slide",
            "detail": detail,
            "server_sdk_env": server_sdk_env,
            "mode": "slide",
            "did": device_dict['did'],
            "device_id": device_dict['did'],
            "os_name": "android",
            "platform": "app",
            "os_type": "0",
            "h5_sdk_version": "3.5.77",
            "webdriver": "undefined",
            "tmp": "1780240255580",
            "verify_host": "https://verify.zijieapi.com/",
            "app_name": "aweme",
            "locale": "zh_CN",
            "ch": "huoshan_fans_page_douyin",
            "channel": "huoshan_fans_page_douyin",
            "iid": device_dict['iid'],
            "vc": "38.9.0",
            "app_verison": "38.9.0",
            "region": "cn",
            "use_native_report": "1",
            "use_jsb_request": "1",
            "verify_cancellable": "0",
            "orientation": "0",
            "resolution": "1440*2880",
            "sdk_version": "4.1.3.cn",
            "os_version": "11",
            "device_brand": "Android",
            "device_model": "AOSP on taimen",
            "version_code": "380901",
            "version_name": "38.9.0",
            "device_type": "AOSP on taimen",
            "device_platform": "android",
            "use_dialog_size_v2": "1",
            "verify_data": verify_data,
            "_rticket": get_current_timestamp13(),

        }
        response = requests.get(get_url, headers=get_headers, params=get_params,
                                proxies=proxies, verify=False)
        js_data = response.json()
        code = js_data['code']
        # print(js_data)
        if code != 200:
            raise Exception("获取滑块/数据响应错误！")

        cid = js_data['data']['id']
        bk_url = js_data['data']['question']['url1']
        target_url = js_data['data']['question']['url2']
        tip_y = js_data['data']['question']['tip_y']
        bg_bytes = requests.get(bk_url, proxies=proxies, verify=False).content
        target_bytes = requests.get(target_url, proxies=proxies, verify=False).content
        distance = get_distance(target_bytes, bg_bytes)
        # logger.info(f'识别距离: {distance}')
        # 滑动轨迹
        time.sleep(random.uniform(1, 2))
        # 普通滑块
        payload = build_plain_payload(cid, distance, tip_y, detail, log_id)
        captchaBody = generate_captcha_body(payload)
        data = {
            "captchaBody": captchaBody,
        }
        post_params = {
            "aid": AID,
            "bd_version": BD_VERSION,
            "detail": detail,
            "server_sdk_env": server_sdk_env,
            "did": device_dict['did'],
            "device_id": device_dict['did'],
            "h5_sdk_version": H5_SDK_VERSION,
            "tmp": get_current_timestamp13(),
            "app_name": APP_NAME,
            "iid": device_dict['iid'],
            "verify_data": verify_data,
            "lang": "zh",
            "subtype": "slide",
            "mode": "slide",
            "os_name": "android",
            "platform": "app",
            "os_type": "0",
            "webdriver": "undefined",
            "verify_host": "https://verify.zijieapi.com/",
            "locale": "zh_CN",
            "ch": "huoshan_fans_page_douyin",
            "channel": "huoshan_fans_page_douyin",
            "vc": "38.9.0",
            "app_verison": "38.9.0",
            "region": "cn",
            "use_native_report": "1",
            "use_jsb_request": "1",
            "verify_cancellable": "0",
            "orientation": "0",
            "resolution": "1440*2880",
            "sdk_version": "4.1.3.cn",
            "os_version": "11",
            "device_brand": "Android",
            "device_model": "AOSP on taimen",
            "version_code": "380901",
            "version_name": "38.9.0",
            "device_type": "AOSP on taimen",
            "device_platform": "android",
            "use_dialog_size_v2": "1",
            "xx-tt-dd": "qJI7ttpVdGKKbSBvYqmaf0aPo"

        }
        post_headers = {
            "User-Agent": "com.cat.readall/14000 (Linux; U; Android 11; zh_CN; M2012K11C; Build/RKQ1.201112.002; Cronet/TTNetVersion:fc4cebd3 2024-12-10 QuicVersion:d9628e3d 2024-10-11)",
            "sdk-version": "2",
            "x-tt-token": "00de77138fa8cb388c51e99fcab90d000e04e1727ddb789c06136d13be0e19bb40be2e78a5cc92e65a5d96a566cd61bbef83f8891404e1586c2335653e6bb38df3b0bb6592a997f11ac6091508b0fad4e7bceed8c4a0e2f906a59a03c72cccfdee891--0a490a2066fcf12fb31b0dcc6cd2f7d8128d153e123d9b8162c1393a6454b82a73c635d812205bcef25447ab042b7dc04bec14f55c8529c54b911d7dbaae1b0d460cf9c5207318f6b4d309-3.0.1",
            "passport-sdk-version": "505109",
            "x-vc-bdturing-sdk-version": "3.7.2.cn",
            "x-tt-dt": "AAARIJXJR5AZEE5CPWKR6MTOPTYEF2DDDFNANQUEKVFGWLF6KV373FIFCRL7VY462R6CDLCFMDVB4N6GG642CO6Y54BXOKZYE4CLDZ7SCPTBL7JVZGSEPUAR3RZYPTFPA2FE3R5I267UKTPAQAP2Q6A",
            "x-tt-request-tag": "n=1;t=0;n=0;s=0;p=0",
            "content-type": "application/json; charset=utf-8",
            "x-tt-trace-id": "00-d482f2ce0d771666360426ccc49919bd-d482f2ce0d77166601",
            'x-perseus': "RCRRRmV0t2EM2MyA6X0xjetNGLEs4lIBgjBvlZoNMMM8pRuLqtD6pPFBbeDyPw0wXy8XwvQXKcfho+wzYClEnCurAs/+qZUfSfoGbtS6GgcvYhwqenC0Z4GcSwEqXc50MVYjyi54RSr24pAkT4gB6O5oc0UJVWQ46bWqtjEYoi+vGUE0u3qqYmDRGHqyXq5iQcb6gQfldio+F5DIEqj/yJvIfcDnKcVoTVn4ZvEcM9f0MsDfeH56fK37OOlI9pWNmpmBSfbyo4kTex4vAmFpMEDaMMe+HXDxgpzQbtXFNSFH7uiRuPEPqayTLOl1Idrk+j2qiN+1zCqLqDV6NokF3Wl2XiO578CuNMMB88SRFYQoli195GA6/gT6qAPAMPkUbHoYj5WBzdchQQNxZbelwjWNoaUKibGr4+KeFAT70AkQMv/ald+Cr5EEwCCy4TRmFQ+4CUCMaW1zLZW/msVeYp94+/i6h+MNsJN22G2pv+iKOzFMLs8QSFkrnLgjXAD4eiOp2y3ZkvehiTn6TSyeeuyTV6d2sxJNiON+zj0fNEWlRCOBYtxvKGTkDqvRtJuOlTNUMOzloNJC3rIZ2Qp8rV+g64udyvsDU4EIraigeCaEDpow1ffoRNgjFP1R460yFLgO7E+lCG1PG6EgxNDl04tRpEsikPSiYme83V2Ld1QZulJrrjSX6flbA0LovVmidmVIw+64/XMS9MDuDt+FmJpTxsMD0Bx71XxDJIMy92X+95w/yyH5v7afErFPW6yVA3SvXt66ruOAJhULzP41kgdgqDw/+HF0zechu9EJ+mN9vTskF8dCVI9Vhgn2MULyb/dFKmdv0OjRsguoAN9W8Q9JyTvcKbAeAGGad2qUhpNysiwXHA4Wza/7/JHx/lmaifO7ie==",
            'x-medusa': "g1Icau/IN0DGybP7BZgeAEZkuJSZsQANclxu8pPbHefMkhQc+TUbJpAtASMIGFQiTOJIaChOwBr1Co9hIK43IQc8fK3807q42j583vS2s23SochSVDsy9vLou5sS1RHGqOfBYxVaVNYfUiO3udn9/DfzKYCPF4G2PPe81tuHIye07mkmOnAx2jHEuHa/LHcd7ONyJZ815aCr+8eMe/tWg9nkmtuNW8u+bqTvTlQLj0st6oIg4Ma7BR+ViSsHKWgFm7PzIL47xm9Af640i9+Toey4Np9r3uNBJC42Vi70SFR6yJRr7kGAOpzVO+Kkk1ZLr0mmE51LP9JWJLGXVSIiTW1w6zklrf//N63//zcZSw==",
            'x-argus': "hFIcag==",
            'x-gorgon': "840480470000af0ea7b058a66b59946ac8af092f379afd8ae463",
            'x-helios': "lPkjL89yzXSVTfuZCGJhsnYnZOjmXip6e5mrWhxJt7Fp5umO",
            'x-ladon': "dvOxaA==",
            'x-khronos': "1780241028",
        }

        response = requests.post(verify_url, headers=post_headers, params=post_params,
                                 data=dumps(data), proxies=proxies, verify=False)
        data_dict = response.json()
        logger.info(f'接口数据: {data_dict}')
        return {
            'code': data_dict['code'],
            'device_dict': device_dict,
            # 'detail': detail,
            'verify_dict': data_dict,
            # 'H5_SDK_VERSION': H5_SDK_VERSION
        }


dy_android_helper = DouYinSlide()

if __name__ == '__main__':
    for _ in range(10):
        print(f'当前测试次数: {_ + 1}')
        xx = {"description": "滑动滑块进行验证", "error_code": 1105,
              "verify_center_decision_conf": "{\"code\":\"10000\",\"from\":\"shark_admin\",\"type\":\"verify\",\"version\":\"1\",\"region\":\"cn\",\"subtype\":\"slide\",\"ui_type\":\"\",\"detail\":\"UxzEsUvSlPGAu1oEP7oy7rotZSj3BrL*5pkSJu39gvywXldLR95KUkxjkYBaFmudWLdIO5IonQ6xzKo9sukOG16lPRSLBLluFW6vsJnc-FxxCrIFb5zhh1N4dkQBUGJR8pDImwSf6w093ru9ayccI6CLo7rNOGf54WUDIqGnFyTbueu4uLGDCZfVhIDnycLfz6Kl9iWQ-K7OqLuZ8u6CZNpN4K5SUARloPEk-9E5kJT5HI1F6avQKMg6oTToZOL6B9ZUvPIO4r4wqKptAMfyiQi8pbmsDYhy53IcT-*CX5ff39ScV-DH8qxjl4-Xwwbqo570bORRUyqDBk4kd9Zfm-GDlsDaFJ7r4n5qUUivpg4ZPzVvphbk6P8IgsQBNq22dUcE*6UbGi4dWNY.\",\"verify_event\":\"tt_sso_send_code\",\"fp\":\"verify_moy99d3q_htSLrt3A_LhbJ_4gk3_ATsD_WijVUpcPMzPI\",\"verify_ticket\":\"VTIDEF6BADA6Y68467D26N78XDQY82TGQ9YM8J_lf\",\"server_sdk_env\":\"{\\\"idc\\\":\\\"lf\\\",\\\"region\\\":\\\"CN\\\",\\\"server_type\\\":\\\"passport\\\"}\",\"log_id\":\"202605091923106483BC15F6F4A7150116\",\"is_assist_mobile\":false,\"is_complex_sms\":false,\"identity_action\":\"\",\"identity_scene\":\"\",\"verify_scene\":\"passport\",\"login_status\":0,\"aid\":0,\"replay_data\":{\"x-tt-passport-replay-params\":\"{}\"}}",
              "verify_ticket": "VTIDEF6BADA6Y68467D26N78XDQY82TGQ9YM8J_lf"}
        # verify_data = xx['data']['verify_center_decision_conf']
        verify_data = xx['verify_center_decision_conf']
        data = {
            'proxies': {},
            'verify_data': verify_data,  # 字符串
            'device_dict': {
                'did': '2789941065296979',
                'iid': '2789941065301075',
            },
        }
        dy_android_helper.pass_slide(data)  # npm install jsdom
