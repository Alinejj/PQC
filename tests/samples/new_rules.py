import oqs
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

sig = oqs.Signature("ML-DSA-65")
kem = oqs.KeyEncapsulation("ML-KEM-768")
oaep = padding.OAEP(mgf=None, algorithm=None, label=None)
key = AESGCM.generate_key(bit_length=256)