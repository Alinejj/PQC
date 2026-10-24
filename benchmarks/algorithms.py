import ctypes.util
import importlib.util
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, mldsa, mlkem, x25519

import classical
from benchmarks.schemes import KEMScheme, SigScheme

RAW = (serialization.Encoding.Raw, serialization.PublicFormat.Raw)


# Importing oqs without the liboqs C library makes it try to download and
# build liboqs, which fails without CMake and a C compiler. So check for the
# library first, in the same places liboqs-python looks for it.
def _liboqs_installed():
    if importlib.util.find_spec("oqs") is None:
        return False
    return ("OQS_INSTALL_PATH" in os.environ
            or (Path.home() / "_oqs").exists()
            or ctypes.util.find_library("oqs") is not None)


# ML-KEM and ML-DSA come from the demo app's PQC_service when liboqs is
# installed, and from the cryptography library otherwise.
PQC_BACKEND = "liboqs" if _liboqs_installed() else "cryptography"
if PQC_BACKEND == "liboqs":
    from PQC_service import mldsa as pqc_mldsa, mlkem as pqc_mlkem


def _keypair(private_key):
    return private_key, private_key.public_key()


def _raw(public_key):
    return public_key.public_bytes(*RAW)


def _p256_bytes(public_key):
    return public_key.public_bytes(serialization.Encoding.X962,
                                   serialization.PublicFormat.UncompressedPoint)


def _checked(verify_fn):
    def verify(public_key, signature, message):
        try:
            verify_fn(public_key, signature, message)
            return True
        except InvalidSignature:
            return False
    return verify


# Classical key exchange is framed as a KEM so it lines up with ML-KEM:
# RSA-OAEP encrypts a fresh 32-byte AES key (key transport), and ECDH uses an
# ephemeral key pair whose public key plays the role of the ciphertext.
# RSA and ECDSA come from the demo app's classical.py.

def _rsa_kem(bits):
    return KEMScheme(
        name=f"RSA-{bits} (OAEP)",
        family="classical",
        keygen=lambda: classical.rsa_keygen(bits),
        encaps=classical.rsa_encap,
        decaps=classical.rsa_decap,
        public_key_bytes=classical.rsa_public_bytes,
    )


def _x25519_encaps(pk):
    eph = x25519.X25519PrivateKey.generate()
    return _raw(eph.public_key()), eph.exchange(pk)


def _x25519_decaps(sk, ct):
    return sk.exchange(x25519.X25519PublicKey.from_public_bytes(ct))


def _p256_encaps(pk):
    eph = ec.generate_private_key(ec.SECP256R1())
    return _p256_bytes(eph.public_key()), eph.exchange(ec.ECDH(), pk)


def _p256_decaps(sk, ct):
    peer = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ct)
    return sk.exchange(ec.ECDH(), peer)


def _mlkem(level, key_class):
    if PQC_BACKEND == "liboqs":
        return _mlkem_liboqs(level)

    def encaps(pk):
        shared_secret, ciphertext = pk.encapsulate()
        return ciphertext, shared_secret
    return KEMScheme(
        name=f"ML-KEM-{level}",
        family="pqc",
        keygen=lambda: _keypair(key_class.generate()),
        encaps=encaps,
        decaps=lambda sk, ct: sk.decapsulate(ct),
        public_key_bytes=_raw,
    )


# PQC_service returns (public_key, secret_key) as bytes and takes arguments in
# a different order, so these adapt it to the KEMScheme and SigScheme shapes.

def _mlkem_liboqs(level):
    alg = f"ML-KEM-{level}"

    def keygen():
        pk, sk = pqc_mlkem.generate_kem_keypair(alg)
        return sk, pk
    return KEMScheme(
        name=alg,
        family="pqc",
        keygen=keygen,
        encaps=lambda pk: pqc_mlkem.encapsulate(pk, alg),
        decaps=lambda sk, ct: pqc_mlkem.decapsulate(ct, sk, alg),
        public_key_bytes=lambda pk: pk,
    )


def _mldsa_liboqs(level):
    alg = f"ML-DSA-{level}"

    def keygen():
        pk, sk = pqc_mldsa.generate_dsa_keypair(alg)
        return sk, pk
    return SigScheme(
        name=alg,
        family="pqc",
        keygen=keygen,
        sign=lambda sk, msg: pqc_mldsa.sign_message(msg, sk, alg),
        verify=lambda pk, sig, msg: pqc_mldsa.verify_signature(msg, sig, pk, alg),
        public_key_bytes=lambda pk: pk,
    )


KEM_SCHEMES = [
    _rsa_kem(2048),
    _rsa_kem(3072),
    KEMScheme("ECDH X25519", "classical",
              lambda: _keypair(x25519.X25519PrivateKey.generate()),
              _x25519_encaps, _x25519_decaps, _raw),
    KEMScheme("ECDH P-256", "classical",
              lambda: _keypair(ec.generate_private_key(ec.SECP256R1())),
              _p256_encaps, _p256_decaps, _p256_bytes),
    _mlkem(768, mlkem.MLKEM768PrivateKey),
    _mlkem(1024, mlkem.MLKEM1024PrivateKey),
]


def _rsa_sig(bits):
    return SigScheme(
        name=f"RSA-{bits} (PSS)",
        family="classical",
        keygen=lambda: classical.rsa_keygen(bits),
        sign=classical.rsa_sign,
        verify=classical.rsa_verify,
        public_key_bytes=classical.rsa_public_bytes,
    )


def _mldsa(level, key_class):
    if PQC_BACKEND == "liboqs":
        return _mldsa_liboqs(level)
    return SigScheme(
        name=f"ML-DSA-{level}",
        family="pqc",
        keygen=lambda: _keypair(key_class.generate()),
        sign=lambda sk, msg: sk.sign(msg),
        verify=_checked(lambda pk, sig, msg: pk.verify(sig, msg)),
        public_key_bytes=_raw,
    )


SIG_SCHEMES = [
    _rsa_sig(2048),
    _rsa_sig(3072),
    SigScheme("ECDSA P-256", "classical",
              classical.ecdsa_keygen, classical.ecdsa_sign,
              classical.ecdsa_verify, classical.ecdsa_public_bytes),
    SigScheme("Ed25519", "classical",
              lambda: _keypair(ed25519.Ed25519PrivateKey.generate()),
              lambda sk, msg: sk.sign(msg),
              _checked(lambda pk, sig, msg: pk.verify(sig, msg)),
              _raw),
    _mldsa(44, mldsa.MLDSA44PrivateKey),
    _mldsa(65, mldsa.MLDSA65PrivateKey),
    _mldsa(87, mldsa.MLDSA87PrivateKey),
]
