# PQC-Ready: Source Code Scanner Core

CS4389 Data and Application Security, final project (Category 13, Post-Quantum Cryptography).

This module is the source-code detection engine of PQC-Ready. It reads Python files, finds cryptography that is either broken by quantum computers or already weak, and reports each finding with a recommended replacement. The report generator, config-file scanner and demo app in the rest of the project are built on top of the output described here.

Owner: Aline (scanner architecture and source-code detection)

## Why this exists

A 2026 empirical study of open-source cryptographic discovery tools (Olewinski, Sandler and Ebinger, ARES 2026 Workshops) found that none of the tools tested caught more than 13 of 30 known crypto assets in a controlled test, and that symmetric ciphers, hash functions and key-exchange groups were missed by all of them. This scanner targets those gaps on purpose. The rules cover symmetric ciphers (AES modes, 3DES, RC4), hash functions (MD5, SHA-1, SHA-2) and key-exchange groups, including hybrid post-quantum ones like `X25519MLKEM768`.

## How to run

Nothing beyond the Python standard library is needed. It was developed and tested on Python 3.13 on Windows.

From the project root:

```
python main.py tests/samples/ground_truth_demo.py
python main.py tests/samples
python main.py --help
```

The first scans one file, the second scans every `.py` file in a folder (skipping `.git`, virtual environments and `__pycache__`). Output is one line per finding, followed by a count:

```
tests\samples\ast_demo.py:7  [VULNERABLE] RSA -> ML-KEM (encryption) / ML-DSA (signatures), hybrid with classical during transition
```

The `--rules` flag points to a different rules file. The default path, `rules/python_rules.json`, is relative to where you run the command, so run from the project root.

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
    python_rules.json      the detection rules (16 rules)
tests/samples/
    crypto_demo.py         small first test
    ground_truth_demo.py   16 known crypto assets, for measuring detection
    ast_demo.py            cases that regex gets wrong and AST gets right
```

## The Finding format

Every detection is a `Finding` with seven fields: `file`, `line`, `matched_text`, `algorithm`, `category`, `status` and `replacement`. Category is one of asymmetric, symmetric, hash, key_exchange or protocol. Status is one of vulnerable (broken by Shor's algorithm, like RSA, elliptic curves and Diffie-Hellman), weak (already discouraged or broken classically, like MD5, SHA-1, DES, RC4 and ECB mode), transitional (usable but should be migrated, like AES-CBC) or safe (including post-quantum algorithms).

The main entry point for other modules is `scan_path(target, rules)` in `scanner/walker.py`, which returns a list of `Finding` objects. This format is shared with the rest of the team, so any change to it needs to be announced.

## Rules are data, not code

Detection rules live in `rules/python_rules.json`. Each rule has an id, a regex pattern, an algorithm name, a category, a status and a replacement. Anyone can add a rule by adding an entry to the JSON; no Python needs to change. `load_rules` checks every rule on load: a missing field, an invalid category or status, or a broken regex stops the program with an error that names the rule. Patterns are compiled once at load time rather than for every line scanned.

## How detection works

The scanner runs two passes over each file and merges the results.

The regex pass reads the file line by line and tests every rule against each line. It is simple and fast, and it works even if the file has a syntax error, but it only sees text. It cannot follow an aliased import (`from Crypto.PublicKey import RSA as r` followed by `r.generate(2048)`), it cannot see a call that is split across several lines, and it would flag crypto names inside comments. Lines that are entirely a comment are skipped.

The AST pass parses the file into a syntax tree with Python's `ast` module. It first builds a map of import aliases, rewrites short names back to their full names, converts each simple statement back to a single normalized line with `ast.unparse`, and then runs the same rules over that text. Because the tree never contained comments, comments are ignored, and because a statement is flattened to one line, a call spread over four lines is matched as one.

The merge step in `walker.py` runs the AST pass first, then regex, and keeps one finding per file, line and algorithm. If the AST pass cannot parse a file, regex still covers it.

## Results so far

On `ground_truth_demo.py`, a file of 16 known crypto assets modeled on the test file in the paper (RSA 2048 and 1024, ECDSA, Ed25519, AES-GCM, AES-CBC, 3DES, MD5, SHA-1, SHA-256, SHA-512 and a TLS group string), the first version of the rules found 10 of 16 and mislabeled 3DES as AES-CBC on one line. After adding rules for AES-GCM, SHA-256, SHA-512, P-256 and the bare `X25519` group, and tightening the CBC rule to require AES, the scanner finds all 16 with no false labels.

On `ast_demo.py`, the regex pass alone reported one finding, and it was a false positive from a comment, while missing all four real ones. The AST pass found the four real ones (RSA through an alias, MD5 and SHA-1 through aliases, and a multi-line AES-CBC call) and ignored the comment.

An important caveat: the 16 of 16 result was measured on a test file written together with the rules, so it shows the rules were fixed correctly, not how well the scanner generalizes. It is not comparable to the paper's 13 of 30. A blind test, where a teammate writes a new test file without looking at the rules, is still to be done.

Blind test results: [to be filled in]

## Known limitations

The AST pass only looks at simple statements (assignments, expression statements and returns). Crypto calls inside an `if` condition, a `for` header, a `with` line or a decorator are skipped by that pass, and only the regex pass covers them. A statement that spans several lines is reported at the line where it starts, so the same call could in rare cases appear twice with different line numbers. Regex is applied to text, so a trailing comment on a code line (`x = 1  # RSA.generate`) is still seen by the regex pass, though the AST pass ignores it. Detection is by name, so a rule cannot tell the key size or whether a variable holding an algorithm name is actually used. The scanner only reads Python source; configuration files such as nginx and OpenSSL are handled by a separate module. The default rules path depends on the working directory.
