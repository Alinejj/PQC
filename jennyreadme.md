# PQC-Ready: Classical Cryptography for the Demo App

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module is the classical half of the demo application. It implements AES-GCM, RSA and ECDSA with the `cryptography` package, and it serves three purposes in the project: it provides the classical security functions for the demo (sending an encrypted message and signing data), it is the classical side that the benchmark compares ML-KEM and ML-DSA against, and it gives the scanner real, working classical cryptography to find.


## Why this exists

RSA and elliptic-curve algorithms such as ECDSA are the public-key cryptography that Shor's algorithm breaks, so they are what a post-quantum migration replaces: ML-KEM takes over RSA's job of delivering keys, and ML-DSA takes over signing. For the comparison to be fair, the classical side has to be built the way a careful developer would build it today, with modern padding, authenticated encryption and fresh random values. Then any difference the project measures comes from the algorithms themselves rather than from implementation mistakes, and the scanner's findings show that even well-built classical cryptography is quantum-vulnerable.

AES is included because both sides need it. A key exchange, classical or post-quantum, only delivers a shared secret; AES is what actually encrypts the message with that secret. AES is not replaced in the migration, since 256-bit AES keys are expected to stay secure against quantum computers.

## How to run

The only dependency is the `cryptography` package. The team uses version 50 or newer because the benchmark needs its ML-KEM and ML-DSA support. This module was tested with Python 3.13 and cryptography 50.0.1.

```
pip install cryptography
```

## Project layout
             

## What's implemented

| Algorithm | Functions | Job | Settings |
|---|---|---|---|
| AES-GCM | `aes_keygen`, `aes_encrypt`, `aes_decrypt` | Encrypts the actual message | 256-bit key by default, a fresh random 12-byte nonce per message, 16-byte authentication tag |
| RSA-OAEP | `rsa_keygen`, `rsa_encaps`, `rsa_decaps` | Delivers a fresh AES key to the receiver | 2048 or 3072 bits (default 3072), public exponent 65537, OAEP with SHA-256 |
| RSA-PSS | `rsa_keygen`, `rsa_sign`, `rsa_verify` | Signs messages | PSS with SHA-256, salt length equal to the hash length |
| ECDSA | `ecdsa_keygen`, `ecdsa_sign`, `ecdsa_verify` | Signs messages | P-256 curve, SHA-256 |

`rsa_public_bytes` and `ecdsa_public_bytes` return a public key as bytes so its size can be measured: PKCS#1 DER for RSA and an uncompressed point for P-256, the same formats the benchmark uses.

## Function shapes

The RSA and ECDSA functions follow the `KEMScheme` and `SigScheme` shapes in `benchmarks/schemes.py`, so the benchmark can call them directly. The AES functions are not part of the benchmark. Every function in the module, by its exact name:

```
# RSA
rsa_keygen(bits=3072)                        -> (private_key, public_key)
rsa_encaps(public_key)                       -> (locked_key, aes_key)
rsa_decaps(private_key, locked_key)          -> aes_key
rsa_sign(private_key, message)               -> signature
rsa_verify(public_key, signature, message)   -> True or False
rsa_public_bytes(public_key)                 -> bytes

# ECDSA
ecdsa_keygen()                               -> (private_key, public_key)
ecdsa_sign(private_key, message)             -> signature
ecdsa_verify(public_key, signature, message) -> True or False
ecdsa_public_bytes(public_key)               -> bytes

# AES
aes_keygen(bits=256)                         -> key
aes_encrypt(key, plaintext)                  -> (nonce, ciphertext)
aes_decrypt(key, nonce, ciphertext)          -> plaintext
```

## How it works

**Sending an encrypted message.** RSA is framed as a key encapsulation mechanism so it lines up with ML-KEM. The sender calls `rsa_encaps` with the receiver's public key, which generates a fresh 32-byte AES key and encrypts it with RSA-OAEP. The sender then encrypts the message with `aes_encrypt` and sends three things: the locked AES key, the nonce and the ciphertext. The receiver recovers the AES key with `rsa_decaps` and decrypts with `aes_decrypt`. The post-quantum version is the same flow with ML-KEM in place of RSA, since ML-KEM's 32-byte shared secret can be used directly as the AES-256 key.

**Signing.** The signer calls `rsa_sign` or `ecdsa_sign` with their private key, and anyone with the matching public key can check the result with `rsa_verify` or `ecdsa_verify`. The verify functions return `False` for a bad signature instead of raising an exception, which is what the benchmark's runner expects.

**Choices that keep it secure.** OAEP and PSS are the recommended padding schemes for RSA encryption and signatures; the older PKCS#1 v1.5 schemes are avoided. AES-GCM is authenticated encryption, so changing even one bit of a message makes `aes_decrypt` raise `InvalidTag` instead of returning garbage. A GCM nonce must never repeat under the same key, so every call to `aes_encrypt` draws a new random one. The self-check uses separate RSA key pairs for encryption and signing, which is standard practice.

## Results so far

**Benchmark integration.** The functions were plugged into `KEMScheme` and `SigScheme` and run through `bench_kem` and `bench_sig` from the benchmark on the laasya branch. All five schemes passed the runner's correctness checks: both sides end up with the same secret, real signatures verify, and tampered messages fail. Sizes match the benchmark's own implementations exactly, and median timings were within normal run-to-run variation of them.

| Scheme | Public key (bytes) | Ciphertext or signature (bytes) |
|---|---|---|
| RSA-2048 (OAEP) | 270 | 256 |
| RSA-3072 (OAEP) | 398 | 384 |
| RSA-2048 (PSS) | 270 | 256 |
| RSA-3072 (PSS) | 398 | 384 |
| ECDSA P-256 | 65 | 70 to 72 |

For comparison, the benchmark measures an ML-KEM-768 ciphertext at 1,088 bytes and an ML-DSA-44 signature at 2,420 bytes. Official timing numbers come from the benchmark; see `laasyareadme.md`.

**Scanner results.** Running the scanner on this folder (`python main.py demo_app`) gives 12 findings: RSA and ECDSA marked vulnerable, AES-GCM and SHA-256 marked safe. The line numbers below are for the current version of `classical.py` and can serve as a starting point for the ground-truth list.

| Line | Crypto use | Scanner result |
|---|---|---|
| 31 | AES key generation | not reported |
| 37, 43 | AES-GCM encrypt, decrypt | AES-GCM, safe |
| 51, 52 | OAEP and PSS settings (SHA-256) | SHA-256, safe |
| 57 | RSA key generation | RSA, vulnerable |
| 65, 71 | RSA-OAEP encrypt, decrypt | not reported |
| 76, 82 | RSA-PSS sign, verify | SHA-256, safe |
| 100 | ECDSA P-256 key generation | ECDSA/ECDH, vulnerable |
| 106, 112 | ECDSA sign, verify | ECDSA/ECDH, vulnerable, and SHA-256, safe |

The scanner finds every algorithm in the file, but RSA is tied only to its key generation line. The OAEP and PSS lines are reported as SHA-256, and the encrypt, decrypt, sign and verify calls on RSA keys are not reported, while ECDSA is reported on three lines. Rules matching `padding.OAEP` and `padding.PSS` (for RSA) and `AESGCM.generate_key` (for AES-GCM) would close these gaps. When comparing against the ground-truth list, it is worth deciding whether findings count per line or per algorithm.

## Known limitations

Keys exist only in memory. There is no saving or loading of keys to files and no password protection, which a real application would need. There is also no user-facing application yet; the module provides the building blocks (an encrypted message and signatures) that a demo would call. Messages must be bytes, so text needs `.encode()` first. Nothing stops a caller from using the same RSA key pair for both encryption and signing, though separate pairs are the recommended practice. Random 12-byte nonces are safe at this project's scale; NIST guidance caps random nonces at about four billion messages per key. AES is not part of the benchmark, since it is identical on the classical and post-quantum sides.
