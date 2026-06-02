import base64
import binascii
import hashlib
import random
import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from gmssl import sm3

from module.six_god.six_god import dyEncrypt_proto


def sm3_hash(message):
    msg_list = [i for i in message]
    hash_hex = sm3.sm3_hash(msg_list)
    hash_bytes = bytes.fromhex(hash_hex)
    return hash_bytes


def NOT(num):
    return ~num&0xffffffff


def checksum(result):
    count = 0
    for i in result:
        count += i
    return count & 0xff


def rotate_left_byte(data, shift):
    shift %= 8  # 防止shift超过8
    return (((data << shift) & 0xff) | (data >> (8 - shift))) & 0xff


def rotate_right__byte(data, shift):
    shift %= 8  # 防止shift超过8
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


def calc_head0(key):
    sum = 0
    for i in range(32):
        if i & 1 == 0:
            sum = (key[i] ^ (sum << 7) ^ (sum >> 3) ^ sum)&0xffffffff
        else:
            sum = ((key[i] | (sum << 11)) ^ (sum >> 5) ^ sum ^ -1)&0xffffffff
    return sum & 0xFF


def calc_head1(querybody, bodyhash):
    x1 = (querybody & 0x3F) << 0xe
    x2 = (bodyhash & 0x3f) << 0x8
    xxx = (0x18100000 | x1 | x2) & 0xffffffff ^ 1
    output = xxx.to_bytes(4, byteorder="little")
    return output


def get_xa_enc(sourceInfo, url, stub, xk, deviceInfos, callTimes, sign_key, licenseID, lanusk):
    pbInput = generatePbData(xk, sourceInfo, deviceInfos, url, stub, callTimes, licenseID, lanusk)
    query_sm3_1st_byte = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))[0]
    if len(stub) == 0:
        stub = bytes(16)
    else:
        stub = bytes.fromhex(stub.decode())
    stub_1st_byte = sm3_hash(stub)[0]
    rrr = random.randint(0x10000000, 0xFFFFFFFF)
    randBytes = struct.pack("<I", rrr)
    randBytes2 = struct.pack(">I", random.randint(0x10000000, 0xFFFFFFFF))
    highRand = randBytes[2:]
    lowRand = randBytes[:2]
    aes_key = hashlib.md5(base64.b64decode(sign_key)[0:16]).digest()
    aes_iv = hashlib.md5(base64.b64decode(sign_key)[16:32]).digest()
    xaKey = [0] * 68
    xaKey[0:32] = base64.b64decode(sign_key)
    xaKey[32:36] = bytes(lowRand + highRand)
    xaKey[36:68] = base64.b64decode(sign_key)

    xaKey = sm3_hash(bytes(xaKey))
    encryptData = xmAlog(pbInput, xaKey)
    encryptData = encryptData[::-1]

    random_1st = rrr
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
    encryptData += bytes.fromhex("0000000000000000")
    tmp1 = bytearray()

    for n, i in enumerate(encryptData):
        tmp1.append(i ^ xor1[(n % 4)])

    tmp1 += highRand
    append_array = calc_head1(query_sm3_1st_byte, stub_1st_byte)

    magic_num = calc_head0(base64.b64decode(sign_key)).to_bytes(1, 'big')
    tmp1 = magic_num + randBytes2 + append_array + tmp1
    aes = AES.new(key=aes_key, mode=AES.MODE_CBC, iv=aes_iv)
    aesEncryptData = aes.encrypt(pad(tmp1, 16))
    return base64.b64encode(lowRand + aesEncryptData).decode()

def generatePbData(xk, sourceInfo, deviceInfos, url, stub, callTimes, licenseID, lanusk):
    deviceId = deviceInfos["device_id"]
    devicetoken = deviceInfos["devicetoken"]
    aid = sourceInfo["aid"]
    if len(stub) == 0:
        stub = bytes(16)
        pskStub = b"00000000000000000000000000000000"
    else:
        pskStub = stub
        stub = bytes.fromhex(stub.decode())
    xaData = dyEncrypt_proto.XA()
    xaData.magic = 1077940818
    xaData.version = 2
    # IOS
    xaData.platform = 1
    xaData.rand = random.randint(0, 0x7FFFFFFF)
    xaData.msAppID = str(aid)
    xaData.deviceID = deviceId
    xaData.licenseID = licenseID
    xaData.appVersion = sourceInfo["appVersion"]
    xaData.sdkVersionStr = sourceInfo["mssdkVersionStr"]
    xaData.sdkVersion = sourceInfo["mssdkVersionInt"] * 2
    xaData.envCode = bytes.fromhex("0000000000000000")
    xaData.createTime = xk * 2
    xaData.bodyHash = sm3_hash(stub)[:6]
    xaData.queryHash = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))[:6]

    xaData.algorithmCount.signCount = callTimes * 2
    xaData.algorithmCount.reportCount = 1388734
    xaData.algorithmCount.settingCount = 1388734
    xaData.secDeviceToken = devicetoken.encode()
    xaData.isAppLicense = xk * 2
    if lanusk:
        xaData.pskHash = getpsk_hash(lanusk)
        xaData.pskCalHash = get_psk_cal_hash(url.split("?")[1], pskStub.decode())
        xaData.pskVersion = "1"
    else:
        xaData.pskVersion = "none"
    xaData.callType = 738
    return xaData.SerializeToString()


def getpsk_hash(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.digest()

def get_psk_cal_hash(query, stub):
    stubHex = binascii.unhexlify(stub)
    buf = bytearray(query.encode('utf-8')) + stubHex + b'0'
    return sm3_hash(buf)
