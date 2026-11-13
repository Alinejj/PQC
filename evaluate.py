import json
from collections import Counter

from scanner.rules import load_rules
from scanner.walker import scan_path


def count_by_line(items):
    by_line = {}
    for line, algorithm in items:
        by_line.setdefault(line, Counter())[algorithm] += 1
    return by_line


def score_file(path, expected, rules):
    found = scan_path(path, rules)
    exp_by_line = count_by_line((e["line"], e["algorithm"]) for e in expected)
    got_by_line = count_by_line((f.line, f.algorithm) for f in found)

    result = {"match": 0, "miss": [], "mislabel": [], "false_positive": []}
    for line in sorted(set(exp_by_line) | set(got_by_line)):
        exp = exp_by_line.get(line, Counter())
        got = got_by_line.get(line, Counter())

        matched = exp & got
        result["match"] += sum(matched.values())

        left_exp = list((exp - matched).elements())
        left_got = list((got - matched).elements())

        while left_exp and left_got:
            result["mislabel"].append((line, left_exp.pop(), left_got.pop()))
        for algorithm in left_exp:
            result["miss"].append((line, algorithm))
        for algorithm in left_got:
            result["false_positive"].append((line, algorithm))

    return len(expected), result


def main():
    rules = load_rules("rules/python_rules.json")
    with open("tests/expected.json", "r", encoding="utf-8") as f:
        answer_key = json.load(f)

    totals = {"expected": 0, "match": 0, "miss": 0, "mislabel": 0, "false_positive": 0}

    for path, expected in answer_key.items():
        total, r = score_file(path, expected, rules)
        print(f"\n{path}")
        print(f"  expected {total}: match {r['match']}, miss {len(r['miss'])}, "
              f"mislabel {len(r['mislabel'])}, false positive {len(r['false_positive'])}")
        for line, algorithm in r["miss"]:
            print(f"    MISS line {line}: {algorithm}")
        for line, wanted, got in r["mislabel"]:
            print(f"    MISLABEL line {line}: wanted {wanted}, got {got}")
        for line, algorithm in r["false_positive"]:
            print(f"    FALSE POSITIVE line {line}: {algorithm}")

        totals["expected"] += total
        totals["match"] += r["match"]
        totals["miss"] += len(r["miss"])
        totals["mislabel"] += len(r["mislabel"])
        totals["false_positive"] += len(r["false_positive"])

    print("\nTOTAL")
    print(f"  expected {totals['expected']}: match {totals['match']}, miss {totals['miss']}, "
          f"mislabel {totals['mislabel']}, false positive {totals['false_positive']}")


if __name__ == "__main__":
    main()