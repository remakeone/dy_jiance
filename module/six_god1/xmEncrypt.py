import base64
import hashlib
import struct

from Crypto.Util.Padding import pad
from gmssl import sm3
from dyMd5 import dyMd5
import dy26_pb2
from dyAES import AES128_CBC_encrypt_buffer


def NOT(num):
    return ~num&0xffffffff

def checksum(result):
    count = 0
    for i in result:
        count += i
    return count & 0xff


def rotate_left_byte(data, shift):
    shift %= 8
    return (((data << shift) & 0xff) | (data >> (8 - shift))) & 0xff


def rotate_right__byte(data, shift):
    shift %= 8
    return (((data >> shift) & 0xff) | (data << (8 - shift))) & 0xff

def parseOneByte(b, b1, b2):
    tmp1 = rotate_right__byte(b, 2)
    tmp2 = ((b1 + tmp1) ^ (~b2)) & 0xff
    tmp3 = rotate_left_byte(tmp2, 5)
    return ((b2 + tmp3) ^ (~b1)) & 0xff


def xmAlog(arr, key):
    arr = bytearray(arr)
    result = []
    for n, i in enumerate(arr):
        index = (n % 8) * 4
        b1, b2 = key[index], key[index+1]
        ret = parseOneByte(i, b1, b2)
        result.append(ret)
    result = result[::-1]
    a = result[-2]
    b = result[-1]
    c = result[0]
    tmp1 = (b ^ NOT(a)) & 0xff
    result[0] = (tmp1 + c) & 0xff

    a = result[-1]
    b = result[0]
    c = result[1]
    result[1] = ((a ^ b ^ 0xfe) + c) & 0xff

    for i in range(2, len(result) - 1):
        k = result[i - 2] ^ ((result[i - 1] & 0x80 != 0) | (2 * result[i - 1] & 0xff))
        s = result[i] + (k ^ NOT(i)) & 0xff
        result[i] = s

    result[-1] = result[-1] ^ result[-2]
    result[0] = ((result[0] ^ result[1]) + checksum(result[1:])) & 0xff
    return bytearray(result)

def sm3_hash(message: bytes):
    msg_list = [i for i in message]
    hash_hex = sm3.sm3_hash(msg_list)
    hash_bytes = bytes.fromhex(hash_hex)
    return hash_bytes

def generatePbData(xk, app_info, url, stub):
    querySm3 = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))
    xmData = dy26_pb2.XM()
    xmData.magic = b'6l\225l5rZ\233\344\324\035e\310\270y&'
    xmData.version = 4
    xmData.rand = 1220
    xmData.msAppID = app_info['aid']
    xmData.deviceID = app_info['device_id']
    xmData.licenseID = "1588093228"
    xmData.appVersion = app_info['app_version']
    xmData.sdkVersionStr = "v04.05.00-ml-android"
    xmData.sdkVersion = 134873088
    xmData.envCode = bytes.fromhex("0000000000000000")
    xmData.createTime = xk * 2
    xmData.bodyHash = bytes.fromhex(dyMd5(querySm3+stub+xk.to_bytes(4, byteorder='little')+bytes.fromhex("8496779dd4150bf8a0010000"))) + bytes.fromhex("00000000")
    xmData.queryHash = querySm3[:6]
    xmData.algorithmCount.signCount = 1872
    xmData.algorithmCount.reportCount = 10
    xmData.algorithmCount.settingCount = 1388734
    xmData.secDeviceToken = "DG-fdsgdfg-ffhdhf"
    xmData.isAppLicense = xk * 2
    xmData.pskVersion = "none"
    xmData.callType = 624
    print("[iOS] xmData V1>>>", xmData.SerializeToString())
    return xmData.SerializeToString()


def get_xm_enc(url, xk, stub, app_info):
    pbInput = generatePbData(xk, app_info, url, stub)
    query_sm3_1st_byte = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))[0]
    if len(stub) == 0:
        stub = bytes(16)
    stub_1st_byte = sm3_hash(stub)[0]
    rrr = 0x10000000
    randBytes = struct.pack("<I", rrr)
    randBytes2 = struct.pack("<I", 0x10000000)
    highRand = randBytes[2:]
    lowRand = randBytes[:2]
    sign_key = "jr36OAbsxc7nlCPmAp7YJUC8Ihi7fq73HLaR96qKovU="
    xmKey = [0] * 68
    xmKey[0:32] = base64.b64decode(sign_key)
    xmKey[32:36] = bytes(lowRand + highRand)
    xmKey[36:68] = base64.b64decode(sign_key)
    xmKey = sm3_hash(bytes(xmKey))
    encryptData = xmAlog(pbInput, xmKey)[::-1]
    random_1st = rrr
    randomArray = bytearray(4)
    randomArray[0] = (random_1st >> 0) & 0xFF
    randomArray[1] = (random_1st >> 8) & 0xFF
    randomArray[2] = (random_1st >> 16) & 0xFF
    randomArray[3] = (random_1st >> 24) & 0xFF

    xor_randomArray = bytearray(4)
    xor_randomArray[0] = (random_1st >> 0) & 0xFF
    xor_randomArray[1] = (random_1st >> 8) & 0xFF
    xor_randomArray[2] = (random_1st >> 16) & 0xFF
    xor_randomArray[3] = (random_1st >> 24) & 0xFF

    x8 = xor_randomArray[2] << 0xb
    x8 = x8 ^ xor_randomArray[3]
    x10 = xor_randomArray[2] >> 0x5
    x10 = x10 ^ x8
    x8 = xor_randomArray[2] ^ x10
    x8 = x8 & 0xffffffff
    xor1 = bytes.fromhex(hex(~x8 & 0xffffffff).replace("0x", ""))
    encryptData += bytes(8)
    tmp1 = bytearray()

    for n, i in enumerate(encryptData):
        tmp1.append(i ^ xor1[(n % 4)])

    tmp1 += highRand
    query_sm3_1st_byte = query_sm3_1st_byte & 0x3f
    stub_1st_byte = stub_1st_byte & 0x3f
    x_reg = 0x18000000
    y_reg = query_sm3_1st_byte << 0xe
    x_reg = x_reg ^ y_reg
    y_reg = stub_1st_byte << 0x8
    x_reg = x_reg ^ y_reg
    x_reg = x_reg ^ 0x1
    x_reg = x_reg & 0xffffffff
    append_array = bytearray([
        (x_reg >> 0) & 0xFF,
        (x_reg >> 8) & 0xFF,
        (x_reg >> 16) & 0xFF,
        (x_reg >> 24) & 0xFF,
    ])
    tmp1 = bytes.fromhex("35") + randBytes2 + append_array + tmp1
    aes_key = hashlib.md5(base64.b64decode(sign_key)[0:16]).digest()
    aes_iv = hashlib.md5(base64.b64decode(sign_key)[16:32]).digest()
    aesKey = []
    xors = [0x39, 0x35, 0x33, 0x43]
    for n, i in enumerate(aes_key):
        aesKey.append(i ^ xors[(n % 4)])
    aesKey = bytes(aesKey)
    aesIv = aes_iv
    aesInput = pad(tmp1, 16)
    aesLength = len(aesInput)
    output = [0] * aesLength
    AES128_CBC_encrypt_buffer(output, bytearray(aesInput), aesLength, aesKey, aesIv)
    result = bytearray(output)
    #print(result.hex())
    last_append_input_str = 'AgAAADZslWw1clqb5NQdZci4eSY='
    last_append_input = base64.b64decode(last_append_input_str)
    xk_bytes = xk.to_bytes(4, byteorder='little')
    last_append = bytearray(20)
    for i in range(20):
        last_append[i] = last_append_input[i] ^ xk_bytes[i % 4]

    before_base64 = bytearray(len(last_append) + 2 + len(result))
    before_base64[:20] = last_append
    before_base64[20:22] = lowRand
    before_base64[22:] = result
    return base64.b64encode(before_base64).decode()