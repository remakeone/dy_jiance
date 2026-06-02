import random
import struct
from copy import deepcopy
from hashlib import md5


def key_schedular(key):
    j = 0
    s = [i for i in range(256)]  # initial state vector of 256 bit [0-255]
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[j]  # swap s[i], s[j]
    return s


# Pseudo Random Generator Algorithm
# Generate key stream
def pseudo_random_generator(s, input):
    i, j = 0, 0
    key_stream = []
    for k in range(0, len(input)):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[j]  # swap s[i] and s[j]
        t = (s[i] + s[j]) % 256
        key_stream.append(s[t])  # generate key stream
    return key_stream


# RC4 encryption
def encryption(key, plain_text):
    uni_key = [c for c in key]  # key convert into unicode
    s = key_schedular(uni_key)  # state vector
    key_stream = pseudo_random_generator(s, plain_text)  # key stream
    ciphertext = []
    for i in range(len(plain_text)):
        ciphertext.append(key_stream[i] ^ plain_text[i])  # bitwise XOR
    return bytearray(ciphertext)  # return cipher_text


def reverse(byte):
    binary_str = bin(byte)[2:].zfill(8)
    left_reverse = binary_str[:4]
    right_reverse = binary_str[4:]
    new_binary_str = right_reverse + left_reverse
    return int(new_binary_str, 2)

def reverse_bit(b):
    binary_str = bin(b)[2:].zfill(8)
    left_reverse = binary_str[:4][::-1]
    right_reverse = binary_str[4:][::-1]
    new_binary_str = right_reverse + left_reverse
    new_byte = int(new_binary_str,2)
    return new_byte

def encrypt_barr(input):
    arr = deepcopy(input)
    length = len(arr)
    for i in range(length):
        a = reverse(arr[i])
        b = arr[(i + 1) % length]
        arr[i] = (reverse_bit(a ^ b) ^ 0xeb)&0xff
    return arr


def XG(xk, url, data, cookie):
    gorgonArr = bytearray()
    zeroPad = bytearray([0] * 4)
    if url:
        gorgonArr += bytes.fromhex(md5(bytearray(url, "UTF-8")).hexdigest()[:8])
    else:
        gorgonArr += zeroPad

    if data:
        gorgonArr += bytes.fromhex(md5(bytearray(data, "UTF-8")).hexdigest()[:8])
    else:
        gorgonArr += zeroPad
    if cookie:
        gorgonArr += bytes(md5(bytearray(cookie, "UTF-8")).hexdigest(), encoding="UTF-8")[:4]
    else:
        gorgonArr += zeroPad

    gorgonArr += bytes.fromhex("10010330")
    gorgonArr += struct.pack(">I", int(xk))

    s1 = [0x00, 0x20, 0x40, 0x60, 0x80, 0xa0, 0xc0, 0xe0]
    rand1 = random.randint(0, 255)
    rand2 = s1[random.randint(0, 7)]
    rc4Key = [0x4a, 0x00, 0x16, rand1, 0x47, 0x6c, 0x00, rand2]
    cipherText = encryption(rc4Key, gorgonArr)
    arr = encrypt_barr(cipherText)
    versionCode = bytes.fromhex("8404")
    keyData = rand2.to_bytes(1, byteorder="little") + rand1.to_bytes(1, byteorder="little")
    xg = versionCode + keyData + bytes.fromhex("0000") + arr
    return xg.hex()



def get_xgorgon(xk, url, data="", cookie=""):
    return XG(xk, url.split("?")[1], data, cookie)