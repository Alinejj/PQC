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

Two files were written independently by a teammate who had not seen the rules. `blind_structure.py` (7 assets in different code structures) scored 7 of 7. `blind_decoys.py` contains 9 lines that look like crypto but are not (a trailing comment, strings inside `print`, and methods or variables that merely share a name with a crypto function), so the right answer is zero findings. The first scoring run reported 9 false positives on it, because the regex pass could not tell code from text and the AST pass did not skip string messages or locally defined names. The fixes described above bring it to zero. Since those fixes were designed after seeing this result, the decoy score shows the problem was understood and fixed, but it is not a blind measurement. A fresh set of decoys would be needed to know how well the fix generalizes. A second blind file covering a wider set of algorithms has not been scored yet.

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