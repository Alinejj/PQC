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

The post-quantum demonstrations use the algorithm interfaces available in `benchmarks/algorithms.py`, backed by the Python `cryptography` library.

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