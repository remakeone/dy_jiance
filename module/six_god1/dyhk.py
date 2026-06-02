import uuid
from io import BytesIO
import cv2
import numpy as np
from Crypto.Cipher import AES
from urllib import parse
import requests
import random
import base64
import json
import time
from PIL import Image
from loguru import logger
from Crypto.Hash import SHA512

from module.error.error import RetryException


class VerifyAweme:
    def __init__(self,did,iid,proxy=""):
        self._get_url = "https://verify.zijieapi.com/captcha/get?"
        self._verify_url = "https://verify.zijieapi.com/captcha/verify?"
        self._query_account_url = "https://api.amemv.com/passport/safe/query_account/?"
        self._query_account_url2 =""
        self._headers = {
            "sdk-version": "2",
            "passport-sdk-version": "203309",
            "x-vc-bdturing-sdk-version": "3.7.4.cn",
            "user-agent": "com.ss.android.ugc.aweme.lite/320801 (Linux; U; Android 11; zh_CN; M2103K19C; Build/RP1A.200720.011;tt-ok/3.12.13.17)",
        }
        self.iid=iid
        self.did=did
        self.oaid="4067ae1c4d619ec8"
        self.openudid="86c34f420d9ff2aa"
        self.first_launch_timestamp="1736449776"
        self.he1={}
        self.proxy = proxy or {}
    def pilImgToCv2(self,img: Image.Image, flag=cv2.COLOR_RGB2BGR):
        return cv2.cvtColor(np.asarray(img), flag)
    def getDistance(self,img: Image.Image, slice: Image.Image):
        grayImg = self.pilImgToCv2(img, cv2.COLOR_BGR2GRAY)
        graySlice = self.pilImgToCv2(slice, cv2.COLOR_BGR2GRAY)
        grayImg = cv2.Canny(grayImg, 255, 255)
        graySlice = cv2.Canny(graySlice, 255, 255)
        result = cv2.matchTemplate(grayImg, graySlice, cv2.TM_CCOEFF_NORMED)
        maxLoc = cv2.minMaxLoc(result)[3]
        distance = maxLoc[0]
        sliceHeight, sliceWidth = graySlice.shape[:2]
        x, y = maxLoc
        x2, y2 = x + sliceWidth, y + sliceHeight
        resultBg = self.pilImgToCv2(img, cv2.COLOR_RGB2BGR)
        cv2.rectangle(resultBg, (x, y), (x2, y2), (0, 0, 255), 2)
        return distance
    def captcha(self, verify_data):
        detail=json.loads(verify_data)["detail"]
        params = {
            "aid": "2329",
            "lang": "zh",
            "subtype": "slide",
            "detail": detail,
            "server_sdk_env": "{\"idc\":\"lf\",\"region\":\"CN\",\"server_type\":\"passport\"}",
            "mode": "slide",
            "did": self.did,
            "device_id":  self.did,
            "os_name": "android",
            "platform": "app",
            "os_type": "0",
            "h5_sdk_version": "3.5.68",
            "webdriver": "undefined",
            "tmp": str(int(time.time() * 1000)),
            "verify_host": "https://verify.zijieapi.com/",
            "app_name": "douyin_lite",
            "locale": "zh_CN",
            "ch": "xiaomi_2329_64_1104",
            "channel": "xiaomi_2329_64_1104",
            "iid":  self.iid,
            "vc": "32.8.0",
            "app_verison": "32.8.0",
            "region": "cn",
            "use_native_report": "1",
            "use_jsb_request": "1",
            "verify_cancellable": "0",
            "orientation": "2",
            "resolution": "1080*2167",
            "sdk_version": "3.7.4.cn",
            "os_version": "30",
            "device_brand": "Redmi",
            "device_model": "M2103K19C",
            "version_code": "320801",
            "version_name": "32.8.0",
            "device_type": "M2103K19C",
            "device_platform": "android",
            "use_dialog_size_v2": "1",
            "verify_data": verify_data
        }
        url=self._get_url+ parse.urlencode(params)
        for i in range(10):
            try:
                response = requests.get(url=url, headers=self._headers, proxies=self.proxy).json()
                break
            except Exception as e:
                logger.error(f"获取验证码失败，重试中{i}/10,错误信息：{e}")
        else:
            raise RetryException("ip异常，重试")
        content = response['data']
        for i in range(10):
            try:
                print(content)
                binary_ct = BytesIO(requests.get(content['question']['url2'],proxies=self.proxy).content)
                binary_bg = BytesIO(requests.get(content['question']['url1'],proxies=self.proxy).content)
                break
            except Exception as e:
                logger.error(f"获取验证码失败，重试中{i}/10,错误信息：{e}")
        else:
            raise RetryException("ip异常，重试")
        res = self.getDistance(Image.open(binary_bg), Image.open(binary_ct))
        x = res
        y = content['question']['tip_y']
        time.sleep(1)
        logger.info(f"滑动的距离为: {int(x / 110 * 57)}, 高度为: {y}")
        jl = int(x / 110 * 57)
        tt = round(time.time() * 1000)
        gj = self.get_tracks(jl, y,tt)
        t = tt - 3000
        reply = gj["reply"]
        moveArr = gj["moveArr2"]
        m={
        "modified_img_width": 287.04,
        "id": content['id'],
        "mode": "slide",
        "MMtJ2Xt": reply,
        "JKWR": [],
        "v7VR5s": {
            "6Jbg": {},
            "MYE": {},
            "AREm": [],
            "vCystNSrL": [],
            "pkxVs4vwG": moveArr,
            "G1uH": []
        },
        "env": {
            "canvas_hash": "68e2c3f16e1f4016496c31a45cca97a3",
            "webgl_hash": "28cd3f71f1de1e66e4ec647400f8c72b",
            "font_hash": "f325d5fa030cfb5364b42f869b1eca81ad17",
            "audio_hash": "143.08072766105033",
            "time_offset": -480,
            "time_zone": "Asia/Shanghai",
            "languages": [
                "zh-CN"
            ],
            "plugins": [],
            "platform": "Linux aarch64",
            "max_touch_points": 5,
            "webdriver": False,
            "touch_actions": [
                "5,1"
            ],
            "mouse_actions": [],
            "device": {
                "model": "M2103K19C",
                "vendor": "Xiaomi"
            },
            "os": {
                "name": "Android",
                "version": "11"
            },
            "browser": {
                "name": "Chrome WebView",
                "version": "126.0.6478.71"
            },
            "engine": {
                "name": "Blink",
                "version": "126.0.6478.71"
            },
            "gpu": {
                "vendor": "ARM",
                "renderer": "Mali-G57 MC2"
            },
            # "fps": 60,
            "resolution": "393,873",
            "browser_size": "312,316",
            "page_size": "312,316",
            "captcha_origin": "0,0",
            "captcha_size": "312, 316",
            "mask_time": round(time.time() * 100000) - 14000,
            "loading_time": t - 14000,
            "ready_time": t - 12000,
            "detectors": {
                "RegToString": {
                    "enabled": False,
                    "value": 0
                },
                "DefineId": {
                    "enabled": True,
                    "value": 0
                },
                "DateToString": {
                    "enabled": True,
                    "value": 0
                },
                "FuncToString": {
                    "enabled": True,
                    "value": 0
                },
                "Debugger": {
                    "enabled": False,
                    "value": 0
                },
                "Performance": {
                    "enabled": True,
                    "value": 0
                },
                "DebugLib": {
                    "enabled": True,
                    "value": 0
                }
            },
            "sensor": {
                "code": 1,
                "func": "bytedcert.getSensor",
                "__msg_type": "callback",
                "data": {
                    "s": {
                        "ka": True,
                        "cb": True,
                        "ef": True,
                        "ve": True,
                        "a": True,
                        "b": [],
                        "c": []
                    },
                    "ae": [],
                    "be": [],
                    "qs": [],
                    "qa": [
                    ]
                }
            }
        },
        "a": 49,
        "b": 45
    }
        captchaBody = self.captcha_encrypt(m)
        params["tmp"] = str(int(time.time() * 1000))
        params["xx-tt-dd"] = 'qJI7ttpVdGKKbSBvYqmaf0aPo'
        url = self._verify_url + parse.urlencode(params)
        payload = {
            'captchaBody': captchaBody
        }
        for i in range(10):
            try:
                result = requests.post(url, json=payload, headers=self._headers, proxies=self.proxy).json()
                return result
            except Exception as e:
                logger.error(f"获取验证码失败，重试中{i}/10,错误信息：{e}")
        else:
            raise RetryException("ip异常，重试")

    def get_tracks(self, distance, _y, tt):
        """
        生成滑动轨迹
        """
        tracks = list()
        tracks_1 = list()
        y, v, t, current = 0, 0, 1, 0

        mid = distance * 3 / 4

        exceed = random.randint(40, 90)
        z = random.randint(100, 130)
        mdjl = int(random.randint(50, 60))
        md_y = int(random.randint(240, 330))
        tracks_1.append([mdjl, y, tt])
        while current < distance:
            if current < mid / 2:
                a = 2
            elif current < mid:
                a = 3
            else:
                a = -3
            a /= 2
            v0 = v
            s = random.choice([1, 2])
            current += int(s)
            v = v0 + a * t

            y += random.randint(-3, 3)
            z = z + random.randint(0, 8)
            tracks.append([min(current, (distance + exceed)), y, z])
            tracks_1.append([mdjl + min(current, (distance + exceed)), y, tt + z])

        # while exceed > 0:
        #     exceed -= random.choice([1, 1])
        #     y += random.randint(-3, 3)
        #     z = z + random.randint(5, 9)
        #     tracks.append([min(current, (distance + exceed)), y, z])
        #     tracks_1.append([mdjl + min(current, (distance + exceed)), y, tt + z])
        tr = []
        md = []
        for i, x in enumerate(tracks):
            tr.append({
                'x': x[0],
                'y': _y,
                'relative_time': x[2]
            })
        for i, x in enumerate(tracks_1):
            md.append({
                'x': x[0],
                'y': md_y,
                'time': x[2],
                't': 1
            })
        reply2 = []
        moveArr2 = []
        reply2.append(tr[0])
        moveArr2.append(md[0])
        d = 0
        for i in range(len(tr)):
            d += 2
            if d >= len(tr):
                reply2.append(tr[len(tr) - 1])
                moveArr2.append(md[len(md) - 1])
                break
            else:
                reply2.append(tr[d - 1])
                moveArr2.append(md[d - 1])
        data = {
            'reply': tr,
            'reply2': reply2,
            'moveArr': md,
            'moveArr2': moveArr2
        }
        # logger.info(data)
        return data
    def get_tracks1(self,distance, _y):
        """
        生成滑动轨迹
        """
        tracks = list()
        y, v, t, current = 0, 0, 1, 0

        mid = distance * 3 / 4

        exceed = random.randint(40, 90)
        z = random.randint(30, 150)

        while current < (distance + exceed):
            if current < mid / 2:
                a = 2
            elif current < mid:
                a = 3
            else:
                a = -3
            a /= 2
            v0 = v
            s = v0 * t + 0.5 * a * (t * t)
            current += int(s)
            v = v0 + a * t

            y += random.randint(-3, 3)
            z = z + random.randint(5, 10)
            tracks.append([min(current, (distance + exceed)), y, z])

        while exceed > 0:
            exceed -= random.randint(0, 5)
            y += random.randint(-3, 3)
            z = z + random.randint(5, 9)
            tracks.append([min(current, (distance + exceed)), y, z])
        tr = []
        for i, x in enumerate(tracks):
            tr.append({
                'x': x[0],
                'y': _y,
                'relative_time': x[2]
            })
        return tr
    def captcha_encrypt(self,data):
        v8 = json.dumps(data, separators=(',', ':')).encode()
        v11 = SHA512.new(v8).digest() + v8
        slat = ''.join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", k=32))
        v12 = SHA512.new(bytes.fromhex(SHA512.new(slat.encode()).hexdigest() + "3c032864bb1f8479f92da1b57aa0553f36bb1ed83b2eab6c7ac9e8b08b50d518f444d4b6d2261f158b2ad27a72f804f058fcb31ba1404cdf78f63cb80ed86290")).hexdigest()
        crypto = AES.new(key=bytes.fromhex(v12[:64]), mode=AES.MODE_GCM, nonce=bytes.fromhex(v12[64:88]))
        ciphertext, mac = crypto.encrypt_and_digest(v11)
        return base64.b64encode(bytes([116, 99, 6, 16, 0, 0]) + slat.encode() + ciphertext + mac).decode()

# data = r'''{"code":"10000","from":"shark_admin","type":"verify","version":"1","region":"cn","subtype":"slide","ui_type":"","detail":"inxgRiM132L3jyldeIHG6DzKp2TDsnWPPyxw0UtjjURJbzGYp4sgueDuggMS6gEOf6N*jS1Wt3SYtowf7ojSpdLAa2UMCs6I1pyXe7SMoQLUWij6XAQynhvCET3BU8gxtJMF7Cl4Ny0jmUVp7KvCiQYiUeWPR5mJMOgCjcA36s*iP2x9hVH6zRWeohtfahTDkjeET8VGz9psMfyiRMYgSd4C2jALYLzVaQNRGzSaYhWXEI1zk7rjkApu-dnerEQ4BBD1l1FXIv6bPF4MsSZX*au04ul2oi20io1gnNMFFqqF2uD7Gbm4s*sehPkSQoZs856V9nClZZUsU1LSQ8IPR*hNmw0*245LJjCiSTUgq2S1KHzJdD2AsyJAA0lArgV*eljHGz5uFTjaAwQKMaqEA1muNsQdKnmls*umgWJJMvUn3NLsV7D2P49nKZh99kMfAPN3LsKxTeKkU5uxg4LfUkuGEAPOczCauyIoaSnj6Q..","verify_event":"tt_find_account_entrance","fp":"verify_m90235ie_xCvVjWA4_j9u5_4sQ2_BXDt_088ZhyJuvogI","server_sdk_env":"{\"idc\":\"hl\",\"region\":\"CN\",\"server_type\":\"passport\"}","log_id":"2025040223023785455DA0D2EC61164E8B","is_assist_mobile":false,"is_complex_sms":false,"identity_action":"","identity_scene":"","verify_scene":"passport","login_status":0,"aid":0}'''
# print(json.loads(data))
# result = VerifyAweme("","").captcha(data)
# print(result)