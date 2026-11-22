# blind_algorithms.py
# The purpose is to test other crypto algorithms that the existing tests do not cover
# Every test below should produce a finding
# This was written without reference to the scanner's rules

import hmac
import hashlib
from Crypto.Cipher import AES, DES, ARC4
from cryptography.hazmat.primitives.asymmetric import dh
import bcrypt
from argon2 import PasswordHasher

# shared inputs
key = b"key" * 16
key2 = b"key2" * 8
message = b"example message" * 16
password = b"example password" * 16
salt = b"example salt" * 16

# A1 (AES-ECB)
AES.new(key, AES.MODE_ECB)

# A2 (A2a and A2b: both HMAC and SHA256 should be flagged)
hmac.new(key, message, hashlib.sha256)

# A3 (Diffie-Hellman)
dh.generate_parameters(generator=2, key_size=2048)

# A4 (DES)
DES.new(key2, DES.MODE_CBC)

# A5 (RC4)
ARC4.new(key)

# A6 (bcrypt)
bcrypt.hashpw(password, bcrypt.gensalt())

# A7 (Argon2)
ph = PasswordHasher()
hashed = ph.hash(password)

# A8 (scrypt)
hashlib.scrypt(password, salt=salt, n=16384, r=8, p=1)