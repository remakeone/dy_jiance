# -*- encoding: utf-8 -*-
import base64
import json
import random
import time

from module.six_god2.sign_proto import EecryptParams
from module.six_god2.xgorgon import encrypt_gorgon
from module.six_god2.header import get_params_encrypturl, xssstub_hash_md5_hex, url_encode
from module.six_god2.helios import encrypt_helios
from module.six_god2.medusa import gen_medusa

def lowerHeader(header: dict):
    """
    将header的key统一转换成小写
    """
    new_header = {}
    for key, value in header.items():
        new_header[str(key).lower()] = value
    header.clear()
    header.update(new_header)
    return new_header


def core_sixgod(surl, params, devices, data:dict={},  common=None, header=None, lanusk="", log=False):
    if devices:
        for k, v in devices.items():
            if k in data:
                data[k] = v
    dataType = header.get("content-type", header.get("Content-Type"))
    xg_rand = int(random.randint(0, 0xFFFF))
    url, url_params, x_common = get_params_encrypturl(surl, params=params, devices=devices, common=common)

    khronos = int(time.time())
    params = EecryptParams()
    params.khronos = str(khronos)
    params.ladon = base64.b64encode(khronos.to_bytes(4, 'big')).decode()
    params.argus = base64.b64encode(khronos.to_bytes(4, 'little')).decode()
    params.gorgon = encrypt_gorgon(data, url_encode(url_params), khronos, xg_rand, dataType)
    params.helios = encrypt_helios(khronos, rand=0)
    params.medusa = gen_medusa(
        url,
        url_params,
        devices,
        data,
        khronos,
        lanusk,
        dataType=dataType
    )
    six = result(params, data, url,  common=x_common, dataType=dataType, log=log)

    headers = header.copy()
    lowerHeader(header=headers)
    headers.update(six.get("sign_header"))
    if devices:
        headers["x-tt-dt"] = devices.get("x_tt_dt", "")
        headers["user-agent"] = devices.get("ua", "")
    return headers, six.get("sign_url")


def sign_android(url, params: dict = None, data: dict = None, header: dict = None, x_common_params_v2=None,
                 lanusk='', cell=False, log=False):
    """
    生成Android签名请求的请求头和相关参数。

    参数:
        url (str): 请求的URL。
        params (dict): URL查询参数，默认为None。
        data (dict): 请求体数据，默认为None。
        header (dict): 请求头，默认为None。
        devices (dict): 设备信息，默认为None。
        x_common_params_v2 (str): 额外的公共参数，默认为None。
        lanusk (str): 用户标识，默认为None。
        log (boon): 打印日志，默认为False。

    返回:
        dict: 包含SixGods请求所需的头部信息（如X-Ladon, X-Khronos等）。
    """
    # from sixgods.android.xgorgon import encrypt_gorgon
    # from sixgods.android.helios import encrypt_helios
    # from sixgods.android.medusa import gen_medusa

    dataType = header.get("content-type", header.get("Content-Type", "application/x-www-form-urlencoded;"))

    surl, url_params, x_common = get_params_encrypturl(url, params=params, common=x_common_params_v2)
    khronos = int(time.time())
    six = {
        'X-Gorgon': encrypt_gorgon(data, url_encode(url_params), khronos, int(random.randint(0, 0xFFFF)), dataType),
        'X-Khronos': str(khronos),
        'X-Ladon': base64.b64encode(khronos.to_bytes(4, 'big')).decode(),
        'X-Argus': base64.b64encode(khronos.to_bytes(4, 'little')).decode(),
        'X-Helios': encrypt_helios(khronos, rand=0),
        'X-Medusa': gen_medusa(
            surl,
            url_params,
            {},
            data,
            khronos,
            lanusk,
            dataType=dataType
        )
    }

    # 如果有数据，则加入X-SS-STUB头部
    if data:
        six["X-SS-STUB"] = xssstub_hash_md5_hex(data=data, dataType=dataType)

    # 记录请求消耗时间
    # et = str(time.time() - self.st) + " Second."
    et = "0 Second."

    # 如果没有params但有x_common_params_v2，添加x-common-params-v2到请求头
    if not params and x_common_params_v2:
        six["x-common-params-v2"] = x_common

    # 准备返回的数据
    result_data = {}
    if header:
        # 如果提供了header，合并header和6God头部信息
        header.update(six)
        result_data["url"] = surl
        result_data["header"] = header
        result_data["timerConsuming"] = et
    else:
        result_data["url"] = surl
        result_data["header"] = six
        result_data["timerConsuming"] = et

    if log:
        print(json.dumps({'url': surl, 'header': six, 'timerConsuming': et, 'platform': 'android'}, indent=4,
                         ensure_ascii=False))

    if cell:
        return header, surl
    else:
        return result_data



def result(params: EecryptParams, data, eurl,  common=None, sell=False, dataType=None, log=False):

    six = {
        'x-ladon': params.ladon,
        'x-khronos': params.khronos,
        'x-argus': params.argus,
        'x-gorgon': params.gorgon,
        'x-helios': params.helios,
        'x-medusa': params.medusa
    }
    if data:
        six["x-ss-stub"] = xssstub_hash_md5_hex(data=data, dataType=dataType)
    if sell:
        datas: dict = dict()
        datas["api"] = eurl
        datas["sign"] = six
        if common:
            datas["sign"]["x-common-params-v2"] = common
        return datas
    datas: dict = dict()
    datas["sign_url"] = eurl
    datas["sign_header"] = six
    if common:
        datas["sign_header"]["x-common-params-v2"] = common
    if log:
        print(json.dumps(datas, indent=4, ensure_ascii=False))
    return datas