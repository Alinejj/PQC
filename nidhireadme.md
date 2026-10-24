# PQC-Ready: Post-Quantum Cryptography

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module implements the post-quantum crypto schemes ML-KEM and ML-DSA via the `liboqs` library. ML-KEM establishes a shared secret between two communicating parties over an insecure network through the use of a key encapsulation mechanism (KEM). ML-DSA is a digital signature scheme, and a post-quantum alternative for classical schemes based on RSA and ECC.


## Why this exists

Post-quantum crypto algorithms (ML-KEM and ML-DSA) replace the mathematical foundations used in classic cryptography, such as RSA and ECC, with heavy module-lattice math and large data structures. This makes them difficult to implement at from scratch, and error prone due to their multiple layers. This module utilizes the `liboqs` library to implement ML-KEM and ML-DSA, enabling the demo application to use these schemes.

## How to run

The only dependency is the `liboqs` library. This version was written in Python 3.13 with `liboqs` 0.16.0.1

```
pip install liboqs-python
```

From the project root, run:

```
python PQC_service/pqc_demo.py
```

...to test that the schemes are working as intended.

NOTE: this is an internal module meant to be leveraged by the demo application.

## Project layout

```
PQC_service                         The service module imported by the demo application
    mldsa.py                        Implementation of ML-KEM scheme
        generate_dsa_keypair        Generates a keypair for the specified signature algorithm
        sign_message                Signs a message with the specified signature algorithm and secret key
        verify_signature            Verifies signature with the specified signature algorithm and public key
    mlkem.py                        Implementation of ML-DSA scheme
        generate_kem_keypair        Generate a keypair for the specified KEM algorithm
        encapsulate                 Returns ciphertext and shared secret
        decapsulate                 Returns shared secret
    pqc_demo.py                     Testing script to ensure the schemes are working as intended
```

## How it works

The functions found in the respective files for ML-KEM and ML-DSA can be imported and used by the demo app to perform the expected operations for each of the schemes: encapsulation and decapsulation for ML-KEM, signing and signature verification for ML-DSA, and keypair generation for both.

## Known limitations

ML-KEM and ML-DSA both have larger key and signature sizes than their classical counterparts, which can increase storage, bandwidth, and impact processing efficiency. Due to the complexity of their implementation, they are typically more difficult to protect against side-channel attacks, such as timing and power analysis attacks. The lattice-based math required to design these schemes is currently an active field of research, and confidence in them may be impacted by future findings.