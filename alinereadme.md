# PQC-Ready: Source Code Scanner Core

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module is the source-code detection engine of PQC-Ready. It reads Python files, finds cryptography that is either broken by quantum computers or already weak, and reports each finding with a recommended replacement. The report generator, config-file scanner and demo app in the rest of the project are built on top of the output described here.


## Why this exists

A 2026 empirical study of open-source cryptographic discovery tools (Olewinski, Sandler and Ebinger, ARES 2026 Workshops) found that none of the tools tested caught more than 13 of 30 known crypto assets in a controlled test, and that symmetric ciphers, hash functions and key-exchange groups were missed by all of them. This scanner targets those gaps on purpose. The rules cover symmetric ciphers (AES modes, 3DES, Blowfish, RC4, ChaCha20, Fernet), hash functions (MD5, SHA-1, SHA-2, SHA-3, BLAKE2), key-exchange groups including hybrid post-quantum ones like `X25519MLKEM768`, and legacy TLS protocol constants.

## How to run

Nothing beyond the Python standard library is needed. It was developed and tested on Python 3.13 on Windows.

From the project root:

```
python main.py tests/samples/ground_truth_demo.py
python main.py tests/samples
python main.py tests/samples/gap_test.py --json
python main.py --help
```

The first scans one file, the second scans every `.py` file in a folder (skipping `.git`, virtual environments and `__pycache__`), and the third prints the findings as a JSON list instead of text. Text output is one line per finding, followed by a count:

```
tests\samples\ast_demo.py:7  [VULNERABLE] RSA -> ML-KEM (encryption) / ML-DSA (signatures), hybrid with classical during transition
```

The `--rules` flag points to a different rules file. The default path, `rules/python_rules.json`, is relative to where you run the command, so run from the project root. To save JSON output from Windows PowerShell, use `python main.py <target> --json | Out-File -Encoding utf8 findings.json`. Other Python code can skip the command line and call `scan_path(target, rules)` from `scanner/walker.py` directly, which returns the `Finding` objects.

## Project layout

```
main.py                    command-line entry point
scanner/
    finding.py             the Finding dataclass (shared output format)
    rules.py               loads and validates the rules JSON
    scan_python.py         line-by-line regex pass
    scan_ast.py            syntax-tree pass using Python's ast module
    walker.py              merges both passes and walks folders
rules/
    python_rules.json      the detection rules (23 rules)
tests/samples/
    crypto_demo.py         small first test
    ground_truth_demo.py   16 known crypto assets, for measuring detection
    ast_demo.py            cases that regex gets wrong and AST gets right
    gap_test.py            11 assets in forms the first rules did not cover
```

## The Finding format

Every detection is a `Finding` with seven fields: `file`, `line`, `matched_text`, `algorithm`, `category`, `status` and `replacement`. Category is one of asymmetric, symmetric, hash, key_exchange or protocol. Status is one of vulnerable (broken by Shor's algorithm, like RSA, DSA, elliptic curves and Diffie-Hellman), weak (already discouraged or broken classically, like MD5, SHA-1, DES, Blowfish, RC4, ECB mode and legacy TLS), transitional (usable but should be migrated, like AES-CBC and Fernet) or safe (including post-quantum algorithms).

The main entry point for other modules is `scan_path(target, rules)` in `scanner/walker.py`, which returns a list of `Finding` objects. This format is shared with the rest of the team, so any change to it needs to be announced.

One detail that matters for anyone consuming the output: for findings from the AST pass, `matched_text` comes from the normalized, alias-resolved version of the statement, not the raw source. For example, a source line `generate_private_key(...)` imported from `cryptography.hazmat.primitives.asymmetric.rsa` is reported with `matched_text` of `rsa.generate_private_key`, and `hashlib.new("md5")` is reported as `hashlib.new('md5'` because Python normalizes quote style. The `file` and `line` fields always point at the original source.

## Rules are data, not code

Detection rules live in `rules/python_rules.json`. Each rule has an id, a regex pattern, an algorithm name, a category, a status and a replacement. Anyone can add a rule by adding an entry to the JSON; no Python needs to change. `load_rules` checks every rule on load: a missing field, an invalid category or status, or a broken regex stops the program with an error that names the rule. Patterns are compiled once at load time rather than for every line scanned.

The status given to each algorithm is a judgment call based on general public guidance on quantum risk and deprecated algorithms, and these classifications should be checked against a cited source (such as NIST guidance) before the final report.

## How detection works

The scanner runs two passes over each file and merges the results.

The regex pass reads the file line by line and tests every rule against each line. It is simple and fast, and it works even if the file has a syntax error, but it only sees text. It cannot follow an aliased or direct-name import (`from Crypto.PublicKey import RSA as r` followed by `r.generate(2048)`), it cannot see a call that is split across several lines, and it would flag crypto names inside comments. Lines that are entirely a comment are skipped.

The AST pass parses the file into a syntax tree with Python's `ast` module. It first builds a map of import aliases, rewrites short names back to their full names, converts each simple statement back to a single normalized line with `ast.unparse`, and then runs the same rules over that text. Because the tree never contained comments, comments are ignored, and because a statement is flattened to one line, a call spread over four lines is matched as one.

The merge step in `walker.py` runs the AST pass first, then regex, and keeps one finding per file, line and algorithm. If the AST pass cannot parse a file, regex still covers it.

## Results so far

All three test files below were written by the project, not by an outside party, so these numbers show that detection gaps were found and fixed, not how well the scanner generalizes. They are not comparable to the paper's 13 of 30.

On `ground_truth_demo.py`, a file of 16 known crypto assets modeled on the test file in the paper (RSA 2048 and 1024, ECDSA, Ed25519, AES-GCM, AES-CBC, 3DES, MD5, SHA-1, SHA-256, SHA-512 and a TLS group string), the first version of the rules found 10 of 16 and mislabeled 3DES as AES-CBC on one line. After adding rules for AES-GCM, SHA-256, SHA-512, P-256 and the bare `X25519` group, and tightening the CBC rule to require AES, the scanner finds all 16 with no false labels.

On `ast_demo.py`, the regex pass alone reported one finding, and it was a false positive from a comment, while missing all four real ones. The AST pass found the four real ones (RSA, MD5 and SHA-1 through import aliases, and a multi-line AES-CBC call) and ignored the comment.

On `gap_test.py`, a file of 11 assets in forms the rules did not yet cover (DSA, MD5 via `hashlib.new`, SHA-3, BLAKE2, Fernet, ChaCha20, Blowfish with ECB mode, and a legacy TLS constant), the scanner found 2 of 11 before the rules were extended and 11 of 11 after, with no false positives. The two it found at first included an RSA call imported by bare name (`generate_private_key`), which only the AST pass can resolve. 



## Known limitations

The AST pass only looks at simple statements (assignments, expression statements and returns). Crypto calls inside an `if` condition, a `for` header, a `with` line or a decorator are skipped by that pass, and only the regex pass covers them. A statement that spans several lines is reported at the line where it starts, so the same call could in rare cases appear twice with different line numbers. Regex is applied to text, so a trailing comment on a code line (`x = 1  # RSA.generate`) is still seen by the regex pass, though the AST pass ignores it. Detection is by name, so a rule cannot tell the key size, and cannot tell whether a variable holding an algorithm name is actually used. Algorithm names passed in as variables or strings built at runtime are not detected. The scanner only reads Python source; configuration files such as nginx and OpenSSL are handled by a separate module. The default rules path depends on the working directory.

