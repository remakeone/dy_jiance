import base64
import hashlib
import random
import struct
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import dy26_pb2
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
from collections import deque
from gmssl import sm3

class SimonCipher(object):
    """Simon Block Cipher Object"""

    # Z Arrays (stored bit reversed for easier usage)
    z0 = 0b01100111000011010100100010111110110011100001101010010001011111
    z1 = 0b01011010000110010011111011100010101101000011001001111101110001
    z2 = 0b11001101101001111110001000010100011001001011000000111011110101
    z3 = 0b11110000101100111001010001001000000111101001100011010111011011
    z4 = 0b11110111001001010011000011101000000100011011010110011110001011

    # valid cipher configurations stored:
    # block_size:{key_size:(number_rounds,z sequence)}
    __valid_setups = {32: {64: (32, z0)},
                      48: {72: (36, z0), 96: (36, z1)},
                      64: {96: (42, z2), 128: (44, z3)},
                      96: {96: (52, z2), 144: (54, z3)},
                      128: {128: (68, z2), 192: (69, z3), 256: (72, z4)}}

    __valid_modes = ['ECB', 'CTR', 'CBC', 'PCBC', 'CFB', 'OFB']

    def __init__(self, key, key_size=128, block_size=128, mode='ECB', init=0, counter=0):
        """
        Initialize an instance of the Simon block cipher.
        :param key: Int representation of the encryption key
        :param key_size: Int representing the encryption key in bits
        :param block_size: Int representing the block size in bits
        :param mode: String representing which cipher block mode the object should initialize with
        :param init: IV for CTR, CBC, PCBC, CFB, and OFB modes
        :param counter: Initial Counter value for CTR mode
        :return: None
        """
        # Setup block/word size
        try:
            self.possible_setups = self.__valid_setups[block_size]
            self.block_size = block_size
            self.word_size = self.block_size >> 1
        except KeyError:
            print('Invalid block size!')
            print('Please use one of the following block sizes:', [x for x in self.__valid_setups.keys()])
            raise

        # Setup Number of Rounds, Z Sequence, and Key Size
        try:
            self.rounds, self.zseq = self.possible_setups[key_size]
            self.key_size = key_size
        except KeyError:
            print('Invalid key size for selected block size!!')
            print('Please use one of the following key sizes:', [x for x in self.possible_setups.keys()])
            raise

        # Create Properly Sized bit mask for truncating addition and left shift outputs
        self.mod_mask = (2 ** self.word_size) - 1

        # Parse the given iv and truncate it to the block length
        try:
            self.iv = init & ((2 ** self.block_size) - 1)
            self.iv_upper = self.iv >> self.word_size
            self.iv_lower = self.iv & self.mod_mask
        except (ValueError, TypeError):
            print('Invalid IV Value!')
            print('Please Provide IV as int')
            raise

        # Parse the given Counter and truncate it to the block length
        try:
            self.counter = counter & ((2 ** self.block_size) - 1)
        except (ValueError, TypeError):
            print('Invalid Counter Value!')
            print('Please Provide Counter as int')
            raise

        # Check Cipher Mode
        try:
            position = self.__valid_modes.index(mode)
            self.mode = self.__valid_modes[position]
        except ValueError:
            print('Invalid cipher mode!')
            print('Please use one of the following block cipher modes:', self.__valid_modes)
            raise

        self.key = int.from_bytes(key, byteorder='little')

        # Pre-compile key schedule
        m = self.key_size // self.word_size
        self.key_schedule = []

        # Create list of subwords from encryption key
        k_init = [((self.key >> (self.word_size * ((m - 1) - x))) & self.mod_mask) for x in range(m)]

        k_reg = deque(k_init)  # Use queue to manage key subwords

        round_constant = self.mod_mask ^ 3  # Round Constant is 0xFFFF..FC

        # Generate all round keys
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
        """
        Complete One Feistel Round
        :param x: Upper bits of current plaintext
        :param y: Lower bits of current plaintext
        :param k: Round Key
        :return: Upper and Lower ciphertext segments
        """

        # Generate all circular shifts
        ls_1_x = ((x >> (self.word_size - 1)) + (x << 1)) & self.mod_mask
        ls_8_x = ((x >> (self.word_size - 8)) + (x << 8)) & self.mod_mask
        ls_2_x = ((x >> (self.word_size - 2)) + (x << 2)) & self.mod_mask

        # XOR Chain
        xor_1 = (ls_1_x & ls_8_x) ^ y
        xor_2 = xor_1 ^ ls_2_x
        new_x = k ^ xor_2

        return new_x, x

    def decrypt_round(self, x, y, k):
        """Complete One Inverse Feistel Round
        :param x: Upper bits of current ciphertext
        :param y: Lower bits of current ciphertext
        :param k: Round Key
        :return: Upper and Lower plaintext segments
        """

        # Generate all circular shifts
        ls_1_y = ((y >> (self.word_size - 1)) + (y << 1)) & self.mod_mask
        ls_8_y = ((y >> (self.word_size - 8)) + (y << 8)) & self.mod_mask
        ls_2_y = ((y >> (self.word_size - 2)) + (y << 2)) & self.mod_mask

        # Inverse XOR Chain
        xor_1 = k ^ x
        xor_2 = xor_1 ^ ls_2_y
        new_x = (ls_1_y & ls_8_y) ^ xor_2

        return y, new_x

    def encrypt(self, plain):
        """
        Process new plaintext into ciphertext based on current cipher object setup
        :param plaintext: Int representing value to encrypt
        :return: Int representing encrypted value
        """
        plaintext = int.from_bytes(plain,byteorder='little')
        try:
            b = (plaintext >> self.word_size) & self.mod_mask
            a = plaintext & self.mod_mask
        except TypeError:
            print('Invalid plaintext!')
            print('Please provide plaintext as int')
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
        """
        Process new ciphertest into plaintext based on current cipher object setup
        :param ciphertext: Int representing value to encrypt
        :return: Int representing decrypted value
        """
        ciphertext = int.from_bytes(cipher, byteorder='little')
        try:
            b = (ciphertext >> self.word_size) & self.mod_mask
            a = ciphertext & self.mod_mask
        except TypeError:
            print('Invalid ciphertext!')
            print('Please provide ciphertext as int')
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
        """
        Completes appropriate number of Simon Fiestel function to encrypt provided words
        Round number is based off of number of elements in key schedule
        upper_word: int of upper bytes of plaintext input
                    limited by word size of currently configured cipher
        lower_word: int of lower bytes of plaintext input
                    limited by word size of currently configured cipher
        x,y:        int of Upper and Lower ciphertext words
        """
        x = upper_word
        y = lower_word

        # Run Encryption Steps For Appropriate Number of Rounds
        for k in self.key_schedule:
            # Generate all circular shifts
            ls_1_x = ((x >> (self.word_size - 1)) + (x << 1)) & self.mod_mask
            ls_8_x = ((x >> (self.word_size - 8)) + (x << 8)) & self.mod_mask
            ls_2_x = ((x >> (self.word_size - 2)) + (x << 2)) & self.mod_mask

            # XOR Chain
            xor_1 = (ls_1_x & ls_8_x) ^ y
            xor_2 = xor_1 ^ ls_2_x
            y = x
            x = k ^ xor_2

        return x, y

    def decrypt_function(self, upper_word, lower_word):
        """
        Completes appropriate number of Simon Fiestel function to decrypt provided words
        Round number is based off of number of elements in key schedule
        upper_word: int of upper bytes of ciphertext input
                    limited by word size of currently configured cipher
        lower_word: int of lower bytes of ciphertext input
                    limited by word size of currently configured cipher
        x,y:        int of Upper and Lower plaintext words
        """
        x = upper_word
        y = lower_word

        # Run Encryption Steps For Appropriate Number of Rounds
        for k in reversed(self.key_schedule):
            # Generate all circular shifts
            ls_1_x = ((x >> (self.word_size - 1)) + (x << 1)) & self.mod_mask
            ls_8_x = ((x >> (self.word_size - 8)) + (x << 8)) & self.mod_mask
            ls_2_x = ((x >> (self.word_size - 2)) + (x << 2)) & self.mod_mask

            # XOR Chain
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
                print('Invalid Initialization Vector!')
                print('Please provide IV as int')
                raise
        return self.iv

def sm3_hash(message: bytes):
    """
    国密sm3加密
    :param message: 消息值，bytes类型
    :return: 哈希值
    """

    msg_list = [i for i in message]
    hash_hex = sm3.sm3_hash(msg_list)
    hash_bytes = bytes.fromhex(hash_hex)
    return hash_bytes


def get_xa_enc(url, xk, stub, app_info):
    pbInput = generatePbData(xk, app_info, url, stub)
    query_sm3_1st_byte = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))[0]
    if len(stub) == 0:
        stub = bytes(16)
    else:
        stub = bytes.fromhex(stub.decode())
    stub_1st_byte = sm3_hash(stub)[0]
    rrr = random.randint(0x10000000, 0xFFFFFFFF)
    # rrr = 0x55208930
    randBytes = struct.pack("<I", rrr)
    randBytes2 = struct.pack(">I", random.randint(0x10000000, 0xFFFFFFFF))
    # randBytes2 = struct.pack(">I", 0x0d876c45)
    highRand = randBytes[2:]
    lowRand = randBytes[:2]
    sign_key = "jr36OAbsxc7nlCPmAp7YJUC8Ihi7fq73HLaR96qKovU="
    aes_key = hashlib.md5(base64.b64decode(sign_key)[0:16]).digest()
    aes_iv = hashlib.md5(base64.b64decode(sign_key)[16:32]).digest()
    xmKey = [0] * 68
    xmKey[0:32] = base64.b64decode(sign_key)
    xmKey[32:36] = bytes(lowRand + highRand)
    xmKey[36:68] = base64.b64decode(sign_key)
    # 获取第一轮加密key
    xmKey = sm3_hash(bytes(xmKey))
    encryptData = bytearray()
    pbPadding = pad(pbInput, 16)
    w = SimonCipher(xmKey, key_size=256)
    for i in range(len(pbPadding) // 16):
        encryptData += w.encrypt(pbPadding[16 * i:16 * (i + 1)])
    encryptData = encryptData[::-1]

    # xor1 = struct.pack("<I", random.randint(0x10000000, 0xFFFFFFFF))
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
    encryptData += bytes.fromhex("0000000000000000")
    tmp1 = bytearray()

    for n, i in enumerate(encryptData):
        tmp1.append(i ^ xor1[(n % 4)])

    tmp1 += highRand
    query_sm3_1st_byte = query_sm3_1st_byte & 0x3f
    stub_1st_byte = stub_1st_byte & 0x3f

    # Initialize x_reg to 0x18000000
    x_reg = 0x18000000

    # Bitwise OR query_sm3_1st_byte shifted left by 14 bits with x_reg
    y_reg = query_sm3_1st_byte << 0xe
    x_reg = x_reg ^ y_reg

    # Bitwise OR stub_1st_byte shifted left by 8 bits with x_reg
    y_reg = stub_1st_byte << 0x8
    x_reg = x_reg ^ y_reg

    # Bitwise XOR x_reg with 0x1
    x_reg = x_reg ^ 0x1

    # Truncate x_reg to 32 bits
    x_reg = x_reg & 0xffffffff

    # Convert x_reg to a byte array
    append_array = bytearray([
        (x_reg >> 0) & 0xFF,
        (x_reg >> 8) & 0xFF,
        (x_reg >> 16) & 0xFF,
        (x_reg >> 24) & 0xFF,
    ])
    tmp1 = bytes.fromhex("35") + randBytes2 + append_array + tmp1
    aes = AES.new(key=aes_key, mode=AES.MODE_CBC, iv=aes_iv)
    aesEncryptData = aes.encrypt(pad(tmp1, 16))
    return base64.b64encode(lowRand + aesEncryptData).decode()


def generatePbData(xk, app_info, url, stub):
    if len(stub) == 0:
        stub = bytes(16)
    else:
        stub = bytes.fromhex(stub.decode())
    xaData = dy26_pb2.XA()
    xaData.roundkey = 1077940818
    xaData.flag = 2
    xaData.random_double = random.randint(0x10000000, 0x20000000) * 2
    xaData.aid = app_info['aid']
    xaData.deviceId = app_info['device_id']
    xaData.licenseID = "1588093228"
    xaData.version = app_info['app_version']
    xaData.mssdk_version = "v04.05.00-ml-android"
    xaData.mssdk_version_hash = 134873088
    xaData.unkonw10 = bytes.fromhex("0000000000000000")
    xaData.x_khronos = xk * 2
    xaData.x_ss_stub_sm3 = sm3_hash(stub)[:6]
    xaData.url_sm3 = sm3_hash(bytes(url.split("?")[1], encoding="UTF-8"))[:6]
    xaData.xa15.unknow1 = 2860  # 调用次数
    xaData.xa15.unknow2 = 10
    xaData.xa15.unknow3 = 1388734
    xaData.unkonw16 = "AkRsw26fF5gSfRtqwuKRE-9g_".encode()
    xaData.x_khronos_2 = xk * 2
    xaData.type = "none"
    xaData.unkonw21 = 624
    return xaData.SerializeToString()



# url = "https://api3-normal-c.amemv.com/aweme/v1/poi/tab/modules/spu_list/?poi_id=7068876195881977895&enter_source&item_id&poi_enter_id=fb5f673bbb4135c0e3d5d9ea9e5fc656&location_permission=1&extra_params=%7B%22search_params%22%3A%22%7B%5C%22enter_from%5C%22%3A%5C%22general_search%5C%22%2C%5C%22enter_method%5C%22%3A%5C%22click_search_poi_card%5C%22%2C%5C%22search_keyword%5C%22%3A%5C%22%E8%8C%B6%E7%99%BE%E9%81%93%E5%9B%A2%E8%B4%AD%E6%8A%96%E9%9F%B3%E5%9B%A2%E8%B4%AD%5C%22%2C%5C%22token_type%5C%22%3A%5C%22douyin_groupbuy_spu%5C%22%7D%22%7D&request_tag_from=h5&iid=407281526652702&device_id=1392443584690903&ac=wifi&channel=shenmasem_ls_dy_305&aid=1128&app_name=aweme&version_code=260200&version_name=26.2.0&device_platform=android&os=android&ssmix=a&device_type=Pixel+6&device_brand=google&language=zh&os_api=33&os_version=13&openudid=fff4b2564aa78d8e&manifest_version_code=260201&resolution=1080*2219&dpi=420&update_version_code=26209900&_rticket=1692275158569&package=com.ss.android.ugc.aweme&cpu_support64=true&host_abi=armeabi-v7a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&need_personal_recommend=1&is_android_pad=0&ts=1692275156"
# stub = bytes.fromhex("")
# xk = 1692275159
# deviceId = ""
# xa = get_xa_enc(url, stub, xk, deviceId)
# print(xa)