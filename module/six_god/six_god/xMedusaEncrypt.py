import base64
import binascii
import hashlib
import random
import struct
from collections import deque

from Crypto.Util.Padding import pad
from gmssl import sm3

from module.six_god.six_god import dyEncrypt_proto
from module.six_god.six_god.byteDanceMd5 import dyMd5
from module.six_god.six_god.byteDanceAES import AES128_CBC_encrypt_buffer


class SimonCipher(object):

    z0 = 0b01100111000011010100100010111110110011100001101010010001011111
    z1 = 0b01011010000110010011111011100010101101000011001001111101110001
    z2 = 0b11001101101001111110001000010100011001001011000000111011110101
    z3 = 0b11110000101100111001010001001000000111101001100011010111011011
    z4 = 0b11110111001001010011000011101000000100011011010110011110001011

    __valid_setups = {32: {64: (32, z0)},
                      48: {72: (36, z0), 96: (36, z1)},
                      64: {96: (42, z2), 128: (44, z3)},
                      96: {96: (52, z2), 144: (54, z3)},
                      128: {128: (68, z2), 192: (69, z3), 256: (72, z4)}}

    __valid_modes = ['ECB', 'CTR', 'CBC', 'PCBC', 'CFB', 'OFB']

    def __init__(self, key, key_size=128, block_size=128, mode='ECB', init=0, counter=0):
        try:
            self.possible_setups = self.__valid_setups[block_size]
            self.block_size = block_size
            self.word_size = self.block_size >> 1
        except KeyError:
            raise

        try:
            self.rounds, self.zseq = self.possible_setups[key_size]
            self.key_size = key_size
        except KeyError:
            raise

        self.mod_mask = (2 ** self.word_size) - 1

        try:
            self.iv = init & ((2 ** self.block_size) - 1)
            self.iv_upper = self.iv >> self.word_size
            self.iv_lower = self.iv & self.mod_mask
        except (ValueError, TypeError):
            raise

        try:
            self.counter = counter & ((2 ** self.block_size) - 1)
        except (ValueError, TypeError):
            raise

        try:
            position = self.__valid_modes.index(mode)
            self.mode = self.__valid_modes[position]
        except ValueError:
            raise

        self.key = int.from_bytes(key, byteorder='little')

        m = self.key_size // self.word_size
        self.key_schedule = []

        k_init = [((self.key >> (self.word_size * ((m - 1) - x))) & self.mod_mask) for x in range(m)]

        k_reg = deque(k_init)

        round_constant = self.mod_mask ^ 3

        for x in range(self.rounds):

            rs_3 = ((k_reg[0] << (self.word_size - 3)) + (k_reg[0] >> 3)) & self.mod_mask

            if m == 4:
                rs_3 = rs_3 ^ k_reg[2]

            rs_1 = ((rs_3 << (self.word_size - 1)) + (rs_3 >> 1)) & self.mod_mask

            c_z = ((self.zseq >> (x % 62)) & 1) ^ round_constant

            new_k = c_z ^ rs_1 ^ rs_3 ^ k_reg[m - 1]

            self.key_schedule.append(k_reg.pop())
            k_reg.appendleft(new_k)

    def encrypt_round(self, x, y, k):
        ls_1_x = ((x >> (self.word_size - 1)) + (x << 1)) & self.mod_mask
        ls_8_x = ((x >> (self.word_size - 8)) + (x << 8)) & self.mod_mask
        ls_2_x = ((x >> (self.word_size - 2)) + (x << 2)) & self.mod_mask

        xor_1 = (ls_1_x & ls_8_x) ^ y
        xor_2 = xor_1 ^ ls_2_x
        new_x = k ^ xor_2

        return new_x, x

    def decrypt_round(self, x, y, k):
        ls_1_y = ((y >> (self.word_size - 1)) + (y << 1)) & self.mod_mask
        ls_8_y = ((y >> (self.word_size - 8)) + (y << 8)) & self.mod_mask
        ls_2_y = ((y >> (self.word_size - 2)) + (y << 2)) & self.mod_mask

        xor_1 = k ^ x
        xor_2 = xor_1 ^ ls_2_y
        new_x = (ls_1_y & ls_8_y) ^ xor_2

        return y, new_x

    def encrypt(self, plain):
        plaintext = int.from_bytes(plain,byteorder='little')
        try:
            b = (plaintext >> self.word_size) & self.mod_mask
            a = plaintext & self.mod_mask
        except TypeError:
            raise

        if self.mode == 'ECB':
            b, a = self.encrypt_function(b, a)

        elif self.mode == 'CTR':
            true_counter = self.iv + self.counter
            d = (true_counter >> self.word_size) & self.mod_mask
            c = true_counter & self.mod_mask
            d, c = self.encrypt_function(d, c)
            b ^= d
            a ^= c
            self.counter += 1

        elif self.mode == 'CBC':
            b ^= self.iv_upper
            a ^= self.iv_lower
            b, a = self.encrypt_function(b, a)

            self.iv_upper = b
            self.iv_lower = a
            self.iv = (b << self.word_size) + a

        elif self.mode == 'PCBC':
            f, e = b, a
            b ^= self.iv_upper
            a ^= self.iv_lower
            b, a = self.encrypt_function(b, a)
            self.iv_upper = b ^ f
            self.iv_lower = a ^ e
            self.iv = (self.iv_upper << self.word_size) + self.iv_lower

        elif self.mode == 'CFB':
            d = self.iv_upper
            c = self.iv_lower
            d, c = self.encrypt_function(d, c)
            b ^= d
            a ^= c

            self.iv_upper = b
            self.iv_lower = a
            self.iv = (b << self.word_size) + a

        elif self.mode == 'OFB':
            d = self.iv_upper
            c = self.iv_lower
            d, c = self.encrypt_function(d, c)
            self.iv_upper = d
            self.iv_lower = c
            self.iv = (d << self.word_size) + c

            b ^= d
            a ^= c

        ciphertext = (b << self.word_size) + a
        return ciphertext.to_bytes(length=len(plain), byteorder="little")

    def decrypt(self, cipher):
        ciphertext = int.from_bytes(cipher, byteorder='little')
        try:
            b = (ciphertext >> self.word_size) & self.mod_mask
            a = ciphertext & self.mod_mask
        except TypeError:
            raise

        if self.mode == 'ECB':
            a, b = self.decrypt_function(a, b)

        elif self.mode == 'CTR':
            true_counter = self.iv + self.counter
            d = (true_counter >> self.word_size) & self.mod_mask
            c = true_counter & self.mod_mask
            d, c = self.encrypt_function(d, c)
            b ^= d
            a ^= c
            self.counter += 1

        elif self.mode == 'CBC':
            f, e = b, a
            a, b = self.decrypt_function(a, b)
            b ^= self.iv_upper
            a ^= self.iv_lower

            self.iv_upper = f
            self.iv_lower = e
            self.iv = (f << self.word_size) + e

        elif self.mode == 'PCBC':
            f, e = b, a
            a, b = self.decrypt_function(a, b)
            b ^= self.iv_upper
            a ^= self.iv_lower
            self.iv_upper = (b ^ f)
            self.iv_lower = (a ^ e)
            self.iv = (self.iv_upper << self.word_size) + self.iv_lower

        elif self.mode == 'CFB':
            d = self.iv_upper
            c = self.iv_lower
            self.iv_upper = b
            self.iv_lower = a
            self.iv = (b << self.word_size) + a
            d, c = self.encrypt_function(d, c)
            b ^= d
            a ^= c

        elif self.mode == 'OFB':
            d = self.iv_upper
            c = self.iv_lower
            d, c = self.encrypt_function(d, c)
            self.iv_upper = d
            self.iv_lower = c
            self.iv = (d << self.word_size) + c

            b ^= d
            a ^= c

        plaintext = (b << self.word_size) + a
        return plaintext.to_bytes(length=len(cipher), byteorder="little")

    def encrypt_function(self, upper_word, lower_word):
        x = upper_word
        y = lower_word

        for k in self.key_schedule[:4]:
            ls_1_x = ((x >> (self.word_size - 1)) + (x << 1)) & self.mod_mask
            ls_8_x = ((x >> (self.word_size - 8)) + (x << 8)) & self.mod_mask
            ls_2_x = ((x >> (self.word_size - 2)) + (x << 2)) & self.mod_mask

            xor_1 = (ls_1_x & ls_8_x) ^ y
            xor_2 = xor_1 ^ ls_2_x
            y = x
            x = k ^ xor_2

        return x, y

    def decrypt_function(self, upper_word, lower_word):
        x = upper_word
        y = lower_word

        for k in reversed(self.key_schedule[:4]):
            # Generate all circular shifts
            ls_1_x = ((x >> (self.word_size - 1)) + (x << 1)) & self.mod_mask
            ls_8_x = ((x >> (self.word_size - 8)) + (x << 8)) & self.mod_mask
            ls_2_x = ((x >> (self.word_size - 2)) + (x << 2)) & self.mod_mask

            xor_1 = (ls_1_x & ls_8_x) ^ y
            xor_2 = xor_1 ^ ls_2_x
            y = x
            x = k ^ xor_2

        return x, y

    def update_iv(self, new_iv):
        if new_iv:
            try:
                self.iv = new_iv & ((2 ** self.block_size) - 1)
                self.iv_upper = self.iv >> self.word_size
                self.iv_lower = self.iv & self.mod_mask
            except TypeError:
                raise
        return self.iv


def sm3_hash(message: bytes):
    msg_list = [i for i in message]
    hash_hex = sm3.sm3_hash(msg_list)
    hash_bytes = bytes.fromhex(hash_hex)
    return hash_bytes


def lsr(val, shift):
    return (val & 0xffffffff) >> shift


def lsl(val, shift):
    return (val & 0xffffffff) << shift


def eor(val1, val2):
    return val1 ^ val2


def orr(val1, val2):
    return val1 | val2


def mvn(val):
    return ~val & 0xffffffffffffffff


def cal_verify(val0, val1, val2):
    x8 = val0
    x10 = lsl(val2, 0x7) & 0xffffffff
    x8 = eor(x8, x10)
    v2 = lsr(val2, 0x3)
    v3 = eor(v2, x8)
    v4 = eor(v3, val2)
    v5 = lsr(v4, 0x5)
    x10 = lsl(v4, 0xb) & 0xffffffff ^ val1
    v6 = eor(v5, x10)
    v7 = eor(v4, v6)
    v7 = orr(v7, 0x0)
    v7 = mvn(v7) & 0xffffffff
    return v7

def calc_fuck4(barr):
    rr = 0x20220420
    byte_arr = bytearray(barr)
    for nn in range(6):
        rr = cal_verify(byte_arr[nn * 2], byte_arr[nn * 2 + 1], rr)
    rr ^= 0x1000004
    return rr.to_bytes(4, byteorder='little')

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


def get_xm_enc(sourceInfo, deviceInfos, url, xk, stub, callTimes, sign_key, licenseID, lanusk, prl):
    if prl == "ios_v2":
        pbInput,bodyHashByte = generatePbDataV2(xk, deviceInfos, url, stub, callTimes, sourceInfo, licenseID, lanusk)
    else:
        pbInput, bodyHashByte = generatePbDataV3(xk, deviceInfos, url, stub, callTimes, sourceInfo, licenseID, lanusk)
    queryHashByte = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))[0]
    rrr = random.randint(0x10000000, 0xFFFFFFFF)
    randBytes = struct.pack("<I", rrr)
    randBytes2 = struct.pack("<I", random.randint(0x10000000, 0xFFFFFFFF))
    highRand = randBytes[2:]
    lowRand = randBytes[:2]
    xmKey = [0] * 68
    xmKey[0:32] = base64.b64decode(sign_key)
    xmKey[32:36] = bytes(lowRand + highRand)
    xmKey[36:68] = base64.b64decode(sign_key)

    xmKey = sm3_hash(bytes(xmKey))
    encryptData = bytearray()
    pbPadding = pad(pbInput, 16)
    w = SimonCipher(xmKey, key_size=256)
    for i in range(len(pbPadding) // 16):
        encryptData += w.encrypt(pbPadding[16 * i:16 * (i + 1)])
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
    encryptData += bytes(8)
    tmp1 = bytearray()
    for n, i in enumerate(encryptData):
        tmp1.append(i ^ xor1[(n % 4)])

    tmp1 += highRand
    append_array = calc_head1(queryHashByte, bodyHashByte)
    magic_num = calc_head0(base64.b64decode(sign_key)).to_bytes(1, 'big')
    tmp1 = magic_num + randBytes2 + append_array + tmp1
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

def get_str(length=4):
    seed = list('0123456789abcdef')
    return ''.join([random.choice(seed) for _ in range(length)])

def generatePbDataV2(xk, deviceInfos, url, stub, callTimes, sourceInfo, licenseID, lanusk):
    deviceId = deviceInfos["deviceid"]
    devicetoken = deviceInfos["devicetoken"]
    aid = sourceInfo["aid"]
    if len(stub) == 0:
        stub = bytes(16)
        pskStub = b"00000000000000000000000000000000"

    else:
        pskStub = stub
        stub = bytes.fromhex(stub.decode())
    querySm3 = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))
    xmData = dyEncrypt_proto.XM()
    xmData.magic = base64.b64decode("NmyVbDVyWpvk1B1lyLh5Jg==")
    xmData.version = 4
    xmData.rand = random.randint(0, 0x7FFFFFFF)
    xmData.msAppID = str(aid)
    xmData.deviceID = deviceId
    xmData.licenseID = licenseID
    xmData.appVersion = sourceInfo["apkVersion"]
    xmData.sdkVersionStr = sourceInfo["mssdkVersionStr"]
    xmData.sdkVersion = sourceInfo["mssdkVersionInt"] * 2
    xmData.envCode = bytes.fromhex("0000000000000000")
    xmData.platform = 1
    xmData.createTime = xk * 2
    hashpart1 = bytes.fromhex(dyMd5(querySm3+stub+xk.to_bytes(4, byteorder='little')+bytes.fromhex(get_str(length=len("8496779dd4150bf8a0010000")))))
    hashpart2 = calc_fuck4(hashpart1)
    xmData.bodyHash = hashpart1 + hashpart2
    xmData.queryHash = querySm3[:6]
    xmData.algorithmCount.signCount = callTimes * 2
    xmData.algorithmCount.reportCount = 1388734
    xmData.algorithmCount.settingCount = 1388734
    xmData.secDeviceToken = devicetoken.encode()
    xmData.isAppLicense = xk * 2
    if lanusk:
        xmData.pskHash = getpsk_hash(lanusk)
        xmData.pskCalHash = get_psk_cal_hash(url.split("?")[1], pskStub.decode())
        xmData.pskVersion = "1"
    else:
        xmData.pskVersion = "none"
    xmData.callType = 738
    xmData.unknownCount.unknown1 = callTimes * 2
    xmData.unknownCount.unknown2 = 1388734
    xmData.unknownCount.unknown3 = 1388734
    xmData.unknownCount.unknown5 = 1388734
    xmData.unknownCount.sdkspec_str = sourceInfo["mssdkVersionStr"]
    xmData.cmr_str = '{"kd":0,"fkd":1041969941,"pd":897456018,"tk":true}'
    # print("[iOS] xmData V2>>>", xmData.SerializeToString())
    return xmData.SerializeToString(),xmData.bodyHash[0]

def generatePbDataV3(xk, deviceInfos, url, stub, callTimes, sourceInfo, licenseID, lanusk):
    deviceId = deviceInfos["device_id"]
    devicetoken = deviceInfos["devicetoken"]
    aid = sourceInfo["aid"]
    if len(stub) == 0:
        stub = bytes(16)
        pskStub = b"00000000000000000000000000000000"

    else:
        pskStub = stub
        stub = bytes.fromhex(stub.decode())
    querySm3 = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))


    xmData = dyEncrypt_proto.XM()
    xmData.magic = base64.b64decode("NmyVbDVyWpvk1B1lyLh5Jg==")
    xmData.version = 4
    xmData.rand = random.randint(0, 0x7FFFFFFF)
    xmData.msAppID = str(aid)
    xmData.deviceID = deviceId
    xmData.licenseID = licenseID
    xmData.appVersion = sourceInfo["appVersion"]
    xmData.sdkVersionStr = sourceInfo["mssdkVersionStr"]
    xmData.sdkVersion = sourceInfo["mssdkVersionInt"] * 2
    xmData.envCode = bytes.fromhex("0000000000000000")
    xmData.platform = 1
    xmData.createTime = xk * 2
    hashpart1 = bytes.fromhex(dyMd5(querySm3+stub+xk.to_bytes(4, byteorder='little')+bytes.fromhex("8496779dd4150bf8a0010000")))
    hashpart2 = calc_fuck4(hashpart1)
    xmData.bodyHash = hashpart1 + hashpart2
    xmData.queryHash = querySm3[:6]
    xmData.algorithmCount.signCount = 58
    xmData.algorithmCount.reportCount = 10
    xmData.algorithmCount.settingCount = 1388734
    xmData.secDeviceToken = devicetoken
    xmData.isAppLicense = xk * 2
    if lanusk:
        xmData.pskHash = getpsk_hash(lanusk)
        xmData.pskCalHash = get_psk_cal_hash(url.split("?")[1], pskStub.decode())
        xmData.pskVersion = "1"
    else:
        xmData.pskVersion = "none"
    xmData.callType = 738
    xmData.unknownCount.unknown1 = 74
    xmData.unknownCount.unknown2 = 1388734
    xmData.unknownCount.unknown3 = 1388734
    xmData.unknownCount.unknown5 = 1388734
    xmData.unknownCount.sdkspec_str = sourceInfo["mssdkVersionStr"]
    xmData.cmr_str = '{"kd":0,"fkd":1041969941,"pd":897456018,"tk":true}'
    # print("[iOS] xmData V3>>>", xmData.SerializeToString())

    return xmData.SerializeToString(),xmData.bodyHash[0]

def getpsk_hash(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.digest()

def get_psk_cal_hash(query, stub):
    stubHex = binascii.unhexlify(stub)
    buf = bytearray(query.encode('utf-8')) + stubHex + b'0'
    return sm3_hash(buf)