# blind_decoys.py: every test below should produce NO findings
# D7
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


# D1
x = 5 # To do: rsa.generate_private_key()

# D2a
def test():
    """Hash the password using sha-256."""
    return

# D2b
"""Hash the password using SHA-256."""

# D3
def md5():
    pass

# D4

# D4a: lvl 1
print("using rsa for signing")

# D4b: lvl 2
print("rsa.generate_private_key")

# D4c: lvl 3
print("rsa.generate_private_key(public_exponent=65537, key_size=2048)")

# D4d: lvl 4
print("X25519MLKEM768:X25519:prime256v1")

# D5
class Tester:
    # D5a1
    def sha1(self):
        pass

    # D5b1
    def generate_private_key(self):
        pass

    # D5c1
    def sign(self):
        pass

    # D5d1
    def sha256(self):
        return 123


myPassword = Tester()

# D5a2
myPassword.sha1()

# D5a3
hashlib = Tester()
hashlib.sha1() # <----- the test line for D5a3

# D5b2
rsa = Tester()
rsa.generate_private_key() # <----- the test line for D5b2

# D5c2
ecdsa_key = Tester()
ecdsa_key.sign() # <----- the test line for D5c2

# D5d2
sha256_digest = hashlib.sha256()

# D6
ec = 0