# Blind Test Files and Scanner Validation (Laura Shupe)

## Purpose
The purpose of the blind test files is to provide an independent measurement of the scanner's accuracy on code it was not developed against. 
While the base ground truth test files' results show that detection gaps were found and fixed, they do not measure how well the scanner performs 
on unfamiliar code. These test files were written without reference of the 'rules/python_rules.json' file. Each test has an expected result 
recorded in the ground truth table answer key, and the scanner output is scored against it as a match, miss, mislabel, or false positive.

## Files Added(in `tests/samples/`)
| File | Contents | Status |
|---|---|---|
| `blind_decoys.py` | Text that mentions algorithms but is not real crypto use (comments, strings, names, unused import). Expected: no findings | Completed |
| `blind_structure.py` | Real crypto calls inside `if`, `while`, `try`/`except`, and a function | Completed |
| `blind_algorithms.py` | Algorithms not in the existing tests (HMAC, Diffie-Hellman, DES, RC4, password hashing, AES-ECB) | Completed |

Answer key: `Ground-Truth Table Expanded` (test ID, file, line, expected algorithm, category, status, replacement). The expected findings are also scored through `tests/expected.json`. Link here: [Ground-Truth-Table(PDF).pdf]

## Requirements
- OS and language: developed and tested on Windows 11 with Python 3.13 and 3.14, and also run on Linux.
- Dependencies: the Python standard library only. The blind files are scanned, not executed, so their imports do not need to be installed.
- Installation: clone the repository. No other setup is required.
- Login credentials: not applicable.

## How to run
From the project root:

```
python main.py tests/samples/blind_decoys.py
python main.py tests/samples/blind_structure.py
python main.py tests/samples/blind_algorithms.py
python evaluate.py
```

`evaluate.py` compares the scanner's findings with `tests/expected.json` and prints matches, misses, mislabels, and false positives for each file, including the three blind files. `python main.py tests/samples` scans these files together with the original samples.

## Results
| File | Expected | First run | After rule and scanner changes |
|---|---|---|---|
| blind_decoys.py | 0 findings | 9 false positives | 0 false positives |
| blind_structure.py | 7 | 7 matched, 0 false positives | 7 matched, 0 false positives |
| blind_algorithms.py | 9 | 5 matched, 4 missed (HMAC, bcrypt, Argon2, scrypt), 1 false positive (RC4 reported on an import line) | 9 matched, 0 false positives |

The first run on the decoy file exposed false positives from trailing comments, strings inside `print` calls, and methods or variables named after algorithms. The first run on `blind_algorithms.py` exposed missing rules for HMAC and the three password hashers, and a case where the Argon2 call names the algorithm only where the hasher object is created. The fixes were new rules, an AST pass that tracks variables created from imported classes, ignoring strings in `print` and logging calls, and no longer matching import statements.

## Decisions made
- Import statements are not reported as findings.
- Strings inside `print` and logging calls are ignored, including a printed TLS group string.
- HMAC, bcrypt, Argon2, and scrypt are categorized as `hash` and labeled `safe`, which is how the rules currently classify them.
