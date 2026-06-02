from PIL import Image
import math
import hashlib
import urllib
import base64
import random
import json
import time
from pathlib import Path
import PIL
import cv2
import numpy as np
import requests
from Crypto.Cipher import AES
from Crypto.Hash import SHA512
import urllib3

# 禁用所有 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UrlHelper:

    @classmethod
    def url_encode(cls, data, encoding='utf-8', safe='*'):
        _byte = str(data).encode(encoding)
        return urllib.parse.quote(_byte, safe=safe)

    @classmethod
    def url_decode(cls, data, encoding='utf-8'):
        _byte = str(data)
        return urllib.parse.unquote(_byte, encoding)

    @classmethod
    def url_join(cls, data: dict, encode=True, encoding='utf-8', safe=''):
        __url = ''
        for key, value in data.items():
            if encode:
                key = cls.url_encode(key, encoding=encoding, safe=safe)
                value = cls.url_encode(value, encoding=encoding, safe=safe)
            __url += f'&{key}={value}'
        return __url.split('&', 1)[-1]

    @classmethod
    def url_parse(cls, data: str, encoding='utf8', safe=''):
        if '?' in data and '&' in data:
            # params = dict()
            params_str = data.split('?', 1)[-1].split('&')
            return {x.split('=', 1)[0]: cls.url_decode(x.split('=', 1)[1], encoding) for x in params_str}
        else:
            raise ValueError('传入链接中无可切割参数，请检查')


SHA512 = lambda byte_: hashlib.sha512(byte_).hexdigest()

RANDOM_SLAT = lambda: ''.join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", k=32))


def slide_encrypt_gcm(data):
    v8 = json.dumps(data, separators=(',', ':')).encode()
    v11 = hashlib.sha512(v8).digest() + v8
    slat = RANDOM_SLAT()
    v12 = SHA512(bytes.fromhex(SHA512(
        slat.encode()) + '4dd4c2e6b83162090e52b3c7a6733ba41cb2462b829ab58a196b39db57177524f49baf7f08e8d68d26a72e37c1a95a2f1f05a51892aef2949732b62a38aadd58'))
    crypto = AES.new(key=bytes.fromhex(v12[:64]), mode=AES.MODE_GCM, nonce=bytes.fromhex(v12[64:88]))
    ciphertext, mac = crypto.encrypt_and_digest(v11)
    return base64.b64encode(bytes([116, 99, 6, 16, 0, 0]) + slat.encode() + ciphertext + mac).decode()


def elastic_motion(t, start_pos, end_pos, duration, amplitude=None, period=None):
    if t == 0:
        return start_pos
    t = t / (duration / 2)
    if t == 2:
        return start_pos + end_pos
    if not period:
        period = duration * (0.3 * 1.5)
    if not amplitude or amplitude < abs(end_pos):
        amplitude = end_pos
        s = period / 4
    else:
        s = period / (2 * math.pi) * math.asin(end_pos / amplitude)
    if t < 1:
        result = -0.5 * (amplitude * (2 ** (10 * (t - 1))) * math.sin(
            (t * duration - s) * (2 * math.pi) / period)) + start_pos
        return round(result, 15)
    result = amplitude * (2 ** (-10 * (t - 1))) * math.sin(
        (t * duration - s) * (2 * math.pi) / period) * 0.5 + end_pos + start_pos
    return round(result, 15)


def random_int(x, y):
    return round(random.uniform(x, y))


def random_uniform(x, y):
    return random.uniform(x, y)


def generate_motion_track(start_pos):
    scales = [[0.04, 0.15, 0.40, 0.76, 0.88, 0.98], [0.05, 0.20, 0.40, 0.78, 0.88, 0.98],
              [0.04, 0.20, 0.50, 0.70, 0.85, 0.98], [0.06, 0.24, 0.47, 0.80, 0.92, 0.98],
              [0.08, 0.22, 0.43, 0.79, 0.89, 0.97]]
    scale = scales[random_int(0, 4)]
    motion_track = []
    slide_rate = 1 if start_pos / 50 < 1.5 else round(start_pos / 50)
    track_length = random_int(start_pos, round(start_pos * slide_rate * 1.2))
    if slide_rate > 2: track_length = round(start_pos * random_uniform(1.2, 1.5))
    t = 0
    t_increment = 0
    for i in range(track_length):
        x = math.ceil(elastic_motion(i, 0, start_pos, track_length))
        if x <= 0:
            continue
        if motion_track and x < motion_track[-1]['x']:
            continue
        a = random_uniform(0, 1)
        if x > start_pos: x = start_pos
        if x < 1:
            t_increment = random_uniform(0, 23)
        elif x < start_pos * scale[0]:
            if a < 0.8:
                t_increment = random_uniform(2, 10)
            else:
                t_increment = random_uniform(2, 15)
        elif x < start_pos * scale[1]:
            if a < 0.6:
                t_increment = random_uniform(3, 10)
            else:
                t_increment = random_uniform(3, 15)
        elif x < start_pos * scale[2]:
            if a < 0.5:
                t_increment = random_uniform(4, 11)
            else:
                t_increment = random_uniform(4, 16)
        elif x < start_pos * scale[3]:
            if a < 0.4:
                t_increment = random_uniform(4, 13)
            else:
                t_increment = random_uniform(4, 16)
        elif x < start_pos * scale[4]:
            if a < 0.3:
                t_increment = random_uniform(4, 17)
            else:
                t_increment = random_uniform(23, 39)
        elif x < start_pos * scale[5]:
            if a < 0.2:
                t_increment = random_uniform(4, 23)
            else:
                t_increment = random_uniform(17, 23)
        else:
            if a < 0.2:
                t_increment = random_uniform(4, 23)
            else:
                t_increment = random_uniform(17, 23)
        t += t_increment
        motion_track.append({'x': x, 't': math.ceil(t), })
        if x >= start_pos:
            break
    return motion_track


def encrypt(id, img_width, img_height):
    motion_track = generate_motion_track(img_width)
    i = 0
    motion_params = []
    while True:
        data = motion_track[i]
        if data["x"] >= img_width:
            break
        i += 1
        motion_params.append({"x": data["x"], "y": img_height, "relative_time": data["t"]})
    motion_params.append({"x": img_width, "y": img_height, "relative_time": motion_params[-1]["relative_time"] + 10})
    motion_obj = {"modified_img_width": 340, "id": id, "mode": "slide", "reply": motion_params, "detRes": 520}
    return slide_encrypt_gcm(motion_obj)

def imshow(img, winname='test', delay=0):
    """cv2展示图片"""
    cv2.imshow(winname, img)
    cv2.waitKey(delay)
    cv2.destroyAllWindows()


def pil_to_cv2(img):
    """
    pil转cv2图片
    :param img: pil图像, <type 'PIL.JpegImagePlugin.JpegImageFile'>
    :return: cv2图像, <type 'numpy.ndarray'>
    """
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    return img


def bytes_to_cv2(img):
    """
    二进制图片转cv2
    :param img: 二进制图片数据, <type 'bytes'>
    :return: cv2图像, <type 'numpy.ndarray'>
    """
    # 将图片字节码bytes, 转换成一维的numpy数组到缓存中
    img_buffer_np = np.frombuffer(img, dtype=np.uint8)
    # 从指定的内存缓存中读取一维numpy数据, 并把数据转换(解码)成图像矩阵格式
    img_np = cv2.imdecode(img_buffer_np, 1)
    return img_np


def cv2_open(img, flag=None):
    """
    统一输出图片格式为cv2图像, <type 'numpy.ndarray'>
    :param img: <type 'bytes'/'numpy.ndarray'/'str'/'Path'/'PIL.JpegImagePlugin.JpegImageFile'>
    :param flag: 颜色空间转换类型, default: None
        eg: cv2.COLOR_BGR2GRAY（灰度图）
    :return: cv2图像, <numpy.ndarray>
    """
    if isinstance(img, bytes):
        img = bytes_to_cv2(img)
    elif isinstance(img, (str, Path)):
        img = cv2.imread(str(img))
    elif isinstance(img, np.ndarray):
        img = img
    elif isinstance(img, PIL.Image):
        img = pil_to_cv2(img)
    else:
        raise ValueError(f'输入的图片类型无法解析: {type(img)}')
    if flag is not None:
        img = cv2.cvtColor(img, flag)
    return img


def get_distance(bg, tp, im_show=False, save_path=None):
    """
    :param bg: 背景图路径或Path对象或图片二进制
        eg: 'assets/bg.jpg'
            Path('assets/bg.jpg')
    :param tp: 缺口图路径或Path对象或图片二进制
        eg: 'assets/tp.jpg'
            Path('assets/tp.jpg')
    :param im_show: 是否显示结果, <type 'bool'>; default: False
    :param save_path: 保存路径, <type 'str'/'Path'>; default: None
    :return: 缺口位置
    """
    # 读取图片
    bg_img = cv2_open(bg)
    tp_gray = cv2_open(tp, flag=cv2.COLOR_BGR2GRAY)

    # 金字塔均值漂移
    bg_shift = cv2.pyrMeanShiftFiltering(bg_img, 5, 50)

    # 边缘检测
    tp_gray = cv2.Canny(tp_gray, 255, 255)
    bg_gray = cv2.Canny(bg_shift, 255, 255)

    # 目标匹配
    result = cv2.matchTemplate(bg_gray, tp_gray, cv2.TM_CCOEFF_NORMED)
    # 解析匹配结果
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    distance = max_loc[0]
    if save_path or im_show:
        # 需要绘制的方框高度和宽度
        tp_height, tp_width = tp_gray.shape[:2]
        # 矩形左上角点位置
        x, y = max_loc
        # 矩形右下角点位置
        _x, _y = x + tp_width, y + tp_height
        # 绘制矩形
        bg_img = cv2_open(bg)
        cv2.rectangle(bg_img, (x, y), (_x, _y), (0, 0, 255), 2)
        # 保存缺口识别结果到背景图
        if save_path:
            save_path = Path(save_path).resolve()
            save_path = save_path.parent / f"{save_path.stem}.{distance}{save_path.suffix}"
            save_path = save_path.__str__()
            cv2.imwrite(save_path, bg_img)
        # 显示缺口识别结果
        if im_show:
            imshow(bg_img)
    return distance
class SlideCrack(object):
    def __init__(self, front, bg, out=None):
        self.front = front
        self.bg = bg
        self.out = out

    @staticmethod
    def clear_white(img):
        img = cv2.imdecode((np.frombuffer(img, np.uint8)), cv2.IMREAD_COLOR)
        rows, cols, channel = img.shape
        min_x = 255
        min_y = 255
        max_x = 0
        max_y = 0
        for x in range(1, rows):
            for y in range(1, cols):
                t = set(img[x, y])
                if len(t) >= 2:
                    if x <= min_x:
                        min_x = x
                    elif x >= max_x:
                        max_x = x
                    if y <= min_y:
                        min_y = y
                    elif y >= max_y:
                        max_y = y
        img1 = img[min_x:max_x, min_y: max_y]
        return img1

    def template_match(self, tpl, target):
        th, tw = tpl.shape[:2]
        result = cv2.matchTemplate(target, tpl, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        tl = max_loc
        br = (tl[0] + tw, tl[1] + th)
        cv2.rectangle(target, tl, br, (0, 0, 255), 2)
        if self.out:
            cv2.imwrite(self.out, target)
        return tl[0]

    @staticmethod
    def image_edge_detection(img):
        edges = cv2.Canny(img, 100, 200)
        return edges

    def discern(self):
        img1 = self.clear_white(self.front)
        img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        slide = self.image_edge_detection(img1)

        back = cv2.imdecode((np.frombuffer(self.bg, np.uint8)), cv2.COLOR_RGB2GRAY)
        back = self.image_edge_detection(back)

        slide_pic = cv2.cvtColor(slide, cv2.COLOR_GRAY2RGB)
        back_pic = cv2.cvtColor(back, cv2.COLOR_GRAY2RGB)
        x = self.template_match(slide_pic, back_pic)
        return int(x)


def time_13():
    return str(int(time.time() * 1000))


class ByteDanceCaptchaIos(object):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrom'
                      'e/91.0.4472.164 Safari/537.36',
        'referer': 'https://www.douyin.com/',
        'origin': 'https://www.douyin.com'
    }

    def __init__(self, did, iid, detail, proxy=None, server_sdk_env=None):
        self.fg = 'images/tiktok_fg.png'
        self.bg = 'images/tiktok_bg.png'
        self.session = requests.session()
        self.session.proxies = proxy
        self.fg_byte = None
        self.bg_byte = None
        self.config = {
            'did': did,
            'detail': detail,
            'iid': iid,
            'mode': 'slide',
            'server_sdk_env': '{"idc":"lf","region":"CN","server_type":"passport"}' if not server_sdk_env else server_sdk_env
        }

    def download_img(self, img_url):
        __res = self.session.get(img_url, headers=self.headers, proxies=None, timeout=30, verify=False)
        # print('下载图片：{}'.format(img_url))
        return __res.content
        # with open(img_name, 'wb') as fw:
        #     fw.write(__res.content)

    def _params(self):
        params = {
            "lang": "zh",
            "app_name": "novel_fm",
            "h5_sdk_version": "2.28.0",
            "h5_sdk_use_type": "cdn",
            "sdk_version": "3.5.0.cn",
            "iid": self.config['iid'],
            "did": self.config['did'],
            "device_id": self.config['did'],
            "ch": "xiaomi_3040_64",
            "aid": "3040",
            "os_type": "0",
            "mode": "slide",
            "tmp": time_13(),
            "platform": "app",
            "webdriver": "undefined",
            "verify_host": "https://verify.zijieapi.com/",
            "locale": "zh_CN",
            "channel": "xiaomi_3040_64",
            "app_key": "",
            "vc": "4.6.5.32",
            "app_verison": "4.6.5.32",
            "session_id": "",
            "region": "cn",
            "use_native_report": "1",
            "use_jsb_request": "1",
            "orientation": "2",
            "resolution": "1080*1920",
            "os_version": "27",
            "device_brand": "Xiaomi",
            "device_model": "MI 6",
            "os_name": "android",
            "version_code": "465",
            "version_name": "4.6.5.32",
            "device_type": "MI 6",
            "device_platform": "android",
            "use_dialog_size_v2": "1",
            "app_version": "4.6.5.32",
            "type": "verify",
            "detail": self.config['detail'],
            "server_sdk_env": "{\"idc\":\"lf\",\"region\":\"CN\",\"server_type\":\"passport\"}",
            "subtype": "slide",
            "challenge_code": "99999",
            "ac": "wifi",
            "os": "android",
            "ssmix": "a",
            "language": "zh",
            "os_api": "27",
            # "openudid": "f9f311f46041db09",
            "manifest_version_code": "465",
            "dpi": "480",
            "update_version_code": "46533",
            "_rticket": time_13(),
            "gender": "2",
            "need_personal_recommend": "1",
            "comment_tag_c": "5",
            "vip_state": "0",
            "category_style": "1",
            # "ab_sdk_version": "4855051,4917458,5024597,5241854",
            # "rom_version": "OPM7.181205.001 release-keys",
            "cdid": "d531ade1-b793-4c76-bded-6e992bd78cc0",
            # "uuid": "61031127649"
        }
        params = {
            "device_id": self.config['did'],
            "os_version": "15.0",
            "device_model": "iPhone14,2",
            "platform": "app",
            "iid": self.config['iid'],
            "did": self.config['did'],
            "app_name": "aweme",
            "locale": "zh_CN",
            "sdk_version": "3.5.0",
            "lang": "zh",
            "mode": "",
            "challenge_code": "3058",
            "detail": self.config['detail'],
            "vc": "24.4.0",
            "type": "verify",
            "orientation": "2",
            "h5_sdk_use_type": "cdn",
            "os_type": "1",
            "version_code": "24.4.0",
            "channel": "App Store",
            "tmp": time_13(),
            "os_name": "iOS",
            "verify_host": "https://verify.zijieapi.com/",
            "webdriver": "false",
            "device_brand": "iPhone",
            "back_up_host": "https://verify.snssdk.com/",
            "device_platform": "iphone",
            "ch": "App Store",
            "use_native_report": "1",
            "server_sdk_env": "{\"idc\":\"lq\",\"region\":\"CN\",\"server_type\":\"whale\"}",
            "aid": "1128",
            "h5_sdk_version": "2.28.4",
            "use_jsb_request": "1",
            "appkey": "",
            "subtype": "slide",
            "app_version": "24.4.0",
            "resolution": "750*1334",
            "appTheme": "light",
            "need_personal_recommend": "1",
            "js_sdk_version": "2.81.1.8",
            "tma_jssdk_version": "2.81.1.8",
            "mcc_mnc": "46001",
            "minor_status": "0",
            "screen_width": "750",
            "cdid": "10F8B1AF-5442-4E3A-BF1B-125D47D897B2",
            "os_api": "18",
            "ac": "",
            "package": "com.ss.iphone.ugc.Aweme",
            "build_number": "244020",
            "is_vcd": "1",
            "device_type": "iPhone14,2",
            "is_guest_mode": "0"
        }
        return params

    def register_captcha(self):
        _url = 'https://verify.zijieapi.com/captcha/get'
        _params = self._params()
        _params['challenge_code'] = '3058'
        _params['app_name'] = UrlHelper.url_decode(_params['app_name'])
        _url = _url + '?' + UrlHelper.url_join(_params)
        res = self.session.get(_url, headers=self.headers, proxies=self.session.proxies, timeout=30, verify=False)
        json_str = res.json()
        token_id = json_str['data']['id']
        self.config['challenge_id'] = token_id
        self.config['mode'] = json_str['data']['mode']
        # print('注册验证码：{}'.format(token_id))
        if self.config['mode'] == 'slide':
            return self.register_slide(json_str)
        raise ValueError(f'mode is not supposed')

    def register_slide(self, json_str):
        self.bg_byte = self.download_img(json_str['data']['question']['url1'])
        self.fg_byte = self.download_img(json_str['data']['question']['url2'])
        self.config['tip_y'] = json_str['data']['question']['tip_y']

    def verify_slide(self):
        _url = 'https://verify.zijieapi.com/captcha/verify'
        _params = self._params()
        _params['xx-tt-dd'] = 'qJI7ttpVdGKKbSBvYqmaf0aPo'
        _url = _url + '?' + UrlHelper.url_join(_params)
        # dis = SlideCrack(self.fg_byte, self.bg_byte).discern()
        dis = get_distance(
            bg=self.bg_byte,
            tp=self.fg_byte,
            im_show=False,
            save_path=None
        )
        dis_x = int(dis / 552 * 344)
        # print('计算缺口距离：{}, {}'.format(dis, dis_x))
        track_data = {
            'captchaBody': encrypt(self.config['challenge_id'], dis_x, self.config['tip_y'])
        }
        # 有时间验证，不能间隔时间太短
        time.sleep(1)
        res = self.session.post(_url, headers=self.headers, json=track_data, proxies=self.session.proxies, timeout=30, verify=False)
        # print('提交验证：{}'.format(res.text))
        return res.json()

    def verify_track(self):
        self.register_captcha()
        if self.config['mode'] == 'slide':
            return self.verify_slide()
        elif self.config['mode'] == 'text':
            return self.verify_text_click()
        else:
            raise ValueError("mode {} is not allow...".format(self.config['mode']))