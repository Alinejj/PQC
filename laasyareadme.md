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

The program prints a timing table and a size table, then writes three files to the output folder: `timings.csv`, `sizes.csv`, and `results.json`, which also records the machine, the Python, cryptography and OpenSSL versions, and whether ML-KEM and ML-DSA came from liboqs or cryptography. The results folder is in `.gitignore` so test runs are not committed. The final 100-iteration run reported below is kept separately in `benchmarks/final_results`.

To draw charts from a results folder (this needs `pip install matplotlib`):

```
python benchmark.py --iterations 100 --out benchmarks/final_results
python benchmarks/plot.py benchmarks/final_results
```

This writes `timings_kem.png`, `timings_sig.png`, `sizes_kem.png` and `sizes_sig.png` into the same folder. Timings are drawn as the median on a log scale, because they range from about 15 µs to over 300 ms.

## Project layout

```
benchmark.py               command-line entry point
benchmarks/
    schemes.py             the KEMScheme and SigScheme shapes every algorithm fills in
    algorithms.py          the algorithms being compared
    runner.py              timing, correctness checks and size measurement
    plot.py                draws the charts from timings.csv and sizes.csv
    final_results/         the 100-iteration run and charts used in the final report
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

## Results

### Test setup

| Setting | Value |
|---|---|
| Timed runs per operation | 100 (after 5 untimed warm-up runs) |
| Signed message size | 1024 bytes |
| ML-KEM and ML-DSA backend | `cryptography` (OpenSSL), not liboqs |
| Library versions | cryptography 50.0.2, OpenSSL 4.0.3 |
| Python | 3.14.6 |
| Machine | Intel Core Ultra 9 386H, 31 GB RAM, Windows 11 |
| Date | 2026-11-21 |

All algorithms, classical and post-quantum, ran through the same `cryptography` library and OpenSSL build, so the comparison is between algorithms rather than between libraries. liboqs could not be built on this machine (it needs CMake and a C compiler), so the `PQC_service` code was not used for these numbers. The raw data is in `benchmarks/final_results`.

### Timing (microseconds, 100 runs each)

Key exchange:

| Algorithm | Operation | Median | Mean | Std. dev. |
|---|---|---|---|---|
| RSA-2048 (OAEP) | keygen | 57,466 | 67,573 | 44,576 |
| | encaps | 21.8 | 32.4 | 22.5 |
| | decaps | 797.7 | 797.5 | 146.0 |
| RSA-3072 (OAEP) | keygen | 230,252 | 264,429 | 175,579 |
| | encaps | 42.3 | 43.9 | 3.8 |
| | decaps | 1,930.7 | 2,160.2 | 554.7 |
| ECDH X25519 | keygen | 25.7 | 25.9 | 1.1 |
| | encaps | 56.9 | 57.4 | 1.9 |
| | decaps | 31.7 | 31.8 | 0.8 |
| ECDH P-256 | keygen | 15.4 | 15.8 | 2.1 |
| | encaps | 68.1 | 68.8 | 2.5 |
| | decaps | 100.5 | 102.4 | 88.4 |
| ML-KEM-768 | keygen | 228.2 | 245.6 | 158.1 |
| | encaps | 51.5 | 52.9 | 5.3 |
| | decaps | 76.5 | 161.1 | 645.8 |
| ML-KEM-1024 | keygen | 314.3 | 333.8 | 71.9 |
| | encaps | 52.5 | 70.2 | 103.0 |
| | decaps | 101.9 | 107.5 | 34.3 |

Signatures:

| Algorithm | Operation | Median | Mean | Std. dev. |
|---|---|---|---|---|
| RSA-2048 (PSS) | keygen | 63,459 | 74,314 | 47,654 |
| | sign | 1,496.3 | 1,600.0 | 493.6 |
| | verify | 55.7 | 59.4 | 8.1 |
| RSA-3072 (PSS) | keygen | 324,417 | 386,410 | 240,911 |
| | sign | 5,023.9 | 5,121.2 | 1,198.8 |
| | verify | 111.8 | 135.9 | 63.0 |
| ECDSA P-256 | keygen | 30.9 | 36.0 | 22.9 |
| | sign | 54.2 | 77.0 | 86.2 |
| | verify | 130.8 | 151.0 | 57.7 |
| Ed25519 | keygen | 53.8 | 56.2 | 32.8 |
| | sign | 48.8 | 49.3 | 16.1 |
| | verify | 128.8 | 136.2 | 42.9 |
| ML-DSA-44 | keygen | 174.8 | 180.0 | 65.4 |
| | sign | 718.4 | 908.3 | 620.5 |
| | verify | 159.0 | 169.1 | 36.1 |
| ML-DSA-65 | keygen | 306.9 | 299.5 | 69.6 |
| | sign | 1,009.6 | 1,305.5 | 927.6 |
| | verify | 263.0 | 259.9 | 53.6 |
| ML-DSA-87 | keygen | 426.4 | 429.6 | 67.8 |
| | sign | 1,342.2 | 1,744.7 | 1,237.2 |
| | verify | 454.9 | 496.7 | 274.8 |

![Key exchange timing](benchmarks/final_results/timings_kem.png)
![Signature timing](benchmarks/final_results/timings_sig.png)

### Sizes (bytes)

The sizes are fixed by each algorithm and match the FIPS 203 and FIPS 204 standards for ML-KEM and ML-DSA.

| Algorithm | Public key | Ciphertext or signature |
|---|---|---|
| RSA-2048 (OAEP) | 270 | 256 |
| RSA-3072 (OAEP) | 398 | 384 |
| ECDH X25519 | 32 | 32 |
| ECDH P-256 | 65 | 65 |
| ML-KEM-768 | 1,184 | 1,088 |
| ML-KEM-1024 | 1,568 | 1,568 |
| RSA-2048 (PSS) | 270 | 256 |
| RSA-3072 (PSS) | 398 | 384 |
| ECDSA P-256 | 65 | 70 (varies by a byte or two) |
| Ed25519 | 32 | 64 |
| ML-DSA-44 | 1,312 | 2,420 |
| ML-DSA-65 | 1,952 | 3,309 |
| ML-DSA-87 | 2,592 | 4,627 |

![Key exchange sizes](benchmarks/final_results/sizes_kem.png)
![Signature sizes](benchmarks/final_results/sizes_sig.png)

### What the results show

**Size is the main cost of moving to post-quantum algorithms.** An ML-KEM-768 public key is 37 times larger than an X25519 key (1,184 vs 32 bytes), and an ML-DSA-65 signature is about 52 times larger than an Ed25519 signature (3,309 vs 64 bytes). Even the smallest ML-DSA signature (2,420 bytes) is over nine times the size of an RSA-2048 signature. This matters most where data is sent often or space is tight, such as TLS handshakes and certificate chains.

**Speed is not a barrier, and against RSA it is an improvement.** ML-KEM-768 key generation took 228 µs, about 250 times faster than RSA-2048 (57 ms) and about 1,000 times faster than RSA-3072 (230 ms). ML-KEM-768 decapsulation (77 µs) was about 10 times faster than RSA-2048 decryption (798 µs). ML-DSA signing (0.7–1.3 ms across the three levels) was faster than RSA-2048 signing (1.5 ms) and 4 to 7 times faster than RSA-3072 signing (5.0 ms).

**Compared with elliptic curves, post-quantum algorithms are somewhat slower but in the same range.** ML-KEM-768 encapsulation (52 µs) was as fast as X25519 (57 µs), while its key generation was about 9 times slower (228 vs 26 µs). ML-DSA-44 verification (159 µs) was close to ECDSA and Ed25519 (about 130 µs), though ML-DSA-87 took about 3.5 times as long (455 µs), and ML-DSA signing was 13 to 25 times slower than ECDSA signing (54 µs).

**Some operations vary a lot from run to run, for known reasons.** RSA key generation has a standard deviation close to its mean, because it searches for random primes and some searches take much longer than others. ML-DSA signing also varies widely, because it uses rejection sampling: it retries with new randomness until the signature meets the required bounds, and the number of retries changes every time. A few other operations, such as ML-KEM-768 decapsulation, show a high mean but a low median, which means one or two runs were slowed down by background activity on the machine. This is why the median is the number quoted above.

**Higher security levels cost little extra time.** Going from ML-KEM-768 to ML-KEM-1024 changed encapsulation time by about 1 µs, and going from ML-DSA-44 to ML-DSA-87 roughly doubled signing time. Size grows more steeply than time across the levels.

## Known limitations

Timings depend on the machine, so they should only be compared within the same run, not across different computers. Python adds some overhead to every call, which matters more for the fastest operations. The RSA and ECDSA entries run the demo app's `classical.py`, and ML-KEM and ML-DSA run its `PQC_service` when liboqs is installed, but ECDH and Ed25519 still use the benchmark's own code. liboqs and OpenSSL implement ML-KEM and ML-DSA differently, and in a short test inside a Linux container liboqs was several times faster, so results should say which backend was used and only be compared within the same backend. The final results above use the `cryptography` backend only. The results come from one laptop and one run, so the exact numbers will differ on other hardware, but the large gaps (RSA key generation, signature sizes) are far bigger than the run-to-run noise. Symmetric algorithms such as AES are not benchmarked, since Shor's algorithm does not break them and the project's comparison is about the public-key algorithms that need replacing.
