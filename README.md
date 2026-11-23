# PQC-Ready: Source Code Scanner Core

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This project contains a detection engine + a demo application with two main parts (classical and post-quantum algorithm based testing) as well as a comparison of classical and post-quantum algorithms and implemented post-quantum crypto schemes. There is also an independent test on accuracy with blind test files. 

The Detection Engine: It reads Python source files and nginx and OpenSSL configuration files, finds cryptography that is either broken by quantum computers or already weak, and reports each finding with a recommended replacement. The report generator and demo app in the rest of the project are built on top of the output described here.

Classical: The classical half implements AES-GCM, RSA and ECDSA with the `cryptography` package, and it serves three purposes in the project: it provides the classical security functions for the demo (sending an encrypted message and signing data), it is the classical side that the benchmark compares ML-KEM and ML-DSA against, and it gives the scanner real, working classical cryptography to find. The post-quantum half implements ML-KEM-768 (post-quantum key encapsulation and decapsulation) and ML-DSA-65 (post-quantum digital signature). 

Post-Quantum Crypto Scheme Implementation: Implements the post-quantum crypto schemes ML-KEM and ML-DSA via the `liboqs` library. ML-KEM establishes a shared secret between two communicating parties over an insecure network through the use of a key encapsulation mechanism (KEM). ML-DSA is a digital signature scheme, and a post-quantum alternative for classical schemes based on RSA and ECC.

Demo: Both can be accessed through an interactive command-line application; there is also performance benchmarking to compare the two.

Comparison/Benchmarking: Measures how post-quantum algorithms compare to the classical algorithms they are meant to replace. It times key generation, key exchange and signing for each algorithm, measures the size of keys, ciphertexts and signatures, and saves the results as CSV and JSON for the final report and slides.

Independent testing: The blind test files provide an independent measurement of the scanner's accuracy on code it was not developed against. 

## Why this exists

A 2026 empirical study of open-source cryptographic discovery tools (Olewinski, Sandler and Ebinger, ARES 2026 Workshops) found that none of the tools tested caught more than 13 of 30 known crypto assets in a controlled test, and that symmetric ciphers, hash functions and key-exchange groups were missed by all of them. This scanner targets those gaps on purpose. The rules cover symmetric ciphers (AES modes, 3DES, Blowfish, RC4, ChaCha20, Fernet), hash functions (MD5, SHA-1, SHA-2, SHA-3, BLAKE2), key-exchange groups including hybrid post-quantum ones like `X25519MLKEM768`, post-quantum signatures and liboqs calls, and legacy TLS protocol constants.

We also compared classical and post-quantum algorithms to show weaknesses in the classical algorithms. RSA and elliptic-curve algorithms (classical algorithms) such as ECDSA are the public-key cryptography that Shor's algorithm breaks, so they are what a post-quantum migration replaces: ML-KEM takes over RSA's job of delivering keys, and ML-DSA takes over signing. For the comparison to be fair, the classical side has to be built the way a careful developer would build it today, with modern padding, authenticated encryption and fresh random values. Then any difference the project measures comes from the algorithms themselves rather than from implementation mistakes, and the scanner's findings show that even well-built classical cryptography is quantum-vulnerable.
AES is also included because both sides need it. A key exchange, classical or post-quantum, only delivers a shared secret; AES is what actually encrypts the message with that secret. AES is not replaced in the migration, since 256-bit AES keys are expected to stay secure against quantum computers.

Additionally, migrating to post-quantum cryptography is not free. ML-KEM and ML-DSA have much larger keys and signatures than RSA or elliptic curves, and the cost in speed is not obvious without measuring it. This benchmark puts numbers on those tradeoffs so the project can say concretely what a migration costs.

Lastly, we need blind files because the base ground truth test files' results show that detection gaps were found and fixed but they do not measure how well the scanner performs on unfamiliar code. These test files were written without knowledge of the 'rules/python_rules.json' file. Each test has an expected result 
recorded in the ground truth table answer key, and the scanner output is scored against it as a match, miss, mislabel, or false positive.

## How to run

**Prerequisites**:
```
pip install cryptography
pip install matplotlib
pip install liboqs-python
```

`cryptography` is needed for the demo app and the benchmark. `matplotlib` is only needed to draw benchmark charts. `liboqs-python` is only needed for the demo app and `PQC_service`. It builds the liboqs C library from source the first time it is imported, which needs git, CMake and a C compiler (on Windows, Build Tools for Visual Studio with the "Desktop development with C++" workload). Without it, `demo_app.py` stops at startup. The scanner (`main.py`), `evaluate.py` and the benchmark do not need it, because the benchmark falls back to the `cryptography` library.

**Detection Engine**
Nothing beyond the Python standard library is needed. It was developed and tested on Python 3.13 on Windows. The final benchmark run used Python 3.14.

From the project root:

```
python main.py tests/samples/ground_truth_demo.py
python main.py tests/samples
python main.py tests/samples/gap_test.py --json
python evaluate.py
python main.py --help
```

The first command scans one file. The second scans every Python and config file in a folder, skipping `.git`, virtual environments and `__pycache__`. The third prints the findings as a JSON list instead of text. The fourth, `evaluate.py`, scores the scanner against the answer key in `tests/expected.json` and prints matches, misses, mislabels and false positives per file. Text output is one line per finding, followed by a count:

```
tests\samples\ast_demo.py:7  [VULNERABLE] RSA -> ML-KEM (encryption) / ML-DSA (signatures), hybrid with classical during transition
```

A path that does not exist prints an error and exits with code 2, so a mistyped filename is never mistaken for a clean scan. By default the rule files are found relative to `main.py`, so the command works from any folder. The `--rules` flag points to a different rules file, which is then applied to Python files only. To save JSON output from Windows PowerShell, use `python main.py <target> --json | Out-File -Encoding utf8 findings.json`. Other Python code can skip the command line and call `scan_path(target, rules, config_rules)` from `scanner/walker.py` directly, which returns the `Finding` objects. The third argument is optional, so existing two-argument calls behave as before.

**Classical**
The classical implementation in `classical.py` provides AES-GCM encryption, RSA key encapsulation and signatures, and ECDSA signatures. These implementations are used by the demo application and the classical side of the benchmark.

**Post-Quantum Algorithm Implementations**
From the project root, run:
```
python PQC_service/pqc_demo.py
```

**Demo App**
*Main file:* `demo_app.py`
The application provides a numbered command-line menu containing the following options:

| Option | Feature                  | Description                                                         |
| ------ | ------------------------ | ------------------------------------------------------------------- |
| 1      | RSA Key Exchange         | Demonstrates RSA-based key encapsulation and recovery               |
| 2      | RSA Digital Signature    | Generates and verifies an RSA digital signature                     |
| 3      | ECDSA Digital Signature  | Generates and verifies an elliptic-curve digital signature          |
| 4      | AES-GCM Encryption       | Encrypts and decrypts data using authenticated symmetric encryption |
| 5      | ML-KEM-768               | Demonstrates post-quantum key encapsulation and decapsulation       |
| 6      | ML-DSA-65                | Generates and verifies a post-quantum digital signature             |
| 7      | Performance Benchmarking | Launches the classical and post-quantum benchmarking tool           |
| 8      | Exit                     | Exits the application                                               |

The application integrates existing cryptographic implementations into a single interactive interface.

**Classical vs. Post-Quantum Benchmarking**
The only required dependency is the `cryptography` package, version 50 or newer, which includes ML-KEM and ML-DSA through OpenSSL. It was developed and tested on Python 3.14 on Windows.

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

To draw charts from a results folder:
```
python benchmark.py --iterations 100 --out benchmarks/my_run
python benchmarks/plot.py benchmarks/my_run
```

This writes `timings_kem.png`, `timings_sig.png`, `sizes_kem.png` and `sizes_sig.png` into the same folder. Timings are drawn as the median on a log scale, because they range from about 15 µs to over 300 ms. Do not use `benchmarks/final_results` as the output folder, since it holds the final run reported below and a new run would overwrite it.

**Independent Testing**
The answer key is the `Ground-Truth Table Expanded.xlsx` workbook, with the expected findings represented by test ID, file, line, expected algorithm, category, status and replacement. The PDF view is [Ground-Truth-Table.pdf](./Ground-Truth-Table.pdf). The findings used to score the scanner are also recorded in `tests/expected.json`.

From the project root:
```
python main.py tests/samples/blind_decoys.py
python main.py tests/samples/blind_structure.py
python main.py tests/samples/blind_algorithms.py
python evaluate.py
```

**Unit tests**
From the project root:
```
python -m unittest tests/test_report_generator.py tests/test_demo_app.py
```

`test_report_generator.py` (3 tests) checks the security report output. `test_demo_app.py` (7 tests) checks the demo app, and it needs liboqs because the demo app imports `PQC_service`.

## Project layout

**Detection Engine**:
```
main.py                    command-line entry point
evaluate.py                scores scanner findings against tests/expected.json
report_generator.py        prints a readable security report from Finding objects
scanner/
    finding.py             the Finding dataclass (shared output format)
    rules.py               loads and validates a rules JSON
    scan_python.py         line-by-line regex pass
    scan_ast.py            syntax-tree pass using Python's ast module
    walker.py              chooses rules by file type, runs the passes, walks folders
rules/
    python_rules.json      Python detection rules (31 rules)
    nginx_rules.json       nginx configuration rules
    openssl_rules.json     OpenSSL configuration rules
tests/
    expected.json          answer key for the scored sample files
    test_report_generator.py
                           unit tests for report generation
    test_demo_app.py       unit tests for the demo application
    samples/
        ast_demo.py        basic AST detection sample
        ast_headers.py     crypto in decorators, defaults and block headers
        blind_decoys.py    independently supplied non-crypto decoys
        blind_structure.py independently supplied code with varied structures
        blind_algorithms.py
                           independently supplied algorithm coverage sample
        gap_test.py        algorithm and syntax gaps
        ground_truth_demo.py
                           16 known cryptographic assets
        new_rules.py       post-quantum and RSA-padding rules
        nginx_demo.conf    nginx configuration sample
        openssl_demo.cnf   OpenSSL configuration sample
        crypto_demo.py     additional cryptography sample
```

**Classical**
```
classical.py               RSA, ECDSA and AES-GCM implementations
```

**Post-Quantum Algorithm Implementations**
```
PQC_service                service module imported by the demo application
    mldsa.py               implementation of the ML-DSA scheme
        generate_dsa_keypair        Generates a keypair for the specified signature algorithm
        sign_message                Signs a message with the specified signature algorithm and secret key
        verify_signature            Verifies signature with the specified signature algorithm and public key
    mlkem.py               implementation of the ML-KEM scheme
        generate_kem_keypair        Generate a keypair for the specified KEM algorithm
        encapsulate                 Returns ciphertext and shared secret
        decapsulate                 Returns shared secret
    pqc_demo.py            standalone test script for ML-KEM and ML-DSA
```

**Demo App**
```
demo_app.py                interactive command-line menu for classical and PQC demos
```

**Classical vs. Post-Quantum Benchmarking**
```
benchmark.py               command-line entry point
benchmarks/
    schemes.py             the KEMScheme and SigScheme shapes every algorithm fills in
    algorithms.py          the algorithms being compared
    runner.py              timing, correctness checks and size measurement
    plot.py                draws the charts from timings.csv and sizes.csv
    final_results/         the 100-iteration run and charts used in the final report
```

**Independent Testing**
```
Ground-Truth Table Expanded.xlsx
                           expanded ground-truth answer key
Ground-Truth-Table.pdf      PDF version of the expanded ground-truth table
tests/
    expected.json              answer key for the evaluated sample files
    samples/
        blind_structure.py     independent code-structure coverage test
        blind_decoys.py        independent false-positive/decoy test
        blind_algorithms.py    independent algorithm-coverage test
```


## Results so far

**Detection Engine**
Detection is measured by `evaluate.py`, which compares the scanner's output with a hand-written answer key (`tests/expected.json`) and sorts every result into a match, a miss (expected but not found), a mislabel (found the wrong algorithm on a line) or a false positive (found where nothing was expected). The earlier sample files were written by the project itself, not by an outside party, so those numbers show that detection gaps were found and fixed, not how well the scanner generalizes. They are not comparable to the paper's 13 of 30.

```
evaluate.py:

TOTAL
  expected 83: match 83, miss 0, mislabel 0, false positive 0
```

On `ground_truth_demo.py`, a file of 16 known crypto assets modeled on the test file in the paper, the first version of the rules found 10 of 16 and mislabeled 3DES as AES-CBC on one line. After adding rules for AES-GCM, SHA-256, SHA-512, P-256 and the bare `X25519` group, and tightening the CBC rule to require AES, the scanner finds all 16. On `ast_demo.py`, the regex pass alone reported one finding, a false positive from a comment, and missed all four real ones. The AST pass found the four and ignored the comment. On `gap_test.py`, 11 assets in forms the first rules did not cover, the scanner found 2 of 11 before the rules were extended and 11 of 11 after. These two files were written after the rules existed, so they target known gaps rather than testing blind. `new_rules.py` (post-quantum signatures, liboqs, RSA padding) and `ast_headers.py` (crypto in decorators, default arguments and block headers) are in the same category.

Three files were written independently by a teammate who had not seen the rules. `blind_structure.py` (7 assets in different code structures) scored 7 of 7. `blind_decoys.py` contains 9 lines that look like crypto but are not (a trailing comment, strings inside `print`, and methods or variables that merely share a name with a crypto function), so the right answer is zero findings. The first scoring run reported 9 false positives on it, because the regex pass could not tell code from text and the AST pass did not skip string messages or locally defined names. The fixes described above bring it to zero. Since those fixes were designed after seeing this result, the decoy score shows the problem was understood and fixed, but it is not a blind measurement. A fresh set of decoys would be needed to know how well the fix generalizes. The third file, `blind_algorithms.py`, covers algorithms the rules were not built around: HMAC, Diffie-Hellman, DES, RC4 and three password hashers. It lists 9 expected findings. The first scan found 5 (AES-ECB, SHA-256, Diffie-Hellman, DES and RC4) and missed 4 (HMAC, bcrypt, Argon2 and scrypt), because there were no rules for them. It also reported RC4 on the line that imports `ARC4`, which counted as a false positive. We then added four rules, made the AST pass follow variables created from imported classes (needed for the Argon2 call, where the name appears only on the line that creates the object), and stopped matching on import statements. The file now scores 9 of 9 with no false positives and is part of the answer key. Because those changes were made after seeing the first result, the final score is not a blind measurement, and the first-run result of 5 of 9 is the honest figure for how the rules generalize.

Config files are scored on two samples (`nginx_demo.conf` and `openssl_demo.cnf`, 21 expected findings, including traps such as a commented-out setting). The first run found 18 of 21. The three misses were gaps in the rule files, not in the scanner: no nginx rule for the ML-KEM hybrid group, no OpenSSL rule for SHA-1 in cipher names such as `AES128-CBC-SHA`, and a TLS 1.3 rule that did not match `TLS_AES_256_GCM_SHA384`. The rules were extended after these results, and the scanner now finds all 21 with no false positives. Because the rules were written after seeing the misses, this shows the gaps were fixed, not how the rules do on new configuration files.

Overall, `evaluate.py` currently reports 83 expected findings, 83 matched, no missed findings, no mislabels and no false positives.

**Classical**
`classical.py` is also a sample the scanner reads. `python main.py classical.py` reports 15 findings: 6 vulnerable (RSA key exchange, RSA padding and ECDSA) and 9 safe (AES-GCM and SHA-256).

**Post-Quantum Algorithm Implementations**
`python PQC_service/pqc_demo.py` runs one ML-KEM key exchange and one ML-DSA signature. It prints `Shared secrets match.` when both sides derive the same secret and `Signature is valid.` when the signature verifies. The key, ciphertext and signature sizes for each parameter set are in the benchmark table below.

**Demo App**
Ten automated tests cover the demo app (7 tests in `tests/test_demo_app.py`) and the report generator (3 tests in `tests/test_report_generator.py`). On `ground_truth_demo.py`, the report generator summarizes 16 findings: 7 vulnerable, 3 weak, 1 transitional and 5 safe.

**Classical vs. Post-Quantum Benchmarking**
The final run used 100 timed runs per operation. It ran on Windows 11 with Python 3.14.6, `cryptography` 50.0.2 (OpenSSL 4.0.3), and the `cryptography` backend for ML-KEM and ML-DSA. The raw data and charts are in `benchmarks/final_results`. All timings below are medians in microseconds.

Key exchange:

| Scheme | Keygen | Encaps | Decaps | Public key (bytes) | Ciphertext (bytes) |
|---|---|---|---|---|---|
| RSA-2048 (OAEP) | 57,466 | 21.8 | 797.7 | 270 | 256 |
| RSA-3072 (OAEP) | 230,252 | 42.3 | 1,930.7 | 398 | 384 |
| ECDH X25519 | 25.7 | 56.9 | 31.7 | 32 | 32 |
| ECDH P-256 | 15.4 | 68.1 | 100.5 | 65 | 65 |
| ML-KEM-768 | 228.2 | 51.5 | 76.5 | 1,184 | 1,088 |
| ML-KEM-1024 | 314.3 | 52.5 | 101.9 | 1,568 | 1,568 |

Signatures:

| Scheme | Keygen | Sign | Verify | Public key (bytes) | Signature (bytes) |
|---|---|---|---|---|---|
| RSA-2048 (PSS) | 63,459 | 1,496.3 | 55.7 | 270 | 256 |
| RSA-3072 (PSS) | 324,417 | 5,023.9 | 111.8 | 398 | 384 |
| ECDSA P-256 | 30.9 | 54.2 | 130.8 | 65 | 70 |
| Ed25519 | 53.8 | 48.8 | 128.8 | 32 | 64 |
| ML-DSA-44 | 174.8 | 718.4 | 159.0 | 1,312 | 2,420 |
| ML-DSA-65 | 306.9 | 1,009.6 | 263.0 | 1,952 | 3,309 |
| ML-DSA-87 | 426.4 | 1,342.2 | 454.9 | 2,592 | 4,627 |

ML-KEM-768 key generation (228 µs) is about 250 times faster than RSA-2048 (57,466 µs) and close to the elliptic-curve schemes. The cost is in size: an ML-KEM-768 public key is 1,184 bytes against 32 for X25519, about 37 times larger. ML-DSA-65 signs in about 1.0 ms, roughly 21 times slower than Ed25519 (48.8 µs) but faster than RSA-2048 (1.5 ms), and its signature is 3,309 bytes against 64 for Ed25519.

**Independent Testing**
| File | Expected | First run | After rule and scanner changes |
|---|---|---|---|
| blind_decoys.py | 0 findings | 9 false positives | 0 false positives |
| blind_structure.py | 7 | 7 matched, 0 false positives | 7 matched, 0 false positives |
| blind_algorithms.py | 9 | 5 matched, 4 missed (HMAC, bcrypt, Argon2, scrypt), 1 false positive (RC4 reported on an import line) | 9 matched, 0 false positives |

The first run on the decoy file exposed false positives from trailing comments, strings inside `print` calls, and methods or variables named after algorithms. The first run on `blind_algorithms.py` exposed missing rules for HMAC and the three password hashers, and a case where the Argon2 call names the algorithm only where the hasher object is created. The fixes were new rules, an AST pass that tracks variables created from imported classes, ignoring strings in `print` and logging calls, and no longer matching import statements.


## Known limitations

**Detection Engine**
A statement that spans several lines is reported at the line where it starts. Detection is by name, so a rule cannot tell the key size and cannot tell whether a variable holding an algorithm name is actually used. Algorithm names passed in as variables or built as strings at runtime are not detected. Blanking string arguments to `print` and logging calls means crypto that is only named in an output message is not reported, which is intended, but a real use hidden inside such a call would be missed. A name that a file both imports and reassigns is treated as the library. Config files only get the regex pass, and the `.conf` and `.cnf` extension convention can misclassify an unrelated file with those extensions. A file that cannot be parsed falls back to the regex pass, which does not understand comments at the end of a code line.

**Classical**
Keys exist only in memory. There is no saving or loading of keys to files and no password protection, which a real application would need. Messages must be bytes, so text needs `.encode()` first. Nothing stops a caller from using the same RSA key pair for both encryption and signing, though separate pairs are the recommended practice. Random 12-byte nonces are safe at this project's scale; NIST guidance caps random nonces at about four billion messages per key. AES is not part of the benchmark, since it is identical on the classical and post-quantum sides.

**Post-Quantum Algorithm Implementations**
ML-KEM and ML-DSA both have larger key and signature sizes than their classical counterparts, which can increase storage, bandwidth, and impact processing efficiency. Due to the complexity of their implementation, they are typically more difficult to protect against side-channel attacks, such as timing and power analysis attacks. The lattice-based math required to design these schemes is currently an active field of research, and confidence in them may be impacted by future findings.

**Demo App**
- The demo is intended for educational use rather than production cryptographic key management.
- The demo app requires liboqs (through `liboqs-python`) because `PQC_service` imports it directly. liboqs builds from source on first use and needs CMake and a C compiler, so without it `demo_app.py` stops at startup. The benchmark does not have this requirement.
- Benchmark results vary by hardware and runtime conditions.
- The report generator relies on the scanner's detection accuracy and configured rules.
- Automated tests verify the individual demo operations but do not constitute a complete security audit.

**Classical vs. Post-Quantum Benchmarking**
Timings depend on the machine, so they should only be compared within the same run, not across different computers. Python adds some overhead to every call, which matters more for the fastest operations. The RSA and ECDSA entries run the demo app's `classical.py`, and ML-KEM and ML-DSA run its `PQC_service` when liboqs is installed, but ECDH and Ed25519 still use the benchmark's own code. liboqs and OpenSSL implement ML-KEM and ML-DSA differently, and in a short test inside a Linux container liboqs was several times faster, so results should say which backend was used and only be compared within the same backend. The final results above use the `cryptography` backend only. The results come from one laptop and one run, so the exact numbers will differ on other hardware, but the large gaps (RSA key generation, signature sizes) are far bigger than the run-to-run noise. Symmetric algorithms such as AES are not benchmarked, since Shor's algorithm does not break them and the project's comparison is about the public-key algorithms that need replacing.

**Independent Testing**
The three blind files were written by one teammate, so they are small and reflect one person's idea of unfamiliar code. The decoy and algorithm results were reached after fixes made in response to the first run, so only the first-run numbers (9 false positives on the decoys, 5 of 9 on `blind_algorithms.py`) measure how the scanner handles new code. The current rules have not been tested on a fresh set of blind files.