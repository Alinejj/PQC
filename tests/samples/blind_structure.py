# blind_structure.py

import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa


# S1a: call in an IF Condition
password = "secret123"
expected_hash = "fcf730b6d95236ecd3c9fc2d92d7b6b2bb061514961aec041d6c7a7192f592e4"

if hashlib.sha256(password.encode()).hexdigest() == expected_hash:
    print("Correct")
else:
    print("False")

# S1b: call in an If Body
if True:
    result = hashlib.sha256(b"secret456").hexdigest()

# S2a: call in a While Condition
data = b"Hello, World!"
expected = "65a8e27d8879283831b664bd8b7f0ad4"

while hashlib.md5(data).hexdigest() == expected:
    break

# S2b: call in a While Body
while True:
    aes_gcm = AESGCM(os.urandom(32))
    break

# S3a: call in a Try Body
try:
    private_key1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
except Exception:
    pass

# S3b: call in an Except Body
try:
    raise ValueError("Test exception") # Would it still count if an exception wasn't raise??
except Exception:
    private_key2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# S4: Call inside a function
def generate_key():
    private_key3 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key3

