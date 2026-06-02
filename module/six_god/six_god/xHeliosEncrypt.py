import base64
import random
import struct
from hashlib import md5
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def generateKey(num, aid):
    message = num + bytes(aid, encoding="UTF-8")
    key = bytes(md5(message).hexdigest(), encoding="UTF-8")
    return key


def xor_arrays(arr1, arr2):
    result = bytearray()
    for i in range(len(arr1)):
        result.append(arr1[i] ^ arr2[i])
    return result

def get_xhelios(xk, sourceInfo, licenseID):
    aid = sourceInfo["aid"]
    plainText = pad((str(xk) + f"-{licenseID}-{aid}").encode(), 16)
    randBytes = struct.pack("<I", random.randint(0x10000000, 0xFFFFFFFF))
    keybuf = generateKey(randBytes, str(aid))
    key = keybuf[:16]
    aesInput = keybuf[16:]
    aes = AES.new(key=key, mode=AES.MODE_ECB)
    tmp1 = aes.encrypt(aesInput)
    tmp2 = aes.encrypt(tmp1)
    return base64.b64encode(randBytes + xor_arrays(tmp1+tmp2, plainText)).decode()




