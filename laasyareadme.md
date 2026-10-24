# PQC-Ready: Classical vs Post-Quantum Benchmarks

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module measures how post-quantum algorithms compare to the classical algorithms they are meant to replace. It times key generation, key exchange and signing for each algorithm, measures the size of keys, ciphertexts and signatures, and saves the results as CSV and JSON for the final report and slides.


## Why this exists

Migrating to post-quantum cryptography is not free. ML-KEM and ML-DSA have much larger keys and signatures than RSA or elliptic curves, and the cost in speed is not obvious without measuring it. This benchmark puts numbers on those tradeoffs so the project can say concretely what a migration costs.

## How to run

The only required dependency is the `cryptography` package, version 50 or newer, which includes ML-KEM and ML-DSA through OpenSSL. It was developed and tested on Python 3.14 on Windows.

```
pip install cryptography
```

If `liboqs-python` and the liboqs C library are also installed, the ML-KEM and ML-DSA entries use the demo app's `PQC_service` code instead. liboqs has to be built from source, which needs CMake and a C compiler; without it the benchmark falls back to the `cryptography` versions. The program prints which one it used.

From the project root:

```
python benchmark.py
python benchmark.py --only ML-DSA
python benchmark.py --iterations 100
python benchmark.py --help
```

The first runs every algorithm with 10 timed runs per operation, the second runs only the algorithms whose name contains `ML-DSA`, and the third does a longer, more stable run. Other flags are `--warmup` (untimed runs before timing, default 5), `--message-size` (bytes in the signed message, default 1024) and `--out` (output folder, default `benchmarks/results`).

The program prints a timing table and a size table, then writes three files to the output folder: `timings.csv`, `sizes.csv`, and `results.json`, which also records the machine, the Python, cryptography and OpenSSL versions, and whether ML-KEM and ML-DSA came from liboqs or cryptography. The results folder is in `.gitignore` so test runs are not committed.

## Project layout

```
benchmark.py               command-line entry point
benchmarks/
    schemes.py             the KEMScheme and SigScheme shapes every algorithm fills in
    algorithms.py          the algorithms being compared
    runner.py              timing, correctness checks and size measurement
```

## Algorithms compared

| Key exchange | Signatures |
|---|---|
| RSA-2048, RSA-3072 (OAEP) | RSA-2048, RSA-3072 (PSS) |
| ECDH X25519, ECDH P-256 | ECDSA P-256, Ed25519 |
| ML-KEM-768, ML-KEM-1024 | ML-DSA-44, ML-DSA-65, ML-DSA-87 |

ML-KEM-512 is not included because the `cryptography` library does not provide it.

## How it works

Every algorithm is described the same way so the timing code can treat them all alike. A key exchange algorithm is a `KEMScheme` with `keygen`, `encaps` and `decaps`, and a signature algorithm is a `SigScheme` with `keygen`, `sign` and `verify`.

Classical key exchange is not naturally a KEM, so it is framed as one to keep the comparison fair. For RSA, encapsulating means encrypting a fresh random 32-byte secret with OAEP, and decapsulating means decrypting it. For ECDH, encapsulating means generating a throwaway key pair and combining it with the receiver's public key, and the throwaway public key is treated as the ciphertext. Every algorithm therefore does the same job: getting a shared secret to the other side.

Before timing anything, the runner checks that each algorithm actually works. For key exchange both sides must end up with the same secret, and for signatures a real signature must verify and a tampered message must fail. If a check fails the program stops rather than report timings for something broken.

Each operation is run a few times untimed as warm-up, then timed individually with `time.perf_counter_ns`. The results report mean, median, standard deviation, min and max in microseconds. The median is the best number to quote, since it is not pulled up by the occasional slow run caused by background activity on the machine.

Public keys are measured in their standard compact form: raw bytes for X25519, Ed25519, ML-KEM and ML-DSA, an uncompressed point for P-256, and PKCS#1 DER for RSA.

## Results so far

The sizes below are fixed by each algorithm and match the FIPS 203 and FIPS 204 standards for ML-KEM and ML-DSA.

| Algorithm | Public key (bytes) | Ciphertext or signature (bytes) |
|---|---|---|
| ECDH X25519 | 32 | 32 |
| RSA-2048 (OAEP) | 270 | 256 |
| ML-KEM-768 | 1184 | 1088 |
| ML-KEM-1024 | 1568 | 1568 |
| Ed25519 | 32 | 64 |
| ECDSA P-256 | 65 | 71 (varies slightly) |
| RSA-2048 (PSS) | 270 | 256 |
| ML-DSA-44 | 1312 | 2420 |
| ML-DSA-65 | 1952 | 3309 |
| ML-DSA-87 | 2592 | 4627 |

Size is the clearest cost of moving to post-quantum algorithms. An ML-DSA-65 signature is about 50 times larger than an Ed25519 signature, and an ML-KEM-768 public key is about 37 times larger than an X25519 key.

A quick 10-run test suggests speed is not the problem. ML-KEM and ML-DSA run in the same range as elliptic curve algorithms, and both are far faster than RSA key generation, which took tens of milliseconds for RSA-2048 and over 100 ms for RSA-3072. Final timing numbers will come from a full run with at least 100 iterations and will be added here.

## Known limitations

Timings depend on the machine, so they should only be compared within the same run, not across different computers. Python adds some overhead to every call, which matters more for the fastest operations. The RSA and ECDSA entries run the demo app's `classical.py`, and ML-KEM and ML-DSA run its `PQC_service` when liboqs is installed, but ECDH and Ed25519 still use the benchmark's own code. liboqs and OpenSSL implement ML-KEM and ML-DSA differently, and in a short test liboqs was several times faster, so results should say which backend was used and only be compared within the same backend. Symmetric algorithms such as AES are not benchmarked yet.
