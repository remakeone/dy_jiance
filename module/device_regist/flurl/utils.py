import secrets
import uuid
import json
import hashlib
import gzip
import random
import time
import urllib
import requests


from http.cookies import SimpleCookie

requests.packages.urllib3.disable_warnings()

def UUID():
    return str(uuid.uuid4())

def md5(message):
    if isinstance(message, str):
        # 将字符串编码为字节集
        message = message.encode()
    md5_hash = hashlib.md5()
    md5_hash.update(message)
    return md5_hash.hexdigest()

def generate_random_mac():
    """生成随机的 MAC 地址"""
    mac = [0x00, 0x16, 0x3e]  # 前三位固定为私有地址
    mac += [random.randint(0x00, 0x7f) for _ in range(3)]  # 中间三位
    mac += [random.randint(0x00, 0xff) for _ in range(3)]  # 后三位
    return ':'.join(f'{byte:02x}' for byte in mac)


def generate_android_id():
    return secrets.token_bytes(8).hex()

def gzip_compress(buff):
    return gzip.compress(buff)

def rand_str(length):
    rand = ''
    random_str = '0123456789abcdef'
    for _ in range(length):
        rand += random.choice(random_str)
    return rand


def fix_json(json_string):
    json_string = json_string.replace('"', '\\"')
    json_string = json_string.replace("'", "\"")

    return json_string


def get_trace_id(aid: str, device_id: str):
    timestamp = "%x" % (round(time.time() * 1000) & 0xffffffff)

    if device_id == "":
        device_str = rand_str(16)
    else:
        device_str = hex(int(device_id))[2:]

    aid_str = hex(int(aid))[2:]
    random_str = str(timestamp) + "10" + device_str + rand_str(2) + "0" + aid_str
    trace_id = f"00-{random_str}-{random_str[:16]}-01"
    return trace_id


def to_query_str(query_dict: dict):
    return urllib.parse.urlencode(query_dict)


def printf(text: str, log=False):
    print(text)
    file = 'log.txt'
    if log:
        with open(file, 'a+') as f:
            f.write(f'{text}\n\n')
            f.close()


def cookie_string(json_cookie):
    c_str = "; ".join([f"{key}={value}" for key, value in json_cookie.items()])
    return c_str

def cookie_json(response):
    cookie_string   = response.cookies
    cookies         = SimpleCookie()
    cookies.load(cookie_string)
    cookies_dict    = {key: morsel.value for key, morsel in cookies.items()}
    return cookies_dict
