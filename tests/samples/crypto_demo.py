import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
h = hashlib.md5(b"hi")
groups = "X25519MLKEM768:X25519"