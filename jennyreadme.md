# PQC-Ready: Classical Cryptography

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module is the classical half of the demo application. It implements AES-GCM, RSA, and ECDSA with the `cryptography` library. It provides classical security functions (sending an encrypted message and signing data) and gives the scanner classical cryptography to find.


## Why this exists

Shor's algorithm breaks widely used public-key cryptography, including RSA and algorithms like ECDSA. ML-KEM takes over RSA's job of delivering keys and ML-DSA takes over digital signatures. The scanner shows that even well implemented classical cryptography remains vulnerable to quantum attacks, since the vulnerability lies in the algorithm rather than the implementation. Once a key exchange is complete, symmetric algorithms like AES are used to encrypt the actual message. Unlike public-key algorithms, AES is expected to stay secure against quantum computers.

## How to run

The only dependency is the `cryptography` package. It was tested on Python 3.13 on Windows with `cryptography` 50.0.2.

```
pip install cryptography
```

From the project root:

```
python main.py classical.py
```

classical.py does not print anything when run on its own: it is a set of functions for the demo app and the benchmark to import, and the docstring at the top of the file lists which function fills each benchmark slot. The command above runs the scanner on it; its output is described under Results so far.

## Project layout

```
classical.py               AES-GCM, RSA and ECDSA functions
    aes_keygen             makes a 256-bit AES key
    aes_encrypt            locks a message, returns (nonce, ciphertext)
    aes_decrypt            unlocks it, raises InvalidTag if anything was changed
    rsa_keygen             makes an RSA key pair, 3072 bits unless given a size
    rsa_encap              locks a fresh AES key with someone's RSA public key
    rsa_decap              unlocks that AES key with the RSA private key
    rsa_sign               signs a message with RSA-PSS
    rsa_verify             checks an RSA-PSS signature, returns True or False
    ecdsa_keygen           makes an ECDSA key pair on the P-256 curve
    ecdsa_sign             signs a message with ECDSA
    ecdsa_verify           checks an ECDSA signature, returns True or False
    rsa_public_bytes       an RSA public key as bytes, for measuring its size
    ecdsa_public_bytes     an ECDSA public key as bytes, for measuring its size
```

## How it works

`aes_keygen` makes a 256-bit AES key. Grover's algorithm lets a quantum computer roughly halve the strength of a symmetric key, so a 256-bit key still leaves about 128 bits of security; the scanner's AES-GCM rule also recommends 256-bit keys. `aes_encrypt` picks a new random 12-byte nonce for every message and returns it with the ciphertext. The nonce does not need to be secret, but it must never be reused with the same key. GCM adds a 16-byte authentication tag to the ciphertext, so an 11-byte message locks to 27 bytes, and `aes_decrypt` raises `InvalidTag` instead of returning a message that was changed.

RSA can only lock a few hundred bytes and is slow, so it is used to deliver an AES key rather than to lock the message itself. `rsa_encap` makes a fresh 256-bit AES key and locks it with the receiver's public key using OAEP padding with SHA-256, and `rsa_decap` unlocks it with the private key. From then on both sides use that key with `aes_encrypt` and `aes_decrypt`. This is the same job ML-KEM does, so the functions are named after a KEM's encapsulate and decapsulate steps, and the 32-byte AES key plays the role of the shared secret. Signatures use PSS padding with SHA-256 and a salt as long as the hash. Keys use the standard public exponent 65537 and are 3072 bits by default, the size NIST pairs with 128-bit security. The benchmark also measures 2048-bit keys, which NIST rates at 112 bits.

`ecdsa_keygen` makes a key pair on the P-256 curve (also called secp256r1 or prime256v1), and signing hashes the message with SHA-256. ECDSA does the same job as RSA signatures with much smaller keys and signatures; the sizes are under Results so far.

Both verify functions return True or False instead of raising an exception, which is what the benchmark expects. All of the settings above match `benchmarks/algorithms.py`, including the byte formats used to measure public keys (PKCS#1 DER for RSA and an uncompressed point for P-256), so results from classical.py and from the benchmark's own code can be compared directly.

## Results so far

Running the scanner on this file gives 12 findings. Both of the scanner's passes find the same 12, and nothing is picked up from comments or docstrings.

| Algorithm | Status | Found in |
|---|---|---|
| RSA | vulnerable | `rsa_keygen` |
| ECDSA/ECDH | vulnerable | `ecdsa_keygen`, `ecdsa_sign`, `ecdsa_verify` |
| AES-GCM | safe | `aes_encrypt`, `aes_decrypt` |
| SHA-256 | safe | the OAEP and PSS settings, `rsa_sign`, `rsa_verify`, `ecdsa_sign`, `ecdsa_verify` |

This is the result the module was written to show. RSA and ECDSA are flagged as vulnerable even though they are used correctly, with modern padding and key sizes, while AES-256-GCM and SHA-256 are marked safe.

The benchmark does not call classical.py yet; the classical and PQC parts of the demo app will be plugged into it once they are ready. To check that classical.py is ready, the benchmark's RSA-2048 and RSA-3072 (OAEP), RSA-2048 and RSA-3072 (PSS) and ECDSA P-256 entries were rebuilt from its functions, using the slots listed in its docstring, and run through the benchmark's own runner. All five passed the runner's correctness checks: both sides end up with the same secret, a real signature verifies, and a signature fails to verify against a changed message. The sizes match the benchmark's own code:

| Algorithm | Public key (bytes) | Ciphertext or signature (bytes) |
|---|---|---|
| RSA-2048 (OAEP) | 270 | 256 |
| RSA-3072 (OAEP) | 398 | 384 |
| RSA-2048 (PSS) | 270 | 256 |
| RSA-3072 (PSS) | 398 | 384 |
| ECDSA P-256 | 65 | about 71 (varies slightly) |

Ciphertexts and signatures made by classical.py are also accepted by the benchmark's code, and the other way round, which confirms the padding and hash settings are the same. Timed back to back on the same RSA-3072 key, classical.py was within 2% of the benchmark's own code, so swapping it in should not change the timing results.

## Known limitations

classical.py covers AES-GCM, RSA and ECDSA only. The benchmark's other classical algorithms, ECDH with X25519 or P-256 and Ed25519 signatures, are not implemented here, so those entries would keep using the benchmark's own code. The benchmark also has no slot for symmetric ciphers, so the AES functions are not benchmarked.

Keys only exist in memory. There is no way to save a private key to a file or load one back, and there are no certificates, so nothing proves that a public key really belongs to Bob. `rsa_encap` does not prove who sent the key either; a real protocol would also authenticate the sender, for example with a signature. Sending a key with RSA also has no forward secrecy: anyone who records a locked key today can unlock it later if the private key leaks, or once a quantum computer can break RSA. This "harvest now, decrypt later" risk is why key exchange is usually the first thing to migrate. Because AES-GCM uses random 12-byte nonces, one key should not lock more than about 4 billion (2^32) messages.

The scanner only finds RSA where the key is made, in `rsa_keygen`. It matches names, so the calls that use an RSA key in `rsa_encap`, `rsa_decap`, `rsa_sign` and `rsa_verify` are not reported as RSA, and code that loaded an RSA key from a file instead of generating one would not be flagged at all.
