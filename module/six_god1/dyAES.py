state = [ [0]*4 for _ in range(4) ]
RoundKey = [0]*176

Key = None
Iv = None

#The number of columns comprising a state in AES. This is a constant in AES. Value=4
Nb = 4
#The number of 32 bit words in a key.
Nk = 4
#Key length in bytes [128 bit]
KEYLEN = 16
#The number of rounds in AES Cipher.
Nr = 10

sbox =   [
  0x2e, 0x5c, 0x55, 0xed, 0x1b, 0xda, 0x0a, 0x79, 0x28, 0x69, 0x57, 0xfe, 0x68, 0x3a, 0xde, 0xac, 0x90, 0xf9, 0xc1,
  0xe1, 0xc3, 0x8b, 0x7f, 0x59, 0x26, 0xca, 0x13, 0xbb, 0x11, 0x37, 0x39, 0x21, 0xeb, 0x9a, 0xff, 0x5e, 0x42, 0x33,
  0xbe, 0x51, 0x8d, 0x40, 0x1e, 0x91, 0xb3, 0x85, 0xb7, 0xcd, 0xdc, 0x27, 0x92, 0x83, 0x87, 0x3f, 0xe6, 0x4a, 0x64,
  0x56, 0x8c, 0xa1, 0x76, 0xd2, 0xfd, 0xc0, 0x63, 0x18, 0x44, 0x1a, 0x9f, 0x61, 0xcb, 0x6e, 0x67, 0x29, 0xaf, 0xb8,
  0x54, 0x60, 0xdb, 0x97, 0xe8, 0xa3, 0xc9, 0xe4, 0x00, 0xec, 0x50, 0x17, 0xbd, 0x2a, 0xb6, 0x8e, 0x3b, 0x46, 0x65,
  0xa6, 0x7a, 0x96, 0xd3, 0x72, 0x12, 0xbc, 0x20, 0x4d, 0x7c, 0xfa, 0x15, 0x0c, 0x41, 0x9b, 0xaa, 0x09, 0xf8, 0xf0,
  0x5d, 0x84, 0xfc, 0x0e, 0xd6, 0xa0, 0xf2, 0xef, 0x4e, 0x10, 0xbf, 0x89, 0x6d, 0x9c, 0x98, 0x06, 0xc2, 0xc7, 0x5a,
  0xf1, 0xb1, 0xa5, 0xf4, 0xb9, 0xa2, 0xf5, 0x78, 0xae, 0x3d, 0x24, 0xfb, 0x30, 0x9d, 0xd8, 0xa4, 0x6f, 0x1f, 0x49,
  0xd0, 0x95, 0x3c, 0x99, 0xba, 0x23, 0xea, 0x53, 0x14, 0x2b, 0xe0, 0x0d, 0x5b, 0x94, 0x38, 0x4b, 0x1c, 0xcc, 0x4c,
  0x88, 0x2c, 0x81, 0xf3, 0x9e, 0x70, 0xf6, 0x58, 0x45, 0xb0, 0x35, 0x5f, 0x6a, 0x8a, 0x32, 0x19, 0x34, 0xdd, 0x4f,
  0x7d, 0x36, 0xee, 0xab, 0x75, 0x71, 0x0f, 0x25, 0xb5, 0xe9, 0x47, 0xf7, 0xcf, 0x43, 0x6c, 0xc6, 0x8f, 0x31, 0xb2,
  0x2f, 0xd9, 0x1d, 0xc4, 0xa8, 0xd4, 0x93, 0x73, 0xa7, 0x82, 0x77, 0x66, 0x08, 0x6b, 0x01, 0xa9, 0xe3, 0xd5, 0xad,
  0xd7, 0xe5, 0x62, 0x86, 0x03, 0x22, 0xb4, 0x2d, 0xd1, 0xdf, 0x3e, 0x7b, 0x52, 0xe2, 0x7e, 0x48, 0xe7, 0x0b, 0x04,
  0xc8, 0x16, 0xc5, 0x02, 0xce, 0x07, 0x74, 0x80, 0x05]
# rsbox = [
#   0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
#   0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
#   0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
#   0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
#   0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
#   0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
#   0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
#   0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
#   0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
#   0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
#   0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
#   0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
#   0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
#   0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
#   0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
#   0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d ]
rsbox = [0, 141, 1, 140, 2, 143, 3, 142, 4, 137, 5, 136, 6, 139, 7, 138, 8, 133, 9, 132, 10, 135, 11, 134, 12, 129, 13, 128, 14, 131, 15, 130, 16, 157, 17, 156, 18, 159, 19, 158, 20, 153, 21, 152, 22, 155, 23, 154, 24, 149, 25, 148, 26, 151, 27, 150, 28, 145, 29, 144, 30, 147, 31, 146, 32, 173, 33, 172, 34, 175, 35, 174, 36, 169, 37, 168, 38, 171, 39, 170, 40, 165, 41, 164, 42, 167, 43, 166, 44, 161, 45, 160, 46, 163, 47, 162, 48, 189, 49, 188, 50, 191, 51, 190, 52, 185, 53, 184, 54, 187, 55, 186, 56, 181, 57, 180, 58, 183, 59, 182, 60, 177, 61, 176, 62, 179, 63, 178, 64, 205, 65, 204, 66, 207, 67, 206, 68, 201, 69, 200, 70, 203, 71, 202, 72, 197, 73, 196, 74, 199, 75, 198, 76, 193, 77, 192, 78, 195, 79, 194, 80, 221, 81, 220, 82, 223, 83, 222, 84, 217, 85, 216, 86, 219, 87, 218, 88, 213, 89, 212, 90, 215, 91, 214, 92, 209, 93, 208, 94, 211, 95, 210, 96, 237, 97, 236, 98, 239, 99, 238, 100, 233, 101, 232, 102, 235, 103, 234, 104, 229, 105, 228, 106, 231, 107, 230, 108, 225, 109, 224, 110, 227, 111, 226, 112, 253, 113, 252, 114, 255, 115, 254, 116, 249, 117, 248, 118, 251, 119, 250, 120, 245, 121, 244, 122, 247, 123, 246, 124, 241, 125, 240, 126, 243, 127, 242]


""" The round constant word array, Rcon[i], contains the values given by
    x to th e power (i-1) being powers of x (x is denoted as {02}) in the field GF(2^8)
    Note that i starts at 1, not 0)."""
Rcon = [
  0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a,
  0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39,
  0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a,
  0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8,
  0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef,
  0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc,
  0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b,
  0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3,
  0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94,
  0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20,
  0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35,
  0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f,
  0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04,
  0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63,
  0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd,
  0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb  ]

def getSBoxValue(num):
  return sbox[num]

def getSBoxInvert(num):
  return rsbox[num]

def KeyExpansion():
  tempa = [0, 0, 0, 0] #Used for the column/row operations

  #The first round key is the key itself.
  for i in range(0, Nk):
    RoundKey[(i * 4) + 0] = Key[(i * 4) + 0]
    RoundKey[(i * 4) + 1] = Key[(i * 4) + 1]
    RoundKey[(i * 4) + 2] = Key[(i * 4) + 2]
    RoundKey[(i * 4) + 3] = Key[(i * 4) + 3]

  i = i+1
  #All other round keys are found from the previous round keys.
  for i in range(i, (Nb * (Nr + 1))):
    for j in range (0, 4):
      tempa[j]=RoundKey[(i-1) * 4 + j]
    if i % Nk == 0:
      #This function rotates the 4 bytes in a word to the left once.
      #[a0,a1,a2,a3] becomes [a1,a2,a3,a0]
      #Function RotWord()
      k = tempa[0]
      tempa[0] = tempa[1]
      tempa[1] = tempa[2]
      tempa[2] = tempa[3]
      tempa[3] = k

      #SubWord() is a function that takes a four-byte input word and
      #applies the S-box to each of the four bytes to produce an output word.

      #Function Subword()
      tempa[0] = getSBoxValue(tempa[0])
      tempa[1] = getSBoxValue(tempa[1])
      tempa[2] = getSBoxValue(tempa[2])
      tempa[3] = getSBoxValue(tempa[3])

      tempa[0] =  tempa[0] ^ Rcon[int(i/Nk)]

    else:
      if (Nk > 6 and i % Nk == 4):
      # Function Subword()
        tempa[0] = getSBoxValue(tempa[0])
        tempa[1] = getSBoxValue(tempa[1])
        tempa[2] = getSBoxValue(tempa[2])
        tempa[3] = getSBoxValue(tempa[3])

    RoundKey[i * 4 + 0] = RoundKey[(i - Nk) * 4 + 0] ^ tempa[0]
    RoundKey[i * 4 + 1] = RoundKey[(i - Nk) * 4 + 1] ^ tempa[1]
    RoundKey[i * 4 + 2] = RoundKey[(i - Nk) * 4 + 2] ^ tempa[2]
    RoundKey[i * 4 + 3] = RoundKey[(i - Nk) * 4 + 3] ^ tempa[3]

#This function adds the round key to state.
#The round key is added to the state by an XOR function.
def AddRoundKey(round):
  for i in range(0,4):
    for j in range(0,4):
      state[i][j] ^= RoundKey[round * Nb * 4 + i * Nb + j]


#The SubBytes Function Substitutes the values in the
#state matrix with values in an S-box.
def SubBytes():
  for i in range(0, 4):
    for j in range(0, 4):
      state[j][i] = getSBoxValue(state[j][i])


#The ShiftRows() function shifts the rows in the state to the left.
#Each row is shifted with different offset.
#Offset = Row number. So the first row is not shifted.
def ShiftRows():
  #Rotate first row 1 columns to left
  temp           = state[0][3]
  state[0][3] = state[1][3]
  state[1][3] = state[2][3]
  state[2][3] = state[3][3]
  state[3][3] = temp

  #Rotate second row 2 columns to left
  temp           = state[0][1]
  state[0][1] = state[2][1]
  state[2][1] = temp

  temp       = state[1][1]
  state[1][1] = state[3][1]
  state[3][1] = temp

  #Rotate third row 3 columns to left
  temp       = state[0][2]
  state[0][2] = state[3][2]
  state[3][2] = state[2][2]
  state[2][2] = state[1][2]
  state[1][2] = temp

def xtime(x):
  return (((x<<1) ^ (((x>>7) & 1) * 0x1b))%256)

#MixColumns function mixes the columns of the state matrix
def MixColumns():
  for i in range(0,4):
    t   = state[i][0]
    Tmp = state[i][0] ^ state[i][1] ^ state[i][2] ^ state[i][3]
    Tm  = state[i][0] ^ state[i][1]
    Tm = xtime(Tm)
    state[i][0] ^= Tm ^ Tmp
    Tm  = state[i][1] ^ state[i][2]
    Tm = xtime(Tm)
    state[i][1] ^= Tm ^ Tmp
    Tm  = state[i][2] ^ state[i][3]
    Tm = xtime(Tm)
    state[i][2] ^= Tm ^ Tmp
    Tm  = state[i][3] ^ t
    Tm = xtime(Tm)
    state[i][3] ^= Tm ^ Tmp

#Multiply is used to multiply numbers in the field GF(2^8)
def Multiply(x, y):
  return (((y & 1) * x) ^
       ((y>>1 & 1) * xtime(x)) ^
       ((y>>2 & 1) * xtime(xtime(x))) ^
       ((y>>3 & 1) * xtime(xtime(xtime(x)))) ^
       ((y>>4 & 1) * xtime(xtime(xtime(xtime(x))))))

#MixColumns function mixes the columns of the state matrix.
#The method used to multiply may be difficult to understand for the inexperienced.
#Please use the references to gain more information.
def InvMixColumns():
  for i in range(0,4):
    a = state[i][0]
    b = state[i][1]
    c = state[i][2]
    d = state[i][3]

    state[i][0] = Multiply(a, 0x0e) ^ Multiply(b, 0x0b) ^ Multiply(c, 0x0d) ^ Multiply(d, 0x09)
    state[i][1] = Multiply(a, 0x09) ^ Multiply(b, 0x0e) ^ Multiply(c, 0x0b) ^ Multiply(d, 0x0d)
    state[i][2] = Multiply(a, 0x0d) ^ Multiply(b, 0x09) ^ Multiply(c, 0x0e) ^ Multiply(d, 0x0b)
    state[i][3] = Multiply(a, 0x0b) ^ Multiply(b, 0x0d) ^ Multiply(c, 0x09) ^ Multiply(d, 0x0e)


#The SubBytes Function Substitutes the values in the
#state matrix with values in an S-box.
def InvSubBytes():
  for i in range(0,4):
    for j in range(0,4):
      try:
          state[j][i] = getSBoxInvert(state[j][i])
      except:
          pass


def InvShiftRows():
  #Rotate first row 1 columns to right
  temp=state[3][1]
  state[3][1]=state[2][1]
  state[2][1]=state[1][1]
  state[1][1]=state[0][1]
  state[0][1]=temp

  #Rotate second row 2 columns to right
  temp=state[0][2]
  state[0][2]=state[2][2]
  state[2][2]=temp

  temp=state[1][2]
  state[1][2]=state[3][2]
  state[3][2]=temp

  #Rotate third row 3 columns to right
  temp=state[0][3]
  state[0][3]=state[1][3]
  state[1][3]=state[2][3]
  state[2][3]=state[3][3]
  state[3][3]=temp


def Reorder():
  tmp = [ [0]*4 for _ in range(4) ]
  for i in range(4):
    for j in range(4):
      tmp[j][i] = state[i][j]

  for i in range(4):
    for j in range(4):
      state[i][j] = tmp[i][j]


#Cipher is the main function that encrypts the PlainText.
def Cipher():
  #Add the First round key to the state before starting the rounds.
  AddRoundKey(0)

  SubBytes()
  ShiftRows()
  Reorder()
  MixColumns()
  Reorder()
  AddRoundKey(1)

  #The last round is given below.
  #The MixColumns function is not here in the last round.
  SubBytes()
  ShiftRows()
  AddRoundKey(2)
  AddRoundKey(1)

def InvCipher():
  #Add the First round key to the state before starting the rounds.
  AddRoundKey(Nr)

  #There will be Nr rounds.
  #The first Nr-1 rounds are identical.
  #These Nr-1 rounds are executed in the loop below.
  for round in range(Nr-1, 0, -1):
    InvShiftRows()
    InvSubBytes()
    AddRoundKey(round)
    InvMixColumns()

  #The last round is given below.
  #The MixColumns function is not here in the last round.
  InvShiftRows()
  InvSubBytes()
  AddRoundKey(0)


"""
Public functions:
"""
def AES128_ECB_encrypt(input, key, output):
  #Copy input to output, and work in-memory on output
  for i in range(0,4):
    for j in range(0, 4):
      state[i][j] = input[4*i + j]

  Key = key
  KeyExpansion()

  #The next function call encrypts the PlainText with the Key using AES algorithm.
  Cipher()
  for i in range(0, 4):
    for j in range (0, 4):
      output[4*i+j] = state[i][j]

def AES128_ECB_decrypt(input, key, output):
  #Copy input to output, and work in-memory on output
  for i in range(0,4):
    for j in range(0, 4):
      state[i][j] = input[4*i + j]

  #The KeyExpansion routine must be called before encryption.
  global Key
  Key = key
  KeyExpansion()

  InvCipher()
  for i in range(0, 4):
    for j in range (0, 4):
      output[4*i+j] = state[i][j]



def XorWithIv(buf):
  for i in range(0, KEYLEN):
    buf[i] ^= Iv[i]

def AES128_CBC_encrypt_buffer(output, input, length, key, iv):
  remainders = length % KEYLEN #Remaining bytes in the last non-full block

  #Skip the key expansion if key is passed as 0
  if 0 != key:
    global Key
    Key = key
    KeyExpansion()

  if iv != 0:
    global Iv
    Iv = iv

  tmpOut = [0] * 16
  for i in range(0, length, KEYLEN):
    tmp = input[i:]
    XorWithIv(tmp)
    for j in range(0,4):
      for k in range(0, 4):
        state[j][k] = tmp[4*j + k]
    Cipher()
    for j in range(0, 4):
      for k in range (0, 4):
        tmpOut[4*j+k] = state[j][k]
    Iv = tmpOut
    output[i:] = tmpOut

  if remainders != 0: #NOT TESTED
    output[remainders:] = [0] * (KEYLEN - remainders) #add 0-padding
    for i in range(0,4):
      for j in range(0, 4):
        state[i][j] = input[4*i + j]
    Cipher()



def AES128_CBC_decrypt_buffer(output, input, length, key, iv):

  remainders = length % KEYLEN #Remaining bytes in the last non-full block

  #Skip the key expansion if key is passed as 0
  if 0 != key:
    global Key
    Key = key
    KeyExpansion()

  #If iv is passed as 0, we continue to encrypt without re-setting the Iv
  if iv != 0:
    global Iv
    Iv = iv

  tmp = [0] * 16
  for i in range(0, length, KEYLEN):
    for j in range(0,4):
      for k in range(0, 4):
        state[j][k] = input[4*j + k]
    InvCipher()
    for j in range(0, 4):
      for k in range (0, 4):
        tmp[4*j+k] = state[j][k]
    XorWithIv(tmp)
    output[i:] = tmp
    Iv = input
    input = input[KEYLEN:]

  if remainders != 0: #REVIEW, NOT TESTED!!
    output[remainders:] = [0] * (KEYLEN - remainders) #add 0-padding
    for i in range(0,4):
      for j in range(0, 4):
        state[i][j] = output[4*i + j]
    InvCipher()


def AES128_CBC_encrypt_block(output, input, key):
  #Skip the key expansion if key is passed as 0
  if(0 != key):
    global Key
    Key = key
    KeyExpansion()
  for i in range(0,4):
    for j in range(0, 4):
      state[i][j] = input[4*i + j]
  Cipher()
  for i in range(0, 4):
    for j in range (0, 4):
      output[4*i+j] = state[i][j]

def LeftShift1Bit(buffer):
    carry = 0
    for i in range(KEYLEN-1, -1, -1):
        cc = carry
        carry = (buffer[i] & 0x80) != 0
        buffer[i] = (buffer[i] << 1)%256 + cc




