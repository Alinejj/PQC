import hashlib as h
from Crypto.PublicKey import RSA as r
from hashlib import sha1
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# RSA.generate(2048) in a comment should not count
key = r.generate(2048)
digest = h.md5(b"data").hexdigest()
old = sha1(b"data")
cipher = Cipher(
    algorithms.AES(key_bytes),
    modes.CBC(iv),
)