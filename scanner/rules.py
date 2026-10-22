import json
import re
from dataclasses import dataclass

REQUIRED_FIELDS = ["id", "pattern", "algorithm", "category", "status", "replacement"]
VALID_CATEGORIES = {"asymmetric", "symmetric", "hash", "key_exchange", "protocol"}
VALID_STATUSES = {"vulnerable", "weak", "transitional", "safe"}


@dataclass
class Rule:
    id: str
    regex: re.Pattern
    algorithm: str
    category: str
    status: str
    replacement: str


def load_rules(path):
    with open(path, "r", encoding="utf-8") as f:
        raw_rules = json.load(f)

    rules = []
    for raw in raw_rules:
        rule_id = raw.get("id", "?")

        for field in REQUIRED_FIELDS:
            if field not in raw:
                raise ValueError(f"Rule {rule_id} is missing field '{field}'")

        if raw["category"] not in VALID_CATEGORIES:
            raise ValueError(f"Rule {rule_id} has invalid category '{raw['category']}'")
        if raw["status"] not in VALID_STATUSES:
            raise ValueError(f"Rule {rule_id} has invalid status '{raw['status']}'")

        try:
            regex = re.compile(raw["pattern"])
        except re.error as e:
            raise ValueError(f"Rule {rule_id} has a bad regex: {e}")

        rules.append(Rule(
            id=raw["id"],
            regex=regex,
            algorithm=raw["algorithm"],
            category=raw["category"],
            status=raw["status"],
            replacement=raw["replacement"],
        ))

    return rules