import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
import logging

@some.decorator(hashlib.md5())
def f(h=hashlib.sha1()):
    if hashlib.md5(b"x").digest():
        pass
    while rsa.generate_private_key(public_exponent=65537, key_size=2048):
        break
    for k in [rsa.generate_private_key(public_exponent=3, key_size=512)]:
        pass
    with open("a") as fh, hashlib.sha256() as h2:
        pass
    try:
        pass
    except hashlib.md5:
        pass
    logging.info("using rsa.generate_private_key")
    ctx.set_groups("X25519:prime256v1")