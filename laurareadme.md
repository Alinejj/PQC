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
| `blind_algorithms.py` | Algorithms not in the existing tests (HMAC, Diffie-Hellman, DES, RC4, password hashing, AES-ECB) | Completed |

### Files Added(in `main/`)
| File | Contents | Status |
|---|---|---|
| `Ground-Truth Table Expanded` | Test ID, file, line, expected algorithm, category, status, replacement | Completed |

## How to run
- Nothing beyond the Python standard library is needed. It was developed and tested on Python 3.13 on Windows.

From the project root:

```
python main.py tests/samples/blind_decoys.py
python main.py tests/samples/blind_structure.py
python main.py tests/samples/blind_algorithms.py
```

### Open questions
Whether an unused import should be reported; whether a printed TLS group string should be reported.
