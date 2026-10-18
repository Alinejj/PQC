import hashlib
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# asymmetric
rsa_2048 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
rsa_1024 = rsa.generate_private_key(public_exponent=65537, key_size=1024)
ecdsa_key = ec.generate_private_key(ec.SECP256R1())
ed_key = ed25519.Ed25519PrivateKey.generate()
signature = ecdsa_key.sign(b"msg", ec.ECDSA(hashes.SHA256()))

# symmetric
aes_gcm = AESGCM(os.urandom(32))
aes_cbc = Cipher(algorithms.AES(os.urandom(32)), modes.CBC(os.urandom(16)))
des_cbc = Cipher(algorithms.TripleDES(os.urandom(24)), modes.CBC(os.urandom(8)))

# hashes
md5_digest = hashlib.md5(b"data").hexdigest()
sha1_digest = hashlib.sha1(b"data").hexdigest()
sha256_digest = hashlib.sha256(b"data").hexdigest()
sha512_digest = hashlib.sha512(b"data").hexdigest()

# key exchange
tls_groups = "X25519MLKEM768:X25519:prime256v1"