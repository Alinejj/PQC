import hashlib
import ssl
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from Crypto.Cipher import AES, Blowfish

key1 = generate_private_key(public_exponent=65537, key_size=3072)
key2 = dsa.generate_private_key(key_size=2048)
digest1 = hashlib.new("md5", b"data")
digest2 = hashlib.sha3_256(b"data")
digest3 = hashlib.blake2b(b"data")
fernet = Fernet(Fernet.generate_key())
chacha = Cipher(algorithms.ChaCha20(b"k" * 32, b"n" * 16), mode=None)
blow = Blowfish.new(b"sixteen byte key", Blowfish.MODE_ECB)
aes = AES.new(b"k" * 16, AES.MODE_CBC)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)