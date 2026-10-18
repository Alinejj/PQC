from scanner.finding import Finding


def scan_file(path, rules):
    findings = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_number, line in enumerate(f, start=1):
            for rule in rules:
                match = rule.regex.search(line)
                if match:
                    findings.append(Finding(
                        file=str(path),
                        line=line_number,
                        matched_text=match.group(0),
                        algorithm=rule.algorithm,
                        category=rule.category,
                        status=rule.status,
                        replacement=rule.replacement,
                    ))
    return findings