import binascii
import sys
import os.path

SV = [
    0xA7AEFE20,0x7149F1D6,0x47E4CA07,0xE9B58F67,0x93B924DE,0xC614D0F5,0x38AFE0EF,0xB2BBAD73,0xE24444C3,0x9D3AEC9B,0xDF7B37E4,0xD8B16D40,0xF8AC31B8,0x76B9A90B,0x31D833EE,0x953FCE64,0x6A6B2B48,0x8C138276,0x6D24A010,0x18DA124B,0xBBEB82EE,0x39F7EA56,0x149F4FE1,0x229946BC,0x0327F309,0xF4F50E66,0x62D569AA,0x78419F92,0x4DB088A7,0x7430A018,0xF31D88F4,0x2F4ED651,0x9B13FE59,0x45C5910D,0x374BF0EC,0xD5A5B69E,0xEFACEB16,0x714F4811,0x4C98233B,0xC9E6E7B1,0xD0623B3F,0xDF5E4F6F,0xCCB31244,0xADDAB856,0x6FAF9C9E,0x62804E10,0x6FA7E29D,0x7E429D51,0xCDB31E01,0xB339E419,0xE497A8A3,0xEBECA6BC,0x1746CD57,0xFBF4F54A,0xD5EA2A8B,0xB4F02ED2,0x0512B192,0xEFAD4D29,0xD59BEC05,0x2A1436E2,0xFAEA73C1,0x1EBDBAE8,0x8FF257BD,0x2D59351D
]


def leftCircularShift(k, bits):
    bits = bits % 32
    k = k % (2 ** 32)
    upper = (k << bits) % (2 ** 32)
    result = upper | (k >> (32 - (bits)))
    return (result)


def blockDivide(block, chunks):
    result = []
    size = len(block) // chunks
    for i in range(0, chunks):
        result.append(int.from_bytes(block[i * size:(i + 1) * size], byteorder="little"))
    return (result)


def F(X, Y, Z):
    return ((X & Y) | ((~X) & Z))


def G(X, Y, Z):
    return ((X & Z) | (Y & (~Z)))


def H(X, Y, Z):
    return (X ^ Y ^ Z)


def I(X, Y, Z):
    return (Y ^ (X | (~Z)))


def FF(a, b, c, d, M, s, t):
    result = b + leftCircularShift((a + F(b, c, d) + M + t), s)
    return (result&0xffffffff)


def GG(a, b, c, d, M, s, t):
    result = b + leftCircularShift((a + G(b, c, d) + M + t), s)
    return (result)


def HH(a, b, c, d, M, s, t):
    result = b + leftCircularShift((a + H(b, c, d) + M + t), s)
    return (result)


def II(a, b, c, d, M, s, t):
    result = b + leftCircularShift((a + I(b, c, d) + M + t), s)
    return (result)


def fmt8(num):
    bighex = "{0:08x}".format(num)
    binver = binascii.unhexlify(bighex)
    result = "{0:08x}".format(int.from_bytes(binver, byteorder='little'))
    return (result)


def bitlen(bitstring):
    return (len(bitstring) * 8)


def dyMd5(msg):
    iterations = 1
    # chaining variables
    A = 0x79e0f2fb
    B = 0xc8b52570
    C = 0xebc2f8cd
    D = 0x7c104d93
    # main loop
    for i in range(0, iterations):
        a = A
        b = B
        c = C
        d = D
        block = msg[i * 64:(i + 1) * 64]
        M = blockDivide(block, 16)
        # Rounds
        a = FF(a, b, c, d, M[0], 7, SV[0])
        d = FF(d, a, b, c, M[14], 12, SV[1])
        c = FF(c, d, a, b, M[13], 17, SV[2])
        b = FF(b, c, d, a, M[12], 22, SV[3])
        a = FF(a, b, c, d, M[11], 7, SV[4])
        d = FF(d, a, b, c, M[10], 12, SV[5])
        c = FF(c, d, a, b, M[9], 17, SV[6])
        b = FF(b, c, d, a, M[7], 22, SV[7])
        a = FF(a, b, c, d, M[8], 7, SV[8])
        d = FF(d, a, b, c, M[6], 12, SV[9])
        c = FF(c, d, a, b, M[5], 17, SV[10])
        b = FF(b, c, d, a, M[4], 22, SV[11])
        a = FF(a, b, c, d, M[3], 7, SV[12])
        d = FF(d, a, b, c, M[2], 12, SV[13])
        c = FF(c, d, a, b, M[1], 17, SV[14])
        b = FF(b, c, d, a, M[15], 22, SV[15])

        a = GG(a, b, c, d, M[0], 5, SV[16])
        d = GG(d, a, b, c, M[5], 9, SV[17])
        c = GG(c, d, a, b, M[10], 14, SV[18])
        b = GG(b, c, d, a, M[1], 20, SV[19])
        a = GG(a, b, c, d, M[12], 5, SV[20])
        d = GG(d, a, b, c, M[11], 9, SV[21])
        c = GG(c, d, a, b, M[15], 14, SV[22])
        b = GG(b, c, d, a, M[2], 20, SV[23])
        a = GG(a, b, c, d, M[9], 5, SV[24])
        d = GG(d, a, b, c, M[14], 9, SV[25])
        c = GG(c, d, a, b, M[3], 14, SV[26])
        b = GG(b, c, d, a, M[8], 20, SV[27])
        a = GG(a, b, c, d, M[6], 5, SV[28])
        d = GG(d, a, b, c, M[7], 9, SV[29])
        c = GG(c, d, a, b, M[4], 14, SV[30])
        b = GG(b, c, d, a, M[13], 20, SV[31])

        a = HH(a, b, c, d, M[8], 4, SV[32])
        d = HH(d, a, b, c, M[5], 11, SV[33])
        c = HH(c, d, a, b, M[12], 16, SV[34])
        b = HH(b, c, d, a, M[14], 23, SV[35])
        a = HH(a, b, c, d, M[1], 4, SV[36])
        d = HH(d, a, b, c, M[12], 11, SV[37])
        c = HH(c, d, a, b, M[7], 16, SV[38])
        b = HH(b, c, d, a, M[13], 23, SV[39])
        a = HH(a, b, c, d, M[10], 4, SV[40])
        d = HH(d, a, b, c, M[0], 11, SV[41])
        c = HH(c, d, a, b, M[2], 16, SV[42])
        b = HH(b, c, d, a, M[6], 23, SV[43])
        a = HH(a, b, c, d, M[4], 4, SV[44])
        d = HH(d, a, b, c, M[11], 11, SV[45])
        c = HH(c, d, a, b, M[15], 16, SV[46])
        b = HH(b, c, d, a, M[3], 23, SV[47])

        a = II(a, b, c, d, M[8], 6, SV[48])
        d = II(d, a, b, c, M[6], 10, SV[49])
        c = II(c, d, a, b, M[15], 15, SV[50])
        b = II(b, c, d, a, M[5], 21, SV[51])
        a = II(a, b, c, d, M[13], 6, SV[52])
        d = II(d, a, b, c, M[9], 10, SV[53])
        c = II(c, d, a, b, M[10], 15, SV[54])
        b = II(b, c, d, a, M[2], 21, SV[55])
        a = II(a, b, c, d, M[2], 6, SV[56])
        d = II(d, a, b, c, M[14], 10, SV[57])
        c = II(c, d, a, b, M[7], 15, SV[58])
        b = II(b, c, d, a, M[12], 21, SV[59])
        a = II(a, b, c, d, M[4], 6, SV[60])
        d = II(d, a, b, c, M[1], 10, SV[61])
        c = II(c, d, a, b, M[11], 15, SV[62])
        b = II(b, c, d, a, M[3], 21, SV[63])

        A = (A + a) % (2 ** 32)
        B = (B + b) % (2 ** 32)
        C = (C + c) % (2 ** 32)
        D = (D + d) % (2 ** 32)
    A ^= 0x19be4866
    B ^= 0xe85986b4
    C ^= 0xe19b326e
    D ^= 0x71d1d7d4
    result = fmt8(A) + fmt8(B) + fmt8(C) + fmt8(D)
    return (result)


if __name__ == "__main__":
    data = bytes.fromhex("83467973f464830b68a628faf0ae0b7b6602e5c50414dcf92b9d3dd24fbfe3dc")+bytes.fromhex("00000000000000000000000000000000")+bytes.fromhex("d2b281648496779dd4150bf8a0010000")

