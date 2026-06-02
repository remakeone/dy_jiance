import hashlib
import json
import time
import urllib.parse

def init(arg1, arg2,arg3,arg4):
    v8 = [i for i in range(256)]
    v6 = 0
    v10 = 0x100
    v9 = [0x4A, arg3, 0x16, arg2, 0x47, 0x6C, arg4, arg1]
    for i in range(256):
        v2 = v6 + v8[i] + v9[i & 7]
        v6 = v2 - (int(v2 / v10) << 8)
        v7 = v8[v6]
        v8[i] = v7
    return v8
def get20Bytes(Byte4_1, Byte4_2,Byte4_3,v0,key):
    arg0 = int(Byte4_1[0:2],16)
    arg1 = int(Byte4_1[2:4],16)
    arg2 = int(Byte4_1[4:6],16)
    arg3 = int(Byte4_1[6:8],16)
    arg4 = int(Byte4_2[0:2],16)
    arg5 = int(Byte4_2[2:4],16)
    arg6 = int(Byte4_2[4:6],16)
    arg7 = int(Byte4_2[6:8],16)
    arg16 = int(Byte4_3[0:2], 16)
    arg17 = int(Byte4_3[2:4], 16)
    arg18 = int(Byte4_3[4:6], 16)
    arg19 = int(Byte4_3[6:8], 16)
    _list2 = [arg0,arg1,arg2,arg3,arg4,arg5,arg6,arg7,]+key+[arg16,arg17,arg18,arg19]  # 版本
    v5 = 0
    v6 = 0
    v3 = 0x100
    _list1 = []
    for i in range(20):
        v5 = v5 + 1 - (int((v5 + 1) / v3) << 8)
        v7 = v6 + v0[v5]
        v6 = v7 - (int(v7 / v3) << 8)
        v7 = v0[v6]
        v0[v5] = v7
        v0[v6] = v7
        x8 = v0[(v0[v5] + v7) & 0xff]
        _list1.append(x8 ^ _list2[i])
    return _list1
def getXg(khronos,key,params,data,byte8,isPost,isJson):
    query_string = "&".join([f"{key}={value}" if value else key for key, value in params.items()])
    encoded_query_string = urllib.parse.quote_plus(query_string, safe='=&*')
    print("encoded_query_string",encoded_query_string)
    sign = hashlib.md5(encoded_query_string.encode('utf-8')).hexdigest()
    if(isPost):
        if(isJson):
            encoded_data = json.dumps(data,separators=(',', ':')) # json用这个
        else:
            encoded_data = urllib.parse.urlencode(data)  # 表单用这个
        x_ss_stub = hashlib.md5(encoded_data.encode('utf-8')).hexdigest().upper()
    else:
        x_ss_stub = '00000000'
    Byte4_1 = sign[0:8]
    Byte4_2 = x_ss_stub[0:8]
    arg1 = int(byte8[0:2],16)
    arg2 = int(byte8[2:4],16)
    arg3 = int(byte8[4:6],16)
    arg4 = int(byte8[6:8],16)
    _list1 = get20Bytes(Byte4_1, Byte4_2,hex(khronos)[2:],init(arg1,arg2,arg3,arg4),key)
    _str = ''
    for i in range(0, len(_list1)):
        xx = _list1[i]
        v8 = ((xx >> 4) & 0xFFFFF00F | (16 * xx)) & 0xff
        if i == 19:
            a3 = (res0 ^ v8) & 0xff
        else:
            a3 = _list1[i + 1] ^ v8
        v10 = (0xffffffaa & (2 * a3)) | 0x55 & (a3 >> 1)
        v11 = (4 * v10) & 0xFFFFFFCF | 0x33 & (v10 >> 2)
        res = ((((v11 >> 4) & 0xf) | (16 * v11)) ^ 0xffffffeb) & 0xff
        if i == 0:
            res0 = res
        _str += hex(res)[2:] if (len(hex(res)[2:]) == 2) else '0' + hex(res)[2:]
    print('后20字节数据:',_str)
    print('x-gorgon:','8404'+byte8+_str)  # 8404是版本号
    return '8404'+byte8+_str

def query_string_to_dict(query_str):
    """
    将URL查询字符串转换为字典

    Args:
        query_str (str): URL查询参数字符串，例如 "key1=value1&key2=value2"

    Returns:
        dict: 转换后的参数字典
    """
    params = {}
    # 按 & 分割键值对
    pairs = query_str.split('&')
    for pair in pairs:
        # 按 = 分割键和值
        if '=' in pair:
            key, value = pair.split('=', 1)  # 只分割第一个等号
            params[key] = value
    return params


def get_xgorgon(khronos, url, data=""):
    key = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x04]
    params = query_string_to_dict(url.split("?")[1])
    if data:
        isPost = True
        byte8 = 'c0520001'
    else:
        isPost = False
        byte8 = '00220001'
    return getXg(khronos,key,params,data=data,byte8=byte8,isPost=isPost,isJson=False)


if __name__ == '__main__':
    khronos = 1743434587
    params = {
        "aweme_id": "7438333354237267251",
        "origin_type": "web",
        "request_source": "0",
        "is_story": "0",
        "location_permission": "0",
        "aweme_type": "1",
        "recommend_collect_feedback": "0",
        "iid": "3288008589123801",
        "device_id": "3288008589119705",
        "ac": "wifi",
        "channel": "tengxun_1128_1025",
        "aid": "1128",
        "app_name": "aweme",
        "version_code": "190000",
        "version_name": "19.0.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": "2203121C",
        "device_brand": "Xiaomi",
        "language": "zh",
        "os_api": "33",
        "os_version": "13",
        "manifest_version_code": "190001",
        "resolution": "1440*3007",
        "dpi": "560",
        "update_version_code": "19009900",
        "_rticket": "1740576157432",
        "package": "com.ss.android.ugc.aweme",
        "mcc_mnc": "46001",
        "cpu_support64": "true",
        "host_abi": "armeabi-v7a",
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "ts": "1740576156",
        "cdid": "c6f36d27-535c-44b5-a547-287e236e45d7",
        "oaid": "4067ae1c4d619ec8"
    }
    data = {
    }
    # key = [0x00,0x00,0x00,0x00,0x00,0x05,0x05,0x04] # 29.3.0
    # key = [0x00,0x00,0x00,0x00,0x00,0x00,0x06,0x04] # 30.0.0
    # key = [0x00,0x00,0x00,0x00,0x00,0x01,0x06,0x04] # 30.0.2
    key = [0x00,0x00,0x00,0x00,0x00,0x00,0x07,0x04] # 31.9.0
    # 29.3.0和31.9.0 刚刚测过完全正确,30.0.0和30.0.2是之前的,没测试,大概率没问题

    # get 29.3.0
    getXg(khronos,key,params,data='',byte8='404b0000',isPost=False,isJson=False) # post为false,data和isjson不用管

    # post 29.3.0
    getXg(khronos,key,params,data={},byte8='a0c80080',isPost=True,isJson=False) # 表单为空直接传{}

    # post 31.9.0
    getXg(khronos,key,params,data,byte8='c0520001',isPost=True,isJson=False)

    # get 31.9.0
    getXg(khronos,key,params,data='',byte8='00220001',isPost=False,isJson=False) # post为false,data和isjson不用管

# byte8是xg的除掉8404的前8位 前4位取的是malloc返回的地址的后4位的小端序,可地址规则随机,后4位应该是刻在汇编里的,不同情况下走了不同分支,常见的有0000,0001,0080,0081等,直接0000即可
# 0x7224639380  9380
# 0x7224639280  9280
# 0x717a64b840  b840
# 0x717a64bae0  bae0
# 0x7224639380  9380
# 0x7224639280  9280
# 0x717a64bb00  bb00
# 0x717a64bb20  bb20
# 0x7224639380  9380
# 0x7224639280  9280
# 0x717a64bb60  bb60
# 0x717a64bba0  bba0