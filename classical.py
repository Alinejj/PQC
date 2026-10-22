""" 
The RSA and ECDSA functions have the same shapes as `KEMScheme` and `SigScheme` in 
benchmarks/schemes.py, so they can be plugged into the benchmark directly:

- RSA key exchange, 
`KEMScheme`: keygen = `rsa_keygen`, encaps = `rsa_encap`, 
    decaps = `rsa_decap`, public_key_bytes = `rsa_public_bytes`

- RSA signatures, 
`SigScheme`: keygen = `rsa_keygen`, sign = `rsa_sign`, 
    verify = `rsa_verify`, public_key_bytes = `rsa_public_bytes`

- ECDSA P-256 signatures, 
`SigScheme`: keygen = `ecdsa_keygen`, sign = `ecdsa_sign`, 
    verify = `ecdsa_verify`, public_key_bytes = `ecdsa_public_bytes`

Note: `rsa_keygen()` makes 3072-bit keys by default, and the benchmark calls `keygen()` 
with no arguments. 
"""
 
import os
 
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# AES ---------------------------------------------------------------

def aes_aes_(bits=256):
    return AESGCM.generate_key(bit_length=bits)
 
def aes_encrypt(key, plaintext):
    """Lock a message (bytes). Returns (nonce, ciphertext)."""
    nonce = os.urandom(12)  # new random value for EVERY message; never reuse one
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return nonce, ciphertext
 
def aes_decrypt(key, nonce, ciphertext):
    """Unlock a message. Raises InvalidTag if anything was changed."""
    return AESGCM(key).decrypt(nonce, ciphertext, None)
 
 
# RSA ---------------------------------------------------------------
 
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH)
 
 
def rsa_aes_(bits=3072):
    """Make an RSA key pair. Returns (private_key, public_key)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    return private_key, private_key.public_key()
 
def rsa_encap(public_key):
    aes_key = aes_aes_()
    locked_key = public_key.encrypt(aes_key, OAEP)
    return locked_key, aes_key
 
def rsa_decap(private_key, locked_key):
    return private_key.decrypt(locked_key, OAEP)
 
def rsa_sign(private_key, message):
    return private_key.sign(message, PSS, hashes.SHA256())
 
def rsa_verify(public_key, signature, message):
    try:
        public_key.verify(signature, message, PSS, hashes.SHA256())
        return True
    except InvalidSignature:
        return False
 
def rsa_public_bytes(public_key):
    return public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.PKCS1)

# ECDSA ---------------------------------------------------------------

def ecdsa_aes_():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key, private_key.public_key()
 
def ecdsa_sign(private_key, message):
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))
 
def ecdsa_verify(public_key, signature, message):
    try:
        public_key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False
 
def ecdsa_public_bytes(public_key):
    return public_key.public_bytes(serialization.Encoding.X962,
                                   serialization.PublicFormat.UncompressedPoint)