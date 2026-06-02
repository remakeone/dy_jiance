import hashlib
import json
import random
import time
from urllib.parse import urlencode, urlparse, parse_qs
from module.six_god.six_god.xLadonEncrypt import get_xladon
from module.six_god.six_god.xArgusEncrypt import get_xa_enc
from module.six_god.six_god.xGorgonEncrypt import get_xgorgon
from module.six_god.six_god.xHeliosEncrypt import get_xhelios
from module.six_god.six_god.xMedusaEncrypt import get_xm_enc


class Encrypt:
    def __init__(self,deviceInfo):
        self.deviceInfo = deviceInfo
        self.licenseID = '712198790'
        self.sign_key = 'nPwahdrenl/V9EEH7FdCytZCiAtgoYTDS79yWFlIxnE='
        # APK 相关的参数
        self.sourceInfo = {
            'aid': 1128,  # 渠道号
            'bit': 64,  # 位数，32/64
            'appVersion': '32.9.0',
            'device_platform': 'iphone',  # apk version
            'mssdkVersionStr': 'v04.09.00-ml-iOS',  # mssdk version str
            'mssdkVersionInt': 67698689,  # mssdk version int
        }
        self.st = time.time()

    def sign_ios(self, url, data: dict = None, params: dict = None, header: dict = None, devices: dict = None, x_common_params_v2: str = None, lanusk = None, prl="ios_v3"):
        """
        生成iOS签名请求的请求头和相关参数。

        参数:
            url (str): 请求的URL。
            data (dict): 请求体数据，默认为None。
            params (dict): URL查询参数，默认为None。
            header (dict): 请求头，默认为None。
            devices (dict): 设备信息，默认为None。
            x_common_params_v2 (str): 额外的公共参数，默认为None。
            lanusk (str): 用户标识，默认为None。
            prl (str): 平台信息，默认值为 "ios_v3"。

        返回:
            dict: 包含请求头、URL、参数和时间消耗等信息的字典。
        """
        # 如果提供了 params，则进行参数处理
        if params:
            x_params = params.copy()
            # 如果有 x_common_params_v2，提取并更新到参数中
            if x_common_params_v2:
                x_params.update(self.extract_url_params(x_common_params_v2))
            # 如果有设备信息，则更新相关参数
            if devices:
                for k, v in devices.items():
                    if k in x_params:
                        x_params[k] = v
            # 处理最终的URL
            eurl = url.split("?")[0] + "?" + urlencode(x_params) if "?" in url else url + "?" + urlencode(x_params)
            url_params = x_params
        elif x_common_params_v2:
            # 如果没有params但有x_common_params_v2
            x_params = {}
            x_params.update(self.extract_url_params(x_common_params_v2))
            if devices:
                for k, v in devices.items():
                    if k in x_params:
                        x_params[k] = v
            # 处理最终的URL
            eurl = url.split("?")[0] + "?" + urlencode(x_params) if "?" in url else url + "?" + urlencode(x_params)
            url_params = x_params
            res_x_params = urlencode(x_params)
        else:
            # 如果都没有params和x_common_params_v2
            eurl = url
            url_params = self.extract_url_params(eurl)

        # 处理请求头的公共参数
        res_hx_params = {}
        if x_common_params_v2:
            res_hx_params.update(self.extract_url_params(x_common_params_v2))
            if devices:
                for k, v in devices.items():
                    if k in res_hx_params:
                        res_hx_params[k] = v

        # 计算6God签名相关的头部信息
        six = self.calc_6god(eurl, bytearray(urlencode(data), "UTF-8"), self.deviceInfo, self.sourceInfo, sign_key=self.sign_key, licenseID=self.licenseID, lanusk=lanusk, platform=prl)

        # 记录请求消耗时间
        et = str(time.time() - self.st) + " Second."

        # 如果没有params但有x_common_params_v2，添加x-common-params-v2到请求头
        if not params and x_common_params_v2:
            six["x-common-params-v2"] = res_x_params

        # 准备返回的数据
        result_data = {}
        if header:
            # 如果提供了header，合并header和6God头部信息
            header.update(six)
            result_data["url"] = eurl
            result_data["header"] = header
            result_data["timerConsuming"] = et
        else:
            result_data["url"] = eurl
            result_data["header"] = six
            result_data["timerConsuming"] = et

        # 如果有res_hx_params，将其添加到返回数据
        if res_hx_params:
            result_data["res_hx_params"] = urlencode(res_hx_params)

        return result_data

    def calc_6god(self, url, data=bytes(0), deviceInfo=None, sourceInfo=None, sign_key=None, licenseID=None, lanusk=None, platform="ios"):
        """
        计算6God请求所需的自定义头部信息。

        参数:
            url (str): 请求的URL。
            data (bytes): 请求的数据，默认值为空字节串。
            deviceInfo (dict): 设备信息，默认值为None，若为空则初始化为空字典。
            sourceInfo (dict): 来源信息。
            sign_key (str): 签名密钥。
            licenseID (str): 许可证ID。
            lanusk (str): 用户标识。
            platform (str): 平台信息，默认值为"ios"。

        返回:
            dict: 包含6God请求所需的头部信息（如X-Ladon, X-Khronos等）。
        """
        if deviceInfo is None:
            deviceInfo = {}  # 如果deviceInfo为None，则初始化为空字典

        xk = int(time.time())  # 当前时间戳，用于生成Khronos和Helios等值
        callTimes = random.randint(100, 2000)  # 随机生成调用次数，用于生成X-Medusa等值
        stub = bytes(0)  # 默认空字节串

        # 如果有传入数据，则计算stub值
        if data:
            stub = bytes(hashlib.md5(data).hexdigest(), encoding="UTF-8")

        # 获取其他必要的请求头值
        xg = get_xgorgon(xk, url, data)  # 获取X-Gorgon头部
        xa = get_xa_enc(sourceInfo, url, stub, xk, deviceInfo, callTimes, sign_key, licenseID, lanusk)  # 获取X-Argus头部
        xl = get_xladon(xk, sourceInfo, int(licenseID))  # 获取X-Ladon头部
        xm = get_xm_enc(sourceInfo, deviceInfo, url, xk, stub, callTimes, sign_key, licenseID, lanusk, platform)  # 获取X-Medusa头部
        xh = get_xhelios(xk, sourceInfo, licenseID)  # 获取X-Helios头部

        # 构建返回的请求头字典
        xx = {
            'X-Ladon': xl,
            'X-Khronos': str(xk),  # 时间戳，转为字符串
            'X-Argus': xa,
            'X-Gorgon': xg,
            'X-Helios': xh,
            'X-Medusa': xm
        }

        # 如果有数据，则加入X-SS-STUB头部
        if data:
            xx["X-SS-STUB"] = stub.decode().upper()  # 将stub值转为大写字符串

        return xx

    def extract_url_params(self, url) -> dict:
        """
        从URL中提取查询参数并返回为字典形式。

        参数:
            url (str): 输入的URL字符串，可以是带有查询参数的完整URL，或者仅为查询部分（例如'key=value'格式）。

        返回:
            dict: URL查询参数的字典，键为参数名，值为参数值。
        """
        params = {}
        # 如果URL包含'?'，则直接解析，否则假设URL是查询字符串，补全成完整URL
        parsed_url = urlparse(url) if "?" in url else urlparse(f"https://www.av.cn/?{url}")

        # 获取查询字符串部分
        query_string = parsed_url.query

        # 如果有查询参数，则解析并存入字典
        if query_string:
            query_params = parse_qs(query_string)
            for key, value in query_params.items():
                params[key] = value[0]  # 默认取第一个值（如果有多个相同的参数）

        return params

    def xor_encrypt(self,s):
        '''
        加密手机号

        参数：
            +86 13123456789

        返回:
            十六进制结果
        '''
        chars = '0123456789abcdef'

        # 进行XOR加密
        arr = [i ^ 5 for i in s.encode()]

        # 生成十六进制结果
        result = ''
        for b in arr:
            result += chars[(b & 255) >> 4]  # 高四位
            result += chars[(b & 255) & 15]  # 低四位

        return result
