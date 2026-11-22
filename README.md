# PQC-Ready: Source Code Scanner Core

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module is the detection engine of PQC-Ready. It reads Python source files and nginx and OpenSSL configuration files, finds cryptography that is either broken by quantum computers or already weak, and reports each finding with a recommended replacement. The report generator and demo app in the rest of the project are built on top of the output described here.

Owner: Aline (scanner architecture and source-code detection)

## Why this exists

A 2026 empirical study of open-source cryptographic discovery tools (Olewinski, Sandler and Ebinger, ARES 2026 Workshops) found that none of the tools tested caught more than 13 of 30 known crypto assets in a controlled test, and that symmetric ciphers, hash functions and key-exchange groups were missed by all of them. This scanner targets those gaps on purpose. The rules cover symmetric ciphers (AES modes, 3DES, Blowfish, RC4, ChaCha20, Fernet), hash functions (MD5, SHA-1, SHA-2, SHA-3, BLAKE2), key-exchange groups including hybrid post-quantum ones like `X25519MLKEM768`, post-quantum signatures and liboqs calls, and legacy TLS protocol constants.

## How to run

Nothing beyond the Python standard library is needed. It was developed and tested on Python 3.13 on Windows.

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

## Project layout

```
main.py                    command-line entry point
evaluate.py                scores the scanner against tests/expected.json
scanner/
    finding.py             the Finding dataclass (shared output format)
    rules.py               loads and validates a rules JSON
    scan_python.py         line-by-line regex pass
    scan_ast.py            syntax-tree pass using Python's ast module
    walker.py              chooses rules by file type, runs the passes, walks folders
rules/
    python_rules.json      Python detection rules (27 rules)
    nginx_rules.json       nginx configuration rules (written by a teammate)
    openssl_rules.json     OpenSSL configuration rules (written by a teammate)
tests/
    expected.json          answer key for the scored sample files
    samples/               Python and config files used to measure detection
```

## The Finding format

Every detection is a `Finding` with seven fields: `file`, `line`, `matched_text`, `algorithm`, `category`, `status` and `replacement`. Category is one of asymmetric, symmetric, hash, key_exchange or protocol. Status is one of vulnerable (broken by Shor's algorithm, like RSA, DSA, elliptic curves and Diffie-Hellman), weak (already discouraged or broken classically, like MD5, SHA-1, DES, Blowfish, RC4, ECB mode and legacy TLS), transitional (usable but should be migrated, like AES-CBC and Fernet) or safe (including post-quantum algorithms).

The main entry point for other modules is `scan_path` in `scanner/walker.py`, which returns a list of `Finding` objects. This format is shared with the rest of the team and has not changed. Any change to it needs to be announced.

One detail matters for anyone consuming the output. For findings from the AST pass, `matched_text` comes from the normalized, alias-resolved version of the statement, not the raw source. A source line `generate_private_key(...)` imported from `cryptography.hazmat.primitives.asymmetric.rsa` is reported with `matched_text` of `rsa.generate_private_key`, and `hashlib.new("md5")` is reported as `hashlib.new('md5'` because Python normalizes quote style. The `file` and `line` fields always point at the original source.

## Rules are data, not code

Detection rules live in the JSON files under `rules/`. Each rule has an id, a regex pattern, an algorithm name, a category, a status and a replacement. Anyone can add a rule by adding an entry to the JSON without touching any Python. `load_rules` checks every rule on load: a missing field, an invalid category or status, or a broken regex stops the program with an error that names the rule. Patterns are compiled once at load time rather than for every line scanned.

The status given to each algorithm is a judgment call based on general public guidance on quantum risk and deprecated algorithms. These classifications should be checked against a cited source, such as NIST guidance, before the final report.

## How detection works

The walker decides which rules apply from the file type. Python files use `python_rules.json`. Files ending in `.conf` use the nginx rules and files ending in `.cnf` use the OpenSSL rules. This extension convention is a single dictionary at the top of `walker.py` and is easy to change.

For a Python file, the AST pass does the work. It parses the file into a syntax tree with Python's `ast` module and builds a map of import aliases, so a short name like `r` is rewritten back to `Crypto.PublicKey.RSA` before matching. Each statement is converted back to a single normalized line with `ast.unparse`, and the rules run over that text. Since the tree never contains comments, comments are ignored, and since a statement is flattened to one line, a call spread over four lines is matched as one. For compound statements (`if`, `while`, `for`, `with`, `def`, `class`, `except`) only the header is matched, which covers conditions, loop iterables, decorators and default arguments. The statements inside the block are visited on their own.

Two filters keep the AST pass from reporting things that are not crypto use. A name the file defines itself and never imports (for example `hashlib = Tester()` followed by `hashlib.sha1()`) is not the library, so it is renamed internally and no longer matches. String arguments to `print` and to logging calls are blanked, since a message that mentions RSA does not use RSA. A string passed anywhere else, such as `set_groups("X25519:prime256v1")`, still counts.

The regex pass reads a file line by line and tests every rule against each line. It runs only as a fallback when a Python file cannot be parsed (for example, because of a syntax error), and for config files, which are not Python. It skips lines that are entirely a comment.

## Results so far

Detection is measured by `evaluate.py`, which compares the scanner's output with a hand-written answer key (`tests/expected.json`) and sorts every result into a match, a miss (expected but not found), a mislabel (found the wrong algorithm on a line) or a false positive (found where nothing was expected). The earlier sample files were written by the project itself, not by an outside party, so those numbers show that detection gaps were found and fixed, not how well the scanner generalizes. They are not comparable to the paper's 13 of 30.

On `ground_truth_demo.py`, a file of 16 known crypto assets modeled on the test file in the paper, the first version of the rules found 10 of 16 and mislabeled 3DES as AES-CBC on one line. After adding rules for AES-GCM, SHA-256, SHA-512, P-256 and the bare `X25519` group, and tightening the CBC rule to require AES, the scanner finds all 16. On `ast_demo.py`, the regex pass alone reported one finding, a false positive from a comment, and missed all four real ones. The AST pass found the four and ignored the comment. On `gap_test.py`, 11 assets in forms the first rules did not cover, the scanner found 2 of 11 before the rules were extended and 11 of 11 after. These two files were written after the rules existed, so they target known gaps rather than testing blind. `new_rules.py` (post-quantum signatures, liboqs, RSA padding) and `ast_headers.py` (crypto in decorators, default arguments and block headers) are in the same category.

Three files were written independently by a teammate who had not seen the rules. `blind_structure.py` (7 assets in different code structures) scored 7 of 7. `blind_decoys.py` contains 9 lines that look like crypto but are not (a trailing comment, strings inside `print`, and methods or variables that merely share a name with a crypto function), so the right answer is zero findings. The first scoring run reported 9 false positives on it, because the regex pass could not tell code from text and the AST pass did not skip string messages or locally defined names. The fixes described above bring it to zero. Since those fixes were designed after seeing this result, the decoy score shows the problem was understood and fixed, but it is not a blind measurement. A fresh set of decoys would be needed to know how well the fix generalizes. The third file, `blind_algorithms.py`, covers algorithms the rules were not built around and was added after the answer key was scored, so it is not in `tests/expected.json` and not in the totals below. It lists 9 expected findings. The scanner found 5 (AES-ECB, SHA-256, Diffie-Hellman, DES and RC4) and missed 4 (HMAC, bcrypt, Argon2 and scrypt), because there are no rules for them. It also reported RC4 on the line that imports `ARC4`, which a strict line-by-line score would count as a false positive. This is the first result on code written without knowledge of the rules, and it shows a rule-coverage gap rather than a parsing problem.

Config files are scored on two samples (`nginx_demo.conf` and `openssl_demo.cnf`, 21 expected findings, including traps such as a commented-out setting). The current nginx and OpenSSL rules cover those samples without false positives. ML-KEM/hybrid nginx curves, SHA-1 cipher names such as `AES128-CBC-SHA`, and TLS 1.3 suites using SHA-384 are all detected.

Overall, `evaluate.py` currently reports 74 expected findings, 74 matched, no missed findings, no mislabels and no false positives.

## Known limitations

A statement that spans several lines is reported at the line where it starts. Detection is by name, so a rule cannot tell the key size and cannot tell whether a variable holding an algorithm name is actually used. Algorithm names passed in as variables or built as strings at runtime are not detected. Blanking string arguments to `print` and logging calls means crypto that is only named in an output message is not reported, which is intended, but a real use hidden inside such a call would be missed. A name that a file both imports and reassigns is treated as the library. Config files only get the regex pass, and the `.conf` and `.cnf` extension convention can misclassify an unrelated file with those extensions. A file that cannot be parsed falls back to the regex pass, which does not understand comments at the end of a code line.

## Change log

October 18, 2026: Created the project skeleton, the `Finding` dataclass, the rules loader and the first 12 rules. Added the regex scanner, folder walker and command-line entry point. Added the ground-truth sample and expanded the rules to 16 after the first run missed 6 assets and mislabeled one. Added the AST pass, merged it with the regex pass and made the regex pass skip comment lines.

October 21, 2026: Added `gap_test.py`, which scored 2 of 11 on the existing rules. Extended the rules to 23: added DSA, SHA-3, BLAKE2, Fernet, ChaCha20, Blowfish and legacy TLS rules, made the MD5 and SHA-1 rules also match `hashlib.new("...")`, and replaced the AES-only ECB rule with a generic ECB rule. Re-ran all test files with no regressions. Added the `--json` output flag to `main.py`.

November 13, 2026: Added `evaluate.py` and the answer key `tests/expected.json`, which gave a baseline of 38 of 38 matched on the real files and 9 false positives on the decoy file. Added four rules (post-quantum signatures, liboqs calls, RSA OAEP and PSS padding, `AESGCM.generate_key`), bringing the Python rules to 27, and `new_rules.py` to test them.

November 14, 2026: Added file-type routing in the walker so `.conf` files use the nginx rules and `.cnf` files use the OpenSSL rules, without changing the `Finding` format or the two-argument `scan_path` call. A nonexistent path now raises an error instead of reporting zero findings. `main.py` finds the rules relative to its own location. Added `nginx_demo.conf` and `openssl_demo.cnf` to the scored samples, which exposed three gaps in the config rules.

November 15, 2026: Made the AST pass the primary pass, with regex as a fallback for files that do not parse. The AST pass now covers compound statement headers, ignores string arguments to `print` and logging calls, and ignores names a file defines itself and never imports. False positives on `blind_decoys.py` dropped from 9 to 0 with no regressions. Added `ast_headers.py` to test the header coverage. Updated this README.

November 22, 2026: Closed the remaining config-rule gaps by adding nginx ML-KEM/hybrid curve detection, OpenSSL SHA-1 cipher detection, and the OpenSSL TLS 1.3 SHA-384 suite pattern. `evaluate.py` now scores 74 of 74 findings with no mislabels or false positives.
November 22, 2026: Ran the scanner on `blind_algorithms.py` (5 of 9 expected findings, 4 misses for HMAC, bcrypt, Argon2 and scrypt, 1 extra RC4 on an import line) and recorded the result above. The file is not yet in `tests/expected.json`, so `evaluate.py` still reports 71 of 74.

# PQC-Ready: Demo Application and Security Report Generator

**Contributor:** Govind Rangappa  
**Course:** CS 4389 – Data and Applications Security  
**Project:** Post-Quantum Cryptography (PQC)

## 1. Overview

My contributions to PQC-Ready consist of two components:

1. **Cryptography Demo Application (**`demo_app.py`**)** – An interactive command-line application that demonstrates classical and post-quantum cryptographic algorithms and provides access to performance benchmarking.
2. **Security Report Generator (**`report_generator.py`**)** – A reporting module that converts findings from the cryptographic vulnerability scanner into a human-readable security report.

These components complement the project's source-code scanner by helping users understand cryptographic operations, compare classical and post-quantum approaches, and interpret detected security findings.

## 2. Requirements and Setup

The demo application was developed and tested using:

- Windows
- Python 3.12
- `cryptography` version 50.0.2

The scanner and report generator use Python's standard library, while the cryptography demo requires the additional dependency.

From the root of the project, install the dependencies:

```
python -m pip install -r requirements.txt
```

The project's `requirements.txt` specifies:

```
cryptography>=50.0.2,<51
```

To start the demo:

```
python demo_app.py
```

## 3. Cryptography Demo Application

**Main file:** `demo_app.py`

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

### 3.1 Classical Cryptography

The first four options demonstrate classical cryptographic algorithms.

**RSA Key Exchange**

Demonstrates the use of RSA to protect a randomly generated symmetric key. The receiving party uses the corresponding private key to recover the original key.

**RSA Digital Signature**

Demonstrates signing a message using an RSA private key and verifying the signature using the public key.

**ECDSA Digital Signature**

Demonstrates digital signature generation and verification using elliptic-curve cryptography.

**AES-GCM Encryption**

Demonstrates symmetric encryption and decryption using AES in Galois/Counter Mode (GCM). AES-GCM also provides authentication, allowing the recipient to detect unauthorized changes to encrypted data.

The classical cryptographic implementations are provided through Jenny's `classical.py` module.

### 3.2 Post-Quantum Cryptography

The next two options demonstrate standardized post-quantum cryptographic algorithms.

**ML-KEM-768**

ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism) is designed to establish a shared secret while resisting attacks from both classical and quantum computers.

The demonstration:

1. Generates a public/private key pair.
2. Encapsulates a shared secret using the public key.
3. Decapsulates the ciphertext using the private key.
4. Confirms that both shared secrets match.

**ML-DSA-65**

ML-DSA (Module-Lattice-Based Digital Signature Algorithm) is a post-quantum digital signature algorithm.

The demonstration:

1. Generates a public/private signing key pair.
2. Signs a sample message using the private key.
3. Verifies the signature using the public key.
4. Displays whether verification succeeded.

The ML-KEM-768 and ML-DSA-65 demonstrations use the scheme interfaces defined in `benchmarks/algorithms.py`. These interfaces use Nidhi's `PQC_service` implementation when liboqs is installed and fall back to the `cryptography` library otherwise.

## 4. Performance Benchmarking

**Files:** `benchmark.py` and `benchmarks/`

The demo application's seventh option launches the benchmarking component developed by Laasya.

The application runs:

```
python benchmark.py --iterations 10 --warmup 2
```

The benchmark measures operations across 13 classical and post-quantum cryptographic schemes, including:

- RSA-2048 and RSA-3072
- ECDH using X25519 and P-256
- ECDSA P-256
- Ed25519
- ML-KEM-768 and ML-KEM-1024
- ML-DSA-44, ML-DSA-65, and ML-DSA-87

The RSA schemes are evaluated in both key-encapsulation and signature contexts.

### Measurements

Depending on the algorithm, the benchmarking component records:

- Key generation time
- Encapsulation time
- Decapsulation time
- Signature generation time
- Signature verification time
- Public key size
- Ciphertext size
- Signature size

The benchmarking tool can also be executed independently:

```
python benchmark.py --iterations 10 --warmup 2
```

### Output Files

Benchmark results are generated in the `benchmarks/results/` directory.


| File           | Description                                        |
| -------------- | -------------------------------------------------- |
| `timings.csv`  | Timing statistics for cryptographic operations     |
| `sizes.csv`    | Cryptographic key, ciphertext, and signature sizes |
| `results.json` | Structured benchmark measurements and metadata     |


These files are generated during execution and are excluded from version control.

### Benchmarking Considerations

The measurements provide a practical comparison of cryptographic operations in the test environment.

Performance depends on the machine, software environment, and benchmark configuration. Additionally, RSA, elliptic-curve, and post-quantum algorithms do not always provide identical functionality or equivalent security levels, so results should be interpreted within their respective cryptographic categories.

## 5. Security Report Generator

**Main file:** `report_generator.py`

The security report generator converts scanner findings into a readable text report.

The scanner detects cryptographic usage in Python source code and classifies findings according to its configured security rules.

The report generator presents the findings in a format that is easier to review than raw structured output.

### 5.1 Report Contents

The generated report includes:

- Total number of findings
- Counts grouped by security classification
- Source file locations
- Line numbers
- Detected cryptographic algorithms
- Matched source-code information
- Recommended replacements or remediation guidance

The report generator supports the scanner's existing security classifications, including vulnerable, weak, transitional, and safe cryptographic usage.

### 5.2 Running the Scanner with a Report

From the repository root:

```
python main.py tests/samples/ground_truth_demo.py --report
```

This scans the provided sample Python file and displays a human-readable report.

To save the output to a text file:

```
python main.py tests/samples/ground_truth_demo.py --report > security_report.txt
```

The report can also be generated when scanning other supported Python files or directories.

### 5.3 JSON Output

The scanner's existing JSON output functionality is preserved.

To display JSON findings:

```
python main.py tests/samples/ground_truth_demo.py --json
```

This allows users to choose between machine-readable JSON output and human-readable reporting.

### 5.4 Implementation

The report generator provides the following function:

```
generate_report(findings)
```

This function accepts the scanner's findings and produces formatted report text.

The reporting functionality is integrated into `main.py` through the `--report` command-line argument.

The report generator does not perform cryptographic vulnerability detection itself. Detection is handled by the scanner, and the report generator formats the resulting findings.

## 6. Automated Testing

Automated tests were created for both components.

### 6.1 Demo Application Tests

**File:** `tests/test_demo_app.py`

Seven automated tests cover:

1. RSA key encapsulation and recovery
2. RSA digital signature verification
3. ECDSA digital signature verification
4. AES-GCM encryption and decryption
5. ML-KEM-768 shared-secret recovery
6. ML-DSA-65 digital signature verification
7. Benchmark subprocess invocation

To run these tests:

```
python -m unittest discover -s tests -p "test_demo_app.py" -v
```

**Local test result:** All 7 tests passed.

The benchmark integration test uses mocking to verify that the demo launches the benchmark with the expected command-line arguments.

### 6.2 Report Generator Tests

**File:** `tests/test_report_generator.py`

The report generator includes three automated tests covering:

- Empty findings
- Individual vulnerability findings
- Multiple findings with different security classifications

Run the tests using:

```
python -m unittest discover -s tests -p "test_report_generator.py" -v
```

**Local test result:** All 3 tests passed.

### 6.3 Running Both Test Files

To run the demo and report generator tests together:

```
python -m unittest discover -s tests -p "test_*.py" -v
```

The demo application and report generator tests passed during local development. Integration testing should be repeated after all teammates' changes are merged.

## 7. Files and Contributions

The following files were created or modified as part of my contributions.


| File                             | Contribution                                                   |
| -------------------------------- | -------------------------------------------------------------- |
| `demo_app.py`                    | Created the interactive cryptography demonstration application |
| `tests/test_demo_app.py`         | Created seven automated tests for the demo                     |
| `report_generator.py`            | Created the human-readable scanner report generator            |
| `tests/test_report_generator.py` | Created automated tests for reporting                          |
| `main.py`                        | Integrated the `--report` command-line option                  |
| `requirements.txt`               | Added the cryptography dependency specification                |
| `.gitignore`                     | Added exclusions for virtual environments and generated output |


### Integration with Other Contributors

The demo application integrates work developed by other team members:

- **Jenny:** Classical cryptography functionality in `classical.py`
- **Laasya:** Benchmarking implementation in `benchmark.py` and `benchmarks/`
- **Aline and the scanner team:** Cryptographic vulnerability detection and findings used by the report generator

My work focused on building the interactive demo interface, connecting these components, implementing human-readable reporting, and testing my additions.

## 8. Limitations

- The demo is intended for educational use rather than production cryptographic key management.
- The demo requires a compatible version of the `cryptography` library with ML-KEM and ML-DSA support.
- Benchmark results vary by hardware and runtime conditions.
- The report generator relies on the scanner's detection accuracy and configured rules.
- Automated tests verify the individual demo operations but do not constitute a complete security audit.

## 9. Conclusion

The cryptography demo application and report generator improve the usability of PQC-Ready in two ways.

The demo application provides a single interface for demonstrating classical and post-quantum cryptographic operations and launching performance comparisons.

The report generator converts cryptographic vulnerability findings into readable security reports containing classifications, source locations, and recommended replacements.

Together, these components support the project's goal of helping users identify cryptographic risks, understand post-quantum alternatives, and explore the transition toward quantum-resistant cryptography.

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
| RSA-OAEP | `rsa_keygen`, `rsa_encap`, `rsa_decap` | Delivers a fresh AES key to the receiver | 2048 or 3072 bits (default 3072), public exponent 65537, OAEP with SHA-256 |
| RSA-PSS | `rsa_keygen`, `rsa_sign`, `rsa_verify` | Signs messages | PSS with SHA-256, salt length equal to the hash length |
| ECDSA | `ecdsa_keygen`, `ecdsa_sign`, `ecdsa_verify` | Signs messages | P-256 curve, SHA-256 |

`rsa_public_bytes` and `ecdsa_public_bytes` return a public key as bytes so its size can be measured: PKCS#1 DER for RSA and an uncompressed point for P-256, the same formats the benchmark uses.

## Function shapes

The RSA and ECDSA functions follow the `KEMScheme` and `SigScheme` shapes in `benchmarks/schemes.py`, so the benchmark can call them directly. The AES functions are not part of the benchmark. Every function in the module, by its exact name:

```
# RSA
rsa_keygen(bits=3072)                        -> (private_key, public_key)
rsa_encap(public_key)                       -> (locked_key, aes_key)
rsa_decap(private_key, locked_key)          -> aes_key
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

**Sending an encrypted message.** RSA is framed as a key encapsulation mechanism so it lines up with ML-KEM. The sender calls `rsa_encap` with the receiver's public key, which generates a fresh 32-byte AES key and encrypts it with RSA-OAEP. The sender then encrypts the message with `aes_encrypt` and sends three things: the locked AES key, the nonce and the ciphertext. The receiver recovers the AES key with `rsa_decap` and decrypts with `aes_decrypt`. The post-quantum version is the same flow with ML-KEM in place of RSA, since ML-KEM's 32-byte shared secret can be used directly as the AES-256 key.

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

# Ground Truth Test Files and Scanner Validation (Laura)

## Purpose
The purpose of the blind test files is to provide an independent measurement of the scanner's accuracy on code it was not developed against. 
While the base ground truth test files' results show that detection gaps were found and fixed, they do not measure how well the scanner performs 
on unfamiliar code. These test files were written without knowledge of the 'rules/python_rules.json' file. Each test has an expected result 
recorded in the ground truth table answer key, and the scanner output is scored against it as a match, miss, mislabel, or false positive.

### Files Added(in `tests/samples/`)
| File | Contents | Status |
|---|---|---|
| `blind_decoys.py` | Text that mentions algorithms but is not real crypto use (comments, strings, names, unused import). Expected: no findings | Completed |
| `blind_structure.py` | Real crypto calls inside `if`, `while`, `try`/`except`, and a function | Completed |
| `blind_algorithms.py` | Algorithms not in the existing tests (HMAC, Diffie-Hellman, DES, RC4, password hashing, AES-ECB) | In Progress |

### Files Added(in `main/`)
| File | Contents | Status |
|---|---|---|
| `Ground-Truth Table Expanded` | Test ID, file, line, expected algorithm, category, status, replacement | Filled out but waiting for scanner results |

## How to run
- Nothing beyond the Python standard library is needed. It was developed and tested on Python 3.13 on Windows.

From the project root:

```
python main.py tests/samples/blind_decoys.py
python main.py tests/samples/blind_structure.py
python main.py tests/samples/blind_algorithms.py
```

## Current status
Works: the written files compile and run; answer-key rows exist for written tests.

Does not work yet: the scanner has not been run on these files, so there are no results; the algorithms file is not started.

Planned: Run the scanner on the new test files and score the output, record the first independent detection rate, then give the misses to the team for updates and re-run.

### Open questions
Whether an unused import should be reported; how HMAC and password hashers should be categorized; whether a printed TLS group string should be reported.

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
